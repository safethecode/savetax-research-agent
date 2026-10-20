"""Non-secret, explicitly validated settings for one local model invocation."""
from dataclasses import asdict, dataclass
import ipaddress
import math
import re
from urllib.parse import urlsplit


@dataclass(frozen=True)
class LocalProfile:
    model: str = 'qwen3.5:9b'
    base_url: str = 'http://127.0.0.1:11434'
    timeout: float = 180
    num_ctx: int = 8192
    num_predict: int = 1536
    think: bool = False

    def __post_init__(self):
        if (not isinstance(self.model, str)
                or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}', self.model)):
            raise ValueError('A valid explicit local model name is required')
        if (type(self.timeout) not in (int, float) or not math.isfinite(self.timeout)
                or not 0 < self.timeout <= 3600):
            raise ValueError('Local timeout must be positive and at most 3600 seconds')
        for value in (self.num_ctx, self.num_predict):
            if type(value) is not int or value <= 0:
                raise ValueError('Local context and generation limits must be positive integers')
        if type(self.think) is not bool:
            raise ValueError('Local thinking mode must be boolean')
        try:
            if (not isinstance(self.base_url, str) or '?' in self.base_url or '#' in self.base_url
                    or any(ord(c) < 33 or ord(c) > 126 for c in self.base_url)):
                raise ValueError
            parsed = urlsplit(self.base_url)
            address = ipaddress.ip_address(parsed.hostname)
            if (parsed.scheme != 'http' or not address.is_loopback
                    or parsed.username is not None or parsed.password is not None
                    or parsed.path not in ('', '/') or parsed.query or parsed.fragment
                    or (parsed.port is not None and not 1 <= parsed.port <= 65535)):
                raise ValueError
        except (ValueError, TypeError, AttributeError):
            raise ValueError('Ollama requires an HTTP loopback IP URL without credentials or a path') from None
        object.__setattr__(self, 'base_url', self.base_url.rstrip('/'))

    def as_dict(self):
        return asdict(self)
