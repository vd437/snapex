from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import (
    Any, Optional, Union, Dict, List, Tuple, Callable, 
    Iterator, AsyncIterator, TypeVar
)
from urllib.parse import urlparse

T = TypeVar('T')

class HTTPVersion(Enum):
    HTTP_1_1 = auto()
    HTTP_2 = auto()
    HTTP_3 = auto()

class RequestMethod(Enum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    HEAD = 'HEAD'
    OPTIONS = 'OPTIONS'
    PATCH = 'PATCH'
    TRACE = 'TRACE'
    CONNECT = 'CONNECT'

class RedirectPolicy(Enum):
    NEVER = auto()
    ALWAYS = auto()
    SAME_DOMAIN = auto()
    SAFE_METHODS = auto()

class CachePolicy(Enum):
    NEVER = auto()
    ALWAYS = auto()
    DEFAULT = auto()
    AGGRESSIVE = auto()

@dataclass
class TimeoutConfig:
    connect: Optional[float] = None
    read: Optional[float] = None
    write: Optional[float] = None
    pool: Optional[float] = None
    total: Optional[float] = None

@dataclass
class Request:
    method: RequestMethod
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[Union[bytes, str, Dict[str, Any], Iterator[bytes], AsyncIterator[bytes]]] = None
    params: Dict[str, Any] = field(default_factory=dict)
    cookies: Dict[str, str] = field(default_factory=dict)
    auth: Optional[Tuple[str, str]] = None
    timeout: Optional[TimeoutConfig] = None
    allow_redirects: bool = True
    max_redirects: int = 10
    http_version: HTTPVersion = HTTPVersion.HTTP_1_1
    stream: bool = False
    verify: bool = True
    cert: Optional[Union[str, Tuple[str, str]]] = None
    proxy: Optional[Union[str, Dict[str, str]]] = None
    cache_policy: CachePolicy = CachePolicy.DEFAULT
    redirect_policy: RedirectPolicy = RedirectPolicy.SAFE_METHODS
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Response:
    status_code: int
    headers: Dict[str, str]
    body: Union[bytes, str, None]
    request: Request
    elapsed: float
    http_version: HTTPVersion
    history: List['Response'] = field(default_factory=list)
    _content: Optional[bytes] = None
    _json: Optional[Any] = None

    @property
    def content(self) -> bytes:
        if self._content is not None:
            return self._content
        if isinstance(self.body, bytes):
            self._content = self.body
        elif isinstance(self.body, str):
            self._content = self.body.encode('utf-8')
        else:
            self._content = b''
        return self._content

    @property
    def text(self) -> str:
        if isinstance(self.body, str):
            return self.body
        return self.content.decode('utf-8', errors='replace')

    def json(self) -> Any:
        if self._json is None:
            import json
            self._json = json.loads(self.text)
        return self._json

    def raise_for_status(self) -> None:
        if 400 <= self.status_code < 600:
            from .exceptions import HTTPError
            raise HTTPError(f"HTTP {self.status_code}", response=self)