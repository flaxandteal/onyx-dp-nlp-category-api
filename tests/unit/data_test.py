from pathlib import Path
from category_api import data
from unittest.mock import patch, MagicMock

class BotoMock:
    data_root = Path(__file__).parent.parent.parent / "test_data"
    expected_from = []

    def download_fileobj(self, fm_b, fm_k, to):
        assert (fm_b, fm_k) in self.expected_from
        with (self.data_root / fm_k).open("rb") as f:
            to.write(f.read())

    def client(self, arg):
        assert arg == "s3"
        mock = MagicMock()
        mock.download_fileobj.side_effect = self.download_fileobj
        return mock

def test_retrieve_dummy(settings, settings_bonn):
    settings.FIFU_FILE = "test.fifu"
    settings_bonn.TAXONOMY_LOCATION = "taxonomy.json"
    settings_bonn.CACHE_TARGET = "cache.json"
    settings.CACHE_S3_BUCKET = ""
    with data.retrieve(settings, settings_bonn) as settings_pair:
        settings, settings_bonn = settings_pair
    assert settings.FIFU_FILE == "test.fifu"
    assert settings_bonn.CACHE_TARGET == "cache.json"
    assert settings.CACHE_S3_BUCKET == ""

def test_retrieve_from_s3(settings, settings_bonn):
    settings.FIFU_FILE = "foo-wiki.en.fifu"
    settings_bonn.TAXONOMY_LOCATION = "foo-taxonomy.json"
    settings_bonn.CACHE_TARGET = "foo-cache.json"
    settings.CACHE_S3_BUCKET = "s3://category-api-cache"
    with patch('category_api.data.boto3', new_callable=BotoMock) as s3client:
        s3client.expected_from = [
            ("category-api-cache", "foo-cache.json"),
            ("category-api-cache", "foo-taxonomy.json"),
            ("category-api-cache", "foo-wiki.en.fifu")
        ]
        with data.retrieve(settings, settings_bonn) as settings_pair:
            settings, settings_bonn = settings_pair
    assert settings.FIFU_FILE.startswith("/tmp")
    assert settings_bonn.TAXONOMY_LOCATION.startswith("/tmp")
    assert settings_bonn.CACHE_TARGET.startswith("/tmp")

def test_retrieve_some_from_s3(settings, settings_bonn):
    settings.FIFU_FILE = "test_data/foo-wiki.en.fifu"
    settings_bonn.TAXONOMY_LOCATION = "foo-taxonomy.json"
    settings_bonn.CACHE_TARGET = "foo-cache.json"
    settings.CACHE_S3_BUCKET = "s3://category-api-cache"
    with patch('category_api.data.boto3', new_callable=BotoMock) as s3client:
        s3client.expected_from = [
            ("category-api-cache", "foo-cache.json"),
            ("category-api-cache", "foo-taxonomy.json"),
        ]
        with data.retrieve(settings, settings_bonn) as settings_pair:
            settings, settings_bonn = settings_pair
    assert settings.FIFU_FILE == "test_data/foo-wiki.en.fifu"
    assert settings_bonn.TAXONOMY_LOCATION.startswith("/tmp")
    assert settings_bonn.CACHE_TARGET.startswith("/tmp")
