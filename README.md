# Snapex - The Ultimate HTTP Client for Python

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://github.com/yourusername/snapex/actions/workflows/tests.yml/badge.svg)

Snapex is a high-performance, full-featured HTTP client for Python with support for:

- HTTP/1.1, HTTP/2, and HTTP/3 (QUIC)
- WebSocket client (RFC 6455)
- Advanced connection pooling
- Intelligent caching system
- Synchronous and asynchronous APIs
- Comprehensive SSL/TLS configuration
- Automatic retry and failover

## Features

🚀 **Blazing Fast** - Optimized for high performance with minimal overhead  
🔒 **Secure** - Built-in SSL/TLS verification and certificate pinning  
🔄 **Async Ready** - Full support for async/await syntax  
📡 **Protocol Support** - HTTP/1.1, HTTP/2, HTTP/3, and WebSockets  
🧩 **Extensible** - Middleware and hooks system  

## Installation

```bash
pip install snapex
```

For optional dependencies:

```bash
# HTTP/2 support
pip install snapex[http2]

# HTTP/3 support
pip install snapex[http3]

# WebSocket support
pip install snapex[websocket]

# All features
pip install snapex[full]

# Development dependencies
pip install snapex[dev]
```

## Quick Start

### Basic Usage

```python
from snapex import Client

with Client() as client:
    # GET request
    response = client.get('https://api.example.com/data')
    print(response.json())

    # POST with JSON
    response = client.post('https://api.example.com/users', json={'name': 'John'})
    
    # Stream large response
    for chunk in client.stream('GET', 'https://example.com/large-file'):
        process_chunk(chunk)
```

### Advanced Usage

```python
# Custom client with configuration
client = Client(
    base_url="https://api.example.com",
    timeout=30.0,
    default_headers={'Authorization': 'Bearer token'},
    http_version=HTTPVersion.HTTP_2
)

# WebSocket client
async def chat():
    async with client.websocket('wss://echo.websocket.org') as ws:
        await ws.send("Hello!")
        print(await ws.recv())
```

## Contributing

Contributions are welcome! Please see our [Contribution Guidelines](CONTRIBUTING.md).

## License

MIT License - See [LICENSE](LICENSE) for details.