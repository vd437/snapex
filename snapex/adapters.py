import socket
import ssl
from typing import Optional, Union
from .models import HTTPVersion
from .exceptions import ConnectionError

class BaseAdapter:
    """Base adapter for all protocol adapters"""
    
    def __init__(self, verify: bool = True):
        self.verify = verify
        self._ssl_context = self._create_ssl_context()
    
    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context with verification settings"""
        ctx = ssl.create_default_context()
        if not self.verify:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        return ctx
    
    def connect(self, host: str, port: int) -> Union[socket.socket, ssl.SSLSocket]:
        """Establish base TCP connection"""
        try:
            sock = socket.create_connection((host, port), timeout=5)
            return sock
        except socket.error as e:
            raise ConnectionError(f"Connection failed: {e}")

class HTTP1Adapter(BaseAdapter):
    """Adapter for HTTP/1.1 connections"""
    
    def __init__(self, verify: bool = True):
        super().__init__(verify)
        self.protocol = HTTPVersion.HTTP_1_1
    
    def wrap_socket(self, sock: socket.socket, host: str) -> ssl.SSLSocket:
        """Wrap socket with SSL if needed"""
        if self._ssl_context:
            return self._ssl_context.wrap_socket(sock, server_hostname=host)
        return sock

class HTTP2Adapter(BaseAdapter):
    """Adapter for HTTP/2 connections"""
    
    def __init__(self, verify: bool = True):
        super().__init__(verify)
        self.protocol = HTTPVersion.HTTP_2
        self._ssl_context.set_alpn_protocols(['h2', 'http/1.1'])
    
    def wrap_socket(self, sock: socket.socket, host: str) -> ssl.SSLSocket:
        """Wrap socket with SSL and ALPN for HTTP/2"""
        return self._ssl_context.wrap_socket(sock, server_hostname=host)

class HTTP3Adapter:
    """Adapter for HTTP/3 connections (QUIC)"""
    
    def __init__(self, verify: bool = True):
        self.protocol = HTTPVersion.HTTP_3
        self.verify = verify
    
    def connect(self, host: str, port: int):
        """Establish HTTP/3 connection using QUIC"""
        try:
            import aioquic
            # Implementation would go here
            raise NotImplementedError("HTTP/3 support is not fully implemented yet")
        except ImportError:
            raise ConnectionError("aioquic package is required for HTTP/3 support")

def get_adapter(version: HTTPVersion, verify: bool = True) -> BaseAdapter:
    """Factory function to get appropriate adapter"""
    adapters = {
        HTTPVersion.HTTP_1_1: HTTP1Adapter,
        HTTPVersion.HTTP_2: HTTP2Adapter,
        HTTPVersion.HTTP_3: HTTP3Adapter,
    }
    return adapters[version](verify)