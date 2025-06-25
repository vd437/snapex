import ssl
from typing import Optional, Dict, Any, Union, Tuple, Callable
from urllib.parse import urlparse
from .connection import ConnectionPool, HTTP1Connection
from .models import Request, Response, HTTPVersion, TimeoutConfig
from .exceptions import InvalidURL, TooManyRedirects
from .cache import CacheBackend
from .utils import is_redirect, merge_headers, normalize_url

class HTTPClient:
    """Core HTTP client implementation"""
    
    def __init__(
        self,
        pool_size: int = 100,
        timeout: TimeoutConfig = TimeoutConfig(),
        verify: bool = True,
        cache_ttl: int = 300
    ):
        self.pool = ConnectionPool(max_size=pool_size)
        self.default_timeout = timeout
        self.verify = verify
        self.cache = CacheBackend(ttl=cache_ttl)
        self.ssl_context = self._create_ssl_context()
        
    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create default SSL context"""
        ctx = ssl.create_default_context()
        if not self.verify:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        return ctx
    
    def _prepare_request(self, request: Request) -> Request:
        """Prepare request with defaults"""
        if not request.timeout:
            request.timeout = self.default_timeout
            
        if request.verify is None:
            request.verify = self.verify
            
        return request
    
    def _should_cache(self, request: Request, response: Response) -> bool:
        """Determine if response should be cached"""
        if request.cache_policy == CachePolicy.NEVER:
            return False
        if request.cache_policy == CachePolicy.ALWAYS:
            return True
        return response.status_code in (200, 203, 300, 301, 302, 307, 308)
    
    def _should_follow_redirect(self, request: Request, response: Response) -> bool:
        """Determine if redirect should be followed"""
        if not request.allow_redirects:
            return False
        if not is_redirect(response.status_code):
            return False
        if len(response.history) >= request.max_redirects:
            raise TooManyRedirects(f"Exceeded max redirects ({request.max_redirects})")
        return True
    
    def _create_connection(self, url: str, verify: bool, http_version: HTTPVersion) -> HTTP1Connection:
        """Create appropriate connection for URL"""
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            raise InvalidURL(f"Unsupported scheme: {parsed.scheme}")
            
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        ssl_context = self.ssl_context if parsed.scheme == 'https' and verify else None
        
        sock = self.pool.get_connection(parsed.hostname, port, ssl_context, http_version)
        return HTTP1Connection(sock, parsed.hostname)
    
    def request(self, request: Request) -> Response:
        """Execute HTTP request"""
        request = self._prepare_request(request)
        request.url = normalize_url(request.url)
        
        # Check cache first
        if request.cache_policy != CachePolicy.NEVER:
            cached = self.cache.get(request)
            if cached:
                return cached
                
        # Execute request
        conn = self._create_connection(request.url, request.verify, request.http_version)
        try:
            response = conn.send_request(request)
            
            # Handle redirects
            if self._should_follow_redirect(request, response):
                redirect_url = response.headers.get('location')
                if not redirect_url:
                    return response
                    
                if not urlparse(redirect_url).netloc:
                    redirect_url = f"{request.url.scheme}://{request.url.netloc}{redirect_url}"
                    
                redirect_request = Request(
                    method=RequestMethod.GET if response.status_code == 303 else request.method,
                    url=redirect_url,
                    headers=request.headers,
                    cookies=request.cookies,
                    auth=request.auth,
                    timeout=request.timeout,
                    allow_redirects=request.allow_redirects,
                    max_redirects=request.max_redirects,
                    http_version=request.http_version,
                    stream=request.stream,
                    verify=request.verify,
                    cert=request.cert,
                    proxy=request.proxy,
                    cache_policy=request.cache_policy,
                    redirect_policy=request.redirect_policy
                )
                
                redirect_response = self.request(redirect_request)
                redirect_response.history = [response] + response.history
                response = redirect_response
            
            # Cache response if needed
            if self._should_cache(request, response):
                self.cache.set(request, response)
                
            return response
        finally:
            self.pool.release_connection(
                urlparse(request.url).hostname,
                urlparse(request.url).port or (443 if urlparse(request.url).scheme == 'https' else 80),
                conn.sock,
                ssl_context if urlparse(request.url).scheme == 'https' else None,
                request.http_version
            )