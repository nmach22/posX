from fastapi import FastAPI


def setup() -> FastAPI:
    app = FastAPI()
    return app
