from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root() -> dict[str, str]:
    """Root endpoint returning a hello world message."""
    return {"message": "Hello World"}
