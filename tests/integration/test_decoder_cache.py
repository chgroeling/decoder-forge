import pytest

from decoder_forge import decoder_cache
from decoder_forge.decoder_cache import (
    CACHE_DIR_ENV,
    cache_dir,
    cache_key,
    load_decoder_source,
)
from decoder_forge.template_engine import TemplateEngine


TEST_FORMAT = """
instructions:
- id: FOO
  mnemonic: FOO
  encodings:
  - name: T1
    length_bits: 8
    pattern: 0000xxxx
    bit_fields:
    - skip: 4
    - field: a
      width: 4
    decode: |
      d = UInt(a);
"""

OTHER_FORMAT = TEST_FORMAT.replace("pattern: 0000xxxx", "pattern: 0001xxxx")


@pytest.fixture
def cache_path(tmp_path, monkeypatch):
    """Point the cache at a directory of this test's own."""
    monkeypatch.setenv(CACHE_DIR_ENV, str(tmp_path / "cache"))
    return tmp_path / "cache"


@pytest.fixture
def generations(monkeypatch):
    """Count how often a decoder is actually generated."""
    calls = []
    real = decoder_cache.generate_code

    def counting(*args, **kwargs):
        calls.append(args[0])
        return real(*args, **kwargs)

    monkeypatch.setattr(decoder_cache, "generate_code", counting)
    return calls


def _load(yaml_buf: str = TEST_FORMAT, **kwargs) -> str:
    return load_decoder_source(yaml_buf, TemplateEngine(), **kwargs)


def test_cache_dir_prefers_the_environment_override(tmp_path, monkeypatch):
    monkeypatch.setenv(CACHE_DIR_ENV, str(tmp_path))
    assert cache_dir() == tmp_path


def test_cache_dir_falls_back_to_xdg_cache_home(tmp_path, monkeypatch):
    monkeypatch.delenv(CACHE_DIR_ENV, raising=False)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    assert cache_dir() == tmp_path / "decoder-forge"


def test_a_second_load_is_served_from_the_cache(cache_path, generations):
    first = _load()
    second = _load()

    assert second == first
    # the decoder was built once and reused, which is the whole point
    assert len(generations) == 1
    assert (cache_path / f"{cache_key(TEST_FORMAT, True)}.py").exists()


def test_a_different_format_gets_its_own_entry(cache_path, generations):
    first = _load(TEST_FORMAT)
    second = _load(OTHER_FORMAT)

    assert first != second
    assert len(generations) == 2
    assert len(list(cache_path.glob("*.py"))) == 2


def test_the_formatting_flag_is_part_of_the_key(cache_path, generations):
    _load(auto_format=True)
    _load(auto_format=False)

    assert len(generations) == 2


def test_a_changed_generator_invalidates_the_cache(
    cache_path, generations, monkeypatch
):
    """The generator's own sources are part of the key, so editing it is not stale."""
    _load()

    monkeypatch.setattr(decoder_cache, "_generator_fingerprint", lambda: "other")
    _load()

    assert len(generations) == 2


def test_use_cache_false_always_regenerates(cache_path, generations):
    _load(use_cache=False)
    _load(use_cache=False)

    assert len(generations) == 2
    assert not cache_path.exists()


def test_an_unusable_cache_still_decodes(cache_path, generations, monkeypatch):
    """The cache is an optimisation; losing it must not lose the decoder."""

    def unwritable(*args, **kwargs):
        raise OSError("read-only file system")

    monkeypatch.setattr(decoder_cache, "_write_entry", unwritable)

    assert _load().startswith("# Auto-generated")
    assert _load().startswith("# Auto-generated")
    assert len(generations) == 2


def test_the_cache_keeps_only_the_most_recent_entries(cache_path, monkeypatch):
    monkeypatch.setattr(decoder_cache, "_MAX_ENTRIES", 2)

    for i in range(4):
        _load(TEST_FORMAT.replace("width: 4", f"width: 4  # {i}"))

    assert len(list(cache_path.glob("*.py"))) == 2


def test_no_temporary_files_are_left_behind(cache_path, generations):
    _load()

    assert [p.name for p in cache_path.iterdir()] == [
        f"{cache_key(TEST_FORMAT, True)}.py"
    ]
