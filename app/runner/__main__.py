import uvicorn

from app.runner.setup import setup

app = setup()
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)