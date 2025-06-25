from typing import Any, Optional, Dict, Union, Callable, Iterator
from .http import HTTPClient
from .models import Request, Response, RequestMethod, HTTPVersion
from .exceptions import SnapexError
from .ws import WebSocket

class Client:
    """Main Snapex client interface"""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        pool_size: int = 100,
        verify: bool = True,
        http_version: HTTPVersion = HTTPVersion.HTTP_1_1,
        default_headers: Optional[Dict[str, str]] = None,
        cache_ttl: int = 300
    ):
        self.base_url = base_url.rstrip('/') if base_url else None
        self.http = HTTPClient(
            pool_size=pool_size,
            timeout=TimeoutConfig(total=timeout) if timeout else None,
            verify=verify,
            cache_ttl=cache_ttl
        )
        self.default_headers = default_headers or {}
        self.default_http_version = http_version
        self.cookies: Dict[str, str] = {}
        
    def request(
        self,
        method: Union[str, RequestMethod],
        url: str,
        **kwargs: Any
    ) -> Response:
        """Send HTTP request"""
        if isinstance(method, str):
            method = RequestMethod[method.upper()]
            
        if self.base_url and not url.startswith(('http://', 'https://')):
            url = f"{self.base_url}/{url.lstrip('/')}"
            
        request = Request(
            method=method,
            url=url,
            headers=merge_headers(self.default_headers, kwargs.pop('headers', None)),
            cookies=merge_headers(self.cookies, kwargs.pop('cookies', None)),
            http_version=kwargs.pop('http_version', self.default_http_version),
            **kwargs
        )
        
        return self.http.request(request)
    
    def get(self, url: str, **kwargs: Any) -> Response:
        """Send GET request"""
        return self.request(RequestMethod.GET, url, **kwargs)
        
    def post(self, url: str, data: Optional[Any] = None, **kwargs: Any) -> Response:
        """Send POST request"""
        return self.request(RequestMethod.POST, url, body=data, **kwargs)
        
    def put(self, url: str, data: Optional[Any] = None, **kwargs: Any) -> Response:
        """Send PUT request"""
        return self.request(RequestMethod.PUT, url, body=data, **kwargs)
        
    def delete(self, url: str, **kwargs: Any) -> Response:
        """Send DELETE request"""
        return self.request(RequestMethod.DELETE, url, **kwargs)
        
    def head(self, url: str, **kwargs: Any) -> Response:
        """Send HEAD request"""
        return self.request(RequestMethod.HEAD, url, **kwargs)
        
    def options(self, url: str, **kwargs: Any) -> Response:
        """Send OPTIONS request"""
        return self.request(RequestMethod.OPTIONS, url, **kwargs)
        
    def patch(self, url: str, data: Optional[Any] = None, **kwargs: Any) -> Response:
        """Send PATCH request"""
        return self.request(RequestMethod.PATCH, url, body=data, **kwargs)
        
    def stream(
        self,
        method: Union[str, RequestMethod],
        url: str,
        chunk_size: int = 8192,
        on_progress: Optional[Callable[[int, int], None]] = None,
        **kwargs: Any
    ) -> Iterator[bytes]:
        """Stream response content"""
        kwargs['stream'] = True
        response = self.request(method, url, **kwargs)
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        if isinstance(response.body, bytes):
            chunk = response.body
            downloaded += len(chunk)
            if on_progress:
                on_progress(len(chunk), total_size)
            yield chunk
        elif hasattr(response.body, '__iter__'):
            for chunk in response.body:
                downloaded += len(chunk)
                if on_progress:
                    on_progress(len(chunk), total_size)
                yield chunk
                
        yield b''
    
    def websocket(self, url: str) -> WebSocket:
        """Create WebSocket connection"""
        if self.base_url and not url.startswith(('ws://', 'wss://')):
            scheme = 'wss://' if urlparse(self.base_url).scheme == 'https' else 'ws://'
            url = f"{scheme}{urlparse(self.base_url).netloc}/{url.lstrip('/')}"
        return WebSocket(self, url)
    
    def close(self) -> None:
        """Close client and release resources"""
        self.http.pool.close()
        
    def __enter__(self) -> 'Client':
        return self
        
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()