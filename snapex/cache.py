import time
from typing import Dict, Optional
from threading import Lock
from .models import Request, Response
from .utils import generate_cache_key

class CacheBackend:
    """In-memory cache backend with TTL support"""
    
    def __init__(self, ttl: int = 300, max_size: int = 1000):
        self.ttl = ttl
        self.max_size = max_size
        self._cache: Dict[str, tuple[float, Response]] = {}
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def get(self, request: Request) -> Optional[Response]:
        """Get cached response for request"""
        key = generate_cache_key(request)
        
        with self._lock:
            if key in self._cache:
                timestamp, response = self._cache[key]
                if time.time() - timestamp < self.ttl:
                    self._hits += 1
                    return response
                del self._cache[key]
            
            self._misses += 1
            return None

    def set(self, request: Request, response: Response) -> None:
        """Cache response for request"""
        if len(self._cache) >= self.max_size:
            self._evict()
            
        key = generate_cache_key(request)
        with self._lock:
            self._cache[key] = (time.time(), response)

    def _evict(self) -> None:
        """Evict expired or least recently used items"""
        now = time.time()
        expired = [k for k, (t, _) in self._cache.items() if now - t > self.ttl]
        
        for key in expired:
            del self._cache[key]
            
        if len(self._cache) >= self.max_size:
            oldest = sorted(self._cache.items(), key=lambda x: x[1][0])[0][0]
            del self._cache[oldest]

    def clear(self) -> None:
        """Clear the cache"""
        with self._lock:
            self._cache.clear()

    @property
    def stats(self) -> dict:
        """Get cache statistics"""
        with self._lock:
            return {
                'size': len(self._cache),
                'hits': self._hits,
                'misses': self._misses,
                'hit_ratio': self._hits / (self._hits + self._misses) if (self._hits + self._misses) > 0 else 0
            }