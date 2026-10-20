"""Compatibility exports; implementation lives in savetax.adapters.market."""
from .adapters.market import (
    json,
    re,
    Any,
    requests,
    AuthBase,
    PROVIDERS,
    SEARCH_TOOLS,
    PROTOCOL,
    SECRET_PATTERN,
    MarketError,
    _NoCredentials,
    _parse_rpc,
    _tool_result,
    _search_arguments,
    MarketClient,
)

__all__ = ['json', 're', 'Any', 'requests', 'AuthBase', 'PROVIDERS', 'SEARCH_TOOLS', 'PROTOCOL', 'SECRET_PATTERN', 'MarketError', 'MarketClient']
