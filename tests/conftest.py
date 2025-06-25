import pytest
from snapex import Client

@pytest.fixture(scope="session")
def base_url():
    return "https://httpbin.org"

@pytest.fixture
def client(base_url):
    with Client(base_url=base_url) as c:
        yield c

@pytest.fixture
def async_client(base_url):
    client = Client(base_url=base_url)
    yield client
    client.close()

@pytest.fixture(scope="module")
def vcr_config():
    return {
        "filter_headers": [('authorization', 'DUMMY')],
        "record_mode": "once",
        "match_on": ["method", "scheme", "host", "port", "path", "query"]
    }

@pytest.fixture(autouse=True)
def mock_environment(monkeypatch):
    """Mock environment variables for testing"""
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("API_KEY", "test_key")