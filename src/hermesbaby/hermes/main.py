from fastapi import FastAPI

app = FastAPI(title="Hermes API", version="0.1.0")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "hermes", "version": "0.1.0"}
