import pytest
from dynaconf import Dynaconf

@pytest.fixture
def settings():
    return Dynaconf(
        settings_files=["tests/settings.yaml"],
        environments=False,
    )

@pytest.fixture
def settings_bonn():
    return Dynaconf(
        settings_files=["tests/settings_bonn.yaml"],
        environments=False,
    )
