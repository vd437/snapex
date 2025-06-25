class SnapexError(Exception):
    """Base exception for all Snapex errors"""
    pass

class HTTPError(SnapexError):
    """HTTP request failed"""
    def __init__(self, message: str, response=None):
        self.response = response
        super().__init__(message)

class TimeoutError(SnapexError):
    """Request timed out"""
    pass

class ConnectionError(SnapexError):
    """Network connection error"""
    pass

class TooManyRedirects(SnapexError):
    """Too many redirects"""
    pass

class InvalidURL(SnapexError):
    """Invalid URL provided"""
    pass

class StreamError(SnapexError):
    """Error during streaming"""
    pass

class WebSocketError(SnapexError):
    """WebSocket related error"""
    pass

class CacheError(SnapexError):
    """Cache related error"""
    pass