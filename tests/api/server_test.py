import pytest
from fastapi.testclient import TestClient
from category_api.server import make_app, Controllers
from unittest.mock import MagicMock
from bonn.extract import CategoryManager
from category_api.healthcheck import Healthcheck
from collections.abc import AsyncGenerator
import pytest_asyncio

@pytest_asyncio.fixture()
async def test_client(settings, settings_bonn) -> AsyncGenerator[TestClient, None]:
    # Create a mock CategoryManager object to simulate the FastText model
    category_manager = MagicMock(spec=CategoryManager)
    category_manager.test.return_value = [
        (0.9, ['cat1', 'cat2']),
        (0.8, ['cat3']),
    ]

    controllers = Controllers()
    app = make_app(controllers, settings, settings_bonn)
    app.controllers = controllers
    app.controllers.healthcheck = Healthcheck(status="OK", checks=[])
    app.controllers.category_manager = category_manager
    client = TestClient(app)
    yield client


@pytest.mark.asyncio
async def test_health_check(test_client):
    response = test_client.get('/health')
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_categories(test_client):
    response = test_client.get('/categories?query=test')
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_category(test_client):
    response = test_client.get('/categories/healthandsocialcare?query=dentist')
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
