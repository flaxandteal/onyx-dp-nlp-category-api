from fastapi import FastAPI
from category_api.settings import settings, get_bonn_settings
from contextlib import asynccontextmanager
from category_api.healthcheck import Healthcheck
import bonn
from bonn.extract import CategoryManager
import importlib.util
from .logger import logger
from .data import retrieve

class Controllers:
    category_manager: CategoryManager
    healthcheck: Healthcheck

def make_app(controllers, settings, settings_bonn):
    app = FastAPI(lifespan=lifespan)
    app.controllers = controllers
    app.settings = settings
    app.settings_bonn = settings_bonn

    routes_spec = importlib.util.find_spec("category_api.routes")
    routes = importlib.util.module_from_spec(routes_spec)
    routes.app = app
    routes_spec.loader.exec_module(routes)

    return app

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.controllers.healthcheck = Healthcheck(status="OK", checks=[])
    with retrieve(app.settings, app.settings_bonn) as (settings, settings_bonn):
        app.settings = settings
        app.settings_bonn = settings_bonn
        app.controllers.category_manager = bonn.extract.load(app.settings.FIFU_FILE, app.settings_bonn)
        yield

def create_app():
    logger.info(event="successfully loaded category manager")

    controllers = Controllers()
    settings_bonn = get_bonn_settings()
    app = make_app(controllers, settings, settings_bonn)

    return app
