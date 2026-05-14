import uvicorn

from api.main import create_app
from backend.runtime import get_container


app = create_app()


@app.on_event("startup")
async def startup() -> None:
    await get_container().database.create_schema()


if __name__ == "__main__":
    container = get_container()
    uvicorn.run(
        "run_api:app",
        host=container.settings.api_host,
        port=container.settings.api_port,
        reload=False,
    )
