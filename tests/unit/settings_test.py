from category_api.settings import settings

def test_load_settings():
    assert settings.load_dotenv is True
    assert settings.ENVVAR_PREFIX_FOR_DYNACONF == "CATEGORY_API"
