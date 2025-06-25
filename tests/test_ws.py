import pytest
from unittest.mock import AsyncMock, patch
from snapex import WebSocket
from snapex.exceptions import WebSocketError

@pytest.fixture
def mock_websocket():
    return AsyncMock()

@pytest.mark.asyncio
async def test_websocket_connect_success(mock_websocket):
    with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
        mock_connect.return_value = mock_websocket
        ws = WebSocket(None, 'wss://test.com')
        await ws.connect()
        assert ws.connection is not None

@pytest.mark.asyncio
async def test_websocket_send_receive(mock_websocket):
    mock_websocket.recv.return_value = "echo"
    ws = WebSocket(None, 'wss://test.com')
    ws.connection = mock_websocket
    
    await ws.send("test")
    response = await ws.recv()
    
    mock_websocket.send.assert_awaited_once_with("test")
    mock_websocket.recv.assert_awaited_once()
    assert response == "echo"

@pytest.mark.asyncio
async def test_websocket_not_connected():
    ws = WebSocket(None, 'wss://test.com')
    with pytest.raises(WebSocketError, match="not connected"):
        await ws.send("test")
    with pytest.raises(WebSocketError, match="not connected"):
        await ws.recv()

def test_websocket_missing_dependency():
    with patch.dict('sys.modules', {'websockets': None}):
        with pytest.raises(WebSocketError, match="not installed"):
            WebSocket(None, 'wss://test.com')