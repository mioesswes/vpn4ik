from fastapi import APIRouter

from backend.runtime import get_container

router = APIRouter(tags=["health"])


@router.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/nodes")
async def nodes_summary() -> dict[str, list[str]]:
    summaries = await get_container().monitoring.node_summary()
    return {"nodes": summaries}
