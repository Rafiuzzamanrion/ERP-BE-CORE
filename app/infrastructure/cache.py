import asyncio
import time


class TTLCache:
    def __init__(self, ttl_seconds: int = 60):
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[float, any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> tuple[bool, any]:
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return False, None
            timestamp, value = entry
            if time.monotonic() - timestamp > self._ttl:
                del self._store[key]
                return False, None
            return True, value

    async def set(self, key: str, value):
        async with self._lock:
            self._store[key] = (time.monotonic(), value)

    async def invalidate(self, key: str):
        async with self._lock:
            self._store.pop(key, None)

    async def clear(self):
        async with self._lock:
            self._store.clear()


dashboard_cache = TTLCache(ttl_seconds=30)
permission_cache = TTLCache(ttl_seconds=60)
