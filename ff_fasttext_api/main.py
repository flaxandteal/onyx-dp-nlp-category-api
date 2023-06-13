from ff_fasttext_api.settings import settings
from ff_fasttext_api.server import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.HOST, port=settings.PORT)