import pytest
from snapex import Client
from snapex.exceptions import HTTPError

@pytest.fixture
def client():
    return Client()

def test_get_request(client):
    response = client.get('https://httpbin.org/get')
    assert response.status_code == 200
    assert 'args' in response.json()

def test_post_request(client):
    response = client.post('https://httpbin.org/post', json={'key': 'value'})
    assert response.status_code == 200
    assert response.json()['json']['key'] == 'value'

def test_invalid_url(client):
    with pytest.raises(HTTPError):
        client.get('invalid-url')

def test_stream_request(client):
    chunks = list(client.stream('GET', 'https://httpbin.org/bytes/1024', chunk_size=128))
    assert len(chunks) > 0
    assert len(b''.join(chunks)) == 1024