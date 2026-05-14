from functools import lru_cache

from backend.container import ServiceContainer
from backend.main import build_container


@lru_cache
def get_container() -> ServiceContainer:
    return build_container()
