from fastapi import FastAPI

app = FastAPI(title="RG Knowledge OS API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "database": "neon"}


def run() -> None:
    import uvicorn

    uvicorn.run("rg_api.main:app", host="0.0.0.0", port=8000, reload=True)
