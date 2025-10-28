from fastapi import FastAPI, Request

import importlib.metadata

__version__ = importlib.metadata.version("hermesbaby.hermes")
app = FastAPI(title="Hermes API", version=__version__)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "hermes", "version": __version__}


@app.put("/{path:path}")
async def put_echo(path: str, request: Request):
    """Accept PUT requests to any endpoint and echo back the endpoint path"""
    return {"endpoint": f"/{path}", "method": "PUT"}
