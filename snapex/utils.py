import hashlib
import json
import time
from typing import Any, Dict, Optional, Union
from urllib.parse import urlencode, urlparse
from .models import Request

def generate_cache_key(request: Request) -> str:
    """Generate a unique cache key for the request"""
    key_parts = [
        request.method.value,
        request.url,
        urlencode(sorted(request.params.items()) if request.params else '',
        json.dumps(request.headers, sort_keys=True) if request.headers else '',
        json.dumps(request.cookies, sort_keys=True) if request.cookies else ''
    ]
    
    if request.body:
        if isinstance(request.body, (bytes, str)):
            body = request.body if isinstance(request.body, bytes) else request.body.encode()
        else:
            body = json.dumps(request.body).encode()
        key_parts.append(hashlib.sha256(body).hexdigest())
    
    return hashlib.sha256('|'.join(key_parts).encode()).hexdigest()

def normalize_url(url: str) -> str:
    """Normalize URL by removing fragments and sorting query params"""
    parsed = urlparse(url)
    query = urlencode(sorted(parse_qs(parsed.query).items()))
    return parsed._replace(query=query, fragment='').geturl()

def merge_headers(
    base: Optional[Dict[str, str]],
    update: Optional[Dict[str, str]]
) -> Dict[str, str]:
    """Merge two headers dictionaries"""
    result = {}
    if base:
        result.update(base)
    if update:
        result.update(update)
    return result

def elapsed_time(start: float) -> float:
    """Calculate elapsed time in milliseconds"""
    return (time.time() - start) * 1000

def is_redirect(status_code: int) -> bool:
    """Check if status code is a redirect"""
    return status_code in (301, 302, 303, 307, 308)