import socket
import ssl
import time
import threading
from typing import Optional, Deque, Dict, Tuple
from collections import defaultdict, deque
from .models import HTTPVersion
from .exceptions import ConnectionError, TimeoutError

class ConnectionPool:
    """Thread-safe connection pool with keep-alive support"""
    
    def __init__(self, max_size: int = 100, idle_timeout: float = 30.0):
        self.max_size = max_size
        self.idle_timeout = idle_timeout
        self._pools: Dict[Tuple[str, int, bool, HTTPVersion], Deque[socket.socket]] = defaultdict(deque)
        self._lock = threading.Lock()
        self._active_connections = 0

    def get_connection(
        self,
        host: str,
        port: int,
        ssl_context: Optional[ssl.SSLContext] = None,
        http_version: HTTPVersion = HTTPVersion.HTTP_1_1
    ) -> socket.socket:
        """Get a connection from pool or create new one"""
        with self._lock:
            key = (host, port, ssl_context is not None, http_version)
            
            # Clean up idle connections
            self._cleanup()
            
            if key in self._pools and self._pools[key]:
                return self._pools[key].popleft()
                
            if self._active_connections >= self.max_size:
                raise ConnectionError("Connection pool limit reached")
                
            self._active_connections += 1
            
        try:
            sock = socket.create_connection((host, port), timeout=5)
            if ssl_context:
                sock = ssl_context.wrap_socket(sock, server_hostname=host)
            return sock
        except Exception as e:
            with self._lock:
                self._active_connections -= 1
            raise ConnectionError(f"Failed to establish connection: {e}")

    def release_connection(
        self,
        host: str,
        port: int,
        sock: socket.socket,
        ssl_context: Optional[ssl.SSLContext] = None,
        http_version: HTTPVersion = HTTPVersion.HTTP_1_1
    ) -> None:
        """Return connection to pool"""
        if sock._closed:  # type: ignore
            with self._lock:
                self._active_connections -= 1
            return
            
        key = (host, port, ssl_context is not None, http_version)
        
        with self._lock:
            if len(self._pools[key]) < self.max_size:
                self._pools[key].append((time.time(), sock))
            else:
                self._active_connections -= 1
                sock.close()

    def _cleanup(self) -> None:
        """Clean up idle connections"""
        now = time.time()
        for key in list(self._pools.keys()):
            pool = self._pools[key]
            while pool:
                if now - pool[0][0] > self.idle_timeout:
                    _, sock = pool.popleft()
                    sock.close()
                    self._active_connections -= 1
                else:
                    break

    def close(self) -> None:
        """Close all connections in pool"""
        with self._lock:
            for pool in self._pools.values():
                for _, sock in pool:
                    try:
                        sock.close()
                    except:
                        pass
                pool.clear()
            self._pools.clear()
            self._active_connections = 0

class HTTP1Connection:
    """HTTP/1.1 connection handler"""
    
    def __init__(self, sock: socket.socket, host: str):
        self.sock = sock
        self.host = host
        self._lock = threading.Lock()
        
    def send_request(self, request: 'Request') -> 'Response':
        """Send HTTP/1.1 request"""
        from .models import Response
        from .utils import elapsed_time
        
        start = time.time()
        
        with self._lock:
            try:
                # Build request
                request_lines = [
                    f"{request.method.value} {request.url.path}?{request.url.query} HTTP/1.1",
                    f"Host: {self.host}",
                    *[f"{k}: {v}" for k, v in request.headers.items()],
                    "Connection: keep-alive",
                    "", ""
                ]
                
                # Send headers
                self.sock.sendall("\r\n".join(request_lines).encode())
                
                # Send body
                if request.body:
                    if isinstance(request.body, (str, bytes)):
                        body = request.body if isinstance(request.body, bytes) else request.body.encode()
                        self.sock.sendall(body)
                    elif hasattr(request.body, '__iter__'):
                        for chunk in request.body:
                            self.sock.sendall(chunk if isinstance(chunk, bytes) else chunk.encode())
                
                # Parse response
                return self._parse_response(request, elapsed_time(start))
            except socket.timeout as e:
                raise TimeoutError(str(e))
            except Exception as e:
                raise ConnectionError(str(e))
    
    def _parse_response(self, request: 'Request', elapsed: float) -> 'Response':
        """Parse HTTP/1.1 response"""
        from .models import Response
        
        # Read status line
        status_line = self._read_line()
        if not status_line.startswith("HTTP/1."):
            raise ConnectionError("Invalid HTTP response")
        
        _, status_code, _ = status_line.split(maxsplit=2)
        status_code = int(status_code)
        
        # Read headers
        headers = {}
        while True:
            line = self._read_line()
            if not line:
                break
            key, value = line.split(":", 1)
            headers[key.strip()] = value.strip()
        
        # Read body
        body = b''
        if "content-length" in headers:
            length = int(headers["content-length"])
            body = self._read_bytes(length)
        elif "transfer-encoding" in headers and headers["transfer-encoding"].lower() == "chunked":
            while True:
                chunk_size_line = self._read_line()
                chunk_size = int(chunk_size_line.split(";")[0], 16)
                if chunk_size == 0:
                    break
                body += self._read_bytes(chunk_size)
                self._read_line()  # Consume trailing \r\n
        
        return Response(
            status_code=status_code,
            headers=headers,
            body=body,
            request=request,
            elapsed=elapsed,
            http_version=HTTPVersion.HTTP_1_1
        )
    
    def _read_line(self) -> str:
        """Read a line from socket"""
        line = bytearray()
        while True:
            char = self.sock.recv(1)
            if char == b'\n':
                break
            line.extend(char)
        return line.decode().rstrip('\r')
    
    def _read_bytes(self, length: int) -> bytes:
        """Read exact number of bytes from socket"""
        data = bytearray()
        while len(data) < length:
            packet = self.sock.recv(length - len(data))
            if not packet:
                break
            data.extend(packet)
        return bytes(data)