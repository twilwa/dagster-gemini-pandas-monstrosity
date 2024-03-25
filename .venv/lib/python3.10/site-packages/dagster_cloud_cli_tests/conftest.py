import pytest


@pytest.fixture
def empty_config(monkeypatch):
    # ensure no defaults are read from the local config
    monkeypatch.setenv("DAGSTER_CLOUD_CLI_CONFIG", "/tmp/nosuchpath")
