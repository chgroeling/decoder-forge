import pytest

from decoder_forge.decoder_cache import CACHE_DIR_ENV


@pytest.fixture(autouse=True)
def isolated_decoder_cache(tmp_path, monkeypatch):
    """Keep the decoder cache out of the developer's real cache directory.

    Generated decoders are cached under ``~/.cache`` by default. A test run must
    neither be served an entry written by an earlier one nor evict the entries a
    developer is actually using, so every test gets a cache of its own.
    """

    monkeypatch.setenv(CACHE_DIR_ENV, str(tmp_path / "decoder-cache"))
