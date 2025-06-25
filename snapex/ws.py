import asyncio
import ssl
from typing import Any, Optional, Dict, Union
from .exceptions import WebSocketError
from .models import RequestMethod

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

class WebSocket:
    """WebSocket client implementation"""
    
    def __init__(self, client: 'Client', url: str):
        if not WEBSOCKETS_AVAILABLE:
            raise WebSocketError("websockets package is not installed")
            
        self.client = client
        self.url = url
        self.connection = None
        self._ssl_context = ssl.create_default_context()
        if not self.client.http.verify:
            self._ssl_context.check_hostname = False
            self._ssl_context.verify_mode = ssl.CERT_NONE
        
    async def connect(self) -> None:
        """Establish WebSocket connection"""
        headers = self.client.default_headers.copy()
        try:
            self.connection = await websockets.connect(
                self.url,
                extra_headers=headers,
                ssl=self._ssl_context
            )
        except Exception as e:
            raise WebSocketError(f"Failed to connect: {e}")
    
    async def send(self, data: Union[str, bytes]) -> None:
        """Send WebSocket message"""
        if not self.connection:
            raise WebSocketError("WebSocket is not connected")
        try:
            await self.connection.send(data)
        except Exception as e:
            raise WebSocketError(f"Failed to send message: {e}")
    
    async def recv(self) -> Union[str, bytes]:
        """Receive WebSocket message"""
        if not self.connection:
            raise WebSocketError("WebSocket is not connected")
        try:
            return await self.connection.recv()
        except Exception as e:
            raise WebSocketError(f"Failed to receive message: {e}")
    
    async def close(self) -> None:
        """Close WebSocket connection"""
        if self.connection:
            try:
                await self.connection.close()
            except:
                pass
            self.connection = None
    
    async def __aenter__(self) -> 'WebSocket':
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()