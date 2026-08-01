"""On-disk cache for generated decoder sources.

Generating the ARMv7-M decoder takes some 17 seconds, nearly all of it transpiling the
369 pseudocode ``decode`` blocks; compiling the finished source takes a fifth of a
second. Decoding a single instruction word therefore spent almost all of its time
rebuilding a decoder identical to the one the previous call built.

A cache entry is keyed by everything the generated source is a function of: the
instruction-set YAML, the formatting flag, and the generator itself -- the sources of
``decoder_forge`` and of ``arm-transpiller``, which is what transpiles the decode
blocks. Hashing both package trees costs a few milliseconds and means an edit to either
one invalidates the cache, including an ``arm-transpiller`` git pin whose version string
did not change. A stale decoder is never served.
"""

import hashlib
import importlib.util
import io
import logging
import os
import tempfile

from functools import cache
from pathlib import Path

from decoder_forge.generate_code import generate_code
from decoder_forge.template_engine import ITemplateEngine

logger = logging.getLogger(__name__)

#: Environment variable overriding where cache entries are stored.
CACHE_DIR_ENV = "DECODER_FORGE_CACHE_DIR"

#: Packages whose source decides what the generated decoder looks like.
_GENERATOR_PACKAGES = ("decoder_forge", "arm_transpiller")

#: Source file kinds contributing to the generator fingerprint: code, the Jinja
#: templates, and the runtime template ``arm-transpiller`` hands out to be embedded.
_SOURCE_SUFFIXES = (".py", ".jinja", ".template", ".lark")

#: How many generated decoders to keep. Each is a few hundred kilobytes, and editing a
#: format leaves the entry for every intermediate version behind.
_MAX_ENTRIES = 8


def cache_dir() -> Path:
    """The directory cache entries are stored in.

    Honours :data:`CACHE_DIR_ENV`, then ``XDG_CACHE_HOME``, then ``~/.cache``.

    Returns:
        Path: The cache directory. It is not created.
    """

    override = os.environ.get(CACHE_DIR_ENV)
    if override:
        return Path(override)

    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg) if xdg else Path.home() / ".cache"
    return base / "decoder-forge"


@cache
def _generator_fingerprint() -> str:
    """Hash the sources that decide what a generated decoder looks like.

    Covers ``decoder_forge`` (the pipeline and its templates) and ``arm_transpiller``
    (the transpiler and the runtime embedded in the output), so any change to either
    yields different cache keys. The result is memoised: the generator cannot change
    while the process runs.

    Returns:
        str: A hex digest over every source file of both packages.
    """

    digest = hashlib.sha256()
    for package in _GENERATOR_PACKAGES:
        spec = importlib.util.find_spec(package)
        if spec is None or not spec.submodule_search_locations:
            # A package we cannot locate cannot be fingerprinted, so nothing may be
            # cached against it.
            raise LookupError(f"cannot locate the {package!r} package")

        root = Path(next(iter(spec.submodule_search_locations)))
        sources = sorted(
            path
            for path in root.rglob("*")
            if path.is_file() and path.suffix in _SOURCE_SUFFIXES
        )
        for path in sources:
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def cache_key(input_yaml: str, auto_format: bool) -> str:
    """Compute the cache key of a decoder.

    Args:
        input_yaml (str): The instruction-set YAML the decoder is generated from.
        auto_format (bool): Whether the generated source is formatted with ruff.

    Returns:
        str: A hex digest identifying this decoder.
    """

    digest = hashlib.sha256()
    digest.update(_generator_fingerprint().encode())
    digest.update(b"\x00format" if auto_format else b"\x00raw")
    digest.update(input_yaml.encode())
    return digest.hexdigest()


def _prune(directory: Path) -> None:
    """Drop the least recently used entries beyond :data:`_MAX_ENTRIES`."""

    entries = sorted(
        directory.glob("*.py"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    for stale in entries[_MAX_ENTRIES:]:
        stale.unlink(missing_ok=True)


def _write_entry(path: Path, code: str) -> None:
    """Store a generated decoder, atomically.

    The entry is written to a temporary file in the cache directory and moved into
    place, so an interrupted or concurrent run cannot leave a half-written decoder for
    the next call to compile.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fp:
            fp.write(code)
        tmp.replace(path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    _prune(path.parent)


def load_decoder_source(
    input_yaml: str,
    tengine: ITemplateEngine,
    auto_format: bool = True,
    use_cache: bool = True,
) -> str:
    """Return the decoder source for ``input_yaml``, generating it only if needed.

    A cached entry is used whenever the YAML and the generator are unchanged since it
    was written. The cache is an optimisation and never a failure mode: if it cannot be
    read or written, the decoder is generated as usual and the reason is logged.

    Args:
        input_yaml (str): A YAML string with an ``instructions`` list.
        tengine (ITemplateEngine): Template engine used to generate the decoder.
        auto_format (bool): Whether to run ``ruff format`` on the generated code
            (default ``True``).
        use_cache (bool): Whether to consult and populate the cache (default ``True``).

    Returns:
        str: The generated decoder source.

    Raises:
        yaml.YAMLError: If the input YAML cannot be parsed.
        ValueError: If an encoding's length is not a supported instruction size.
    """

    entry = None
    if use_cache:
        try:
            entry = cache_dir() / f"{cache_key(input_yaml, auto_format)}.py"
            code = entry.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.info("decoder cache miss: %s", entry)
        except (OSError, LookupError) as e:
            logger.warning("decoder cache unavailable (%s); generating", e)
            entry = None
        else:
            logger.info("decoder cache hit: %s", entry)
            # Keep the entry looking recently used, so pruning drops the decoders that
            # are actually going unused rather than the one in daily service.
            try:
                entry.touch()
            except OSError:
                pass
            return code

    printer = io.StringIO()
    generate_code(input_yaml, tengine, printer, auto_format=auto_format)
    code = printer.getvalue()

    if entry is not None:
        try:
            _write_entry(entry, code)
        except OSError as e:
            logger.warning("could not cache the decoder (%s)", e)

    return code
