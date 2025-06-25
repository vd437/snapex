import pytest
from unittest.mock import MagicMock, patch
from snapex.http import HTTPClient
from snapex.models import Request, Response, HTTPVersion
from snapex.exceptions import ConnectionError, InvalidURL

@pytest.fixture
def http_client():
    return HTTPClient()

def test_prepare_request(http_client):
    request = Request(RequestMethod.GET, "http://test.com")
    prepared = http_client._prepare_request(request)
    assert prepared.timeout is not None
    assert prepared.verify is True

def test_invalid_url_scheme(http_client):
    with pytest.raises(InvalidURL):
        http_client._create_connection("ftp://test.com", True, HTTPVersion.HTTP_1_1)

@patch('socket.create_connection')
def test_connection_error(mock_connect, http_client):
    mock_connect.side_effect = socket.error("Failed")
    with pytest.raises(ConnectionError):
        http_client._create_connection("http://test.com", True, HTTPVersion.HTTP_1_1)

@patch('snapex.connection.HTTP1Connection')
def test_request_success(mock_conn, http_client):
    mock_instance = MagicMock()
    mock_instance.send_request.return_value = Response(
        200, {}, b"test", Request(RequestMethod.GET, "http://test.com"), 0.1, HTTPVersion.HTTP_1_1
    )
    mock_conn.return_value = mock_instance
    
    request = Request(RequestMethod.GET, "http://test.com")
    response = http_client.request(request)
    
    assert response.status_code == 200
    assert response.content == b"test"

def test_should_cache(http_client):
    request = Request(RequestMethod.GET, "http://test.com", cache_policy=CachePolicy.ALWAYS)
    response = Response(200, {}, b"test", request, 0.1, HTTPVersion.HTTP_1_1)
    assert http_client._should_cache(request, response) is True

    request.cache_policy = CachePolicy.NEVER
    assert http_client._should_cache(request, response) is False