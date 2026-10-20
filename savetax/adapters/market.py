"""Credential-free, read-only market MCP searches over HTTP JSON-RPC.

MCP transports tools over POST. The only callable tools here are the two
providers' product searches; no registration, cart, checkout, or write tool can
be invoked. Endpoints are constants, never derived from provider responses.
"""
from __future__ import annotations

import json
import re
from typing import Any

import requests
from requests.auth import AuthBase


PROVIDERS = {
    "daiso": "https://mcp.aka.page",
    "danawa": "https://mcp.ai.cowave.kr/mcp",
}
SEARCH_TOOLS = {"daiso": "daiso_search_products", "danawa": "search_products"}
PROTOCOL = "2025-03-26"
SECRET_PATTERN = re.compile(r"savetax_[A-Za-z0-9_-]{20,}")


class MarketError(RuntimeError):
    def __init__(self, message: str, *, status: int | None = None,
                 code: str | None = None, stage: str = "validation"):
        super().__init__(message)
        self.status = status
        self.code = code
        self.stage = stage


class _NoCredentials(AuthBase):
    """Suppress requests' implicit .netrc Authorization discovery."""

    def __call__(self, request):
        request.headers.pop("Authorization", None)
        return request


def _parse_rpc(content: bytes, request_id: int) -> dict:
    messages = []
    failed = False
    try:
        text = content.decode("utf-8-sig")
        if text.lstrip().startswith("{"):
            messages = [json.loads(text)]
        else:
            data = []
            # SSE events can split a JSON payload across several data lines.
            for line in text.replace("\r\n", "\n").split("\n") + [""]:
                if not line:
                    if data:
                        messages.append(json.loads("\n".join(data)))
                        data = []
                elif line.startswith("data:"):
                    data.append(line[5:].lstrip(" "))
    except (ValueError, UnicodeError):
        failed = True
    if not failed:
        for message in messages:
            if isinstance(message, dict) and message.get("jsonrpc") == "2.0" and message.get("id") == request_id:
                if "error" in message:
                    raise MarketError("Market MCP returned a JSON-RPC error", code="rpc_error", stage="rpc")
                if isinstance(message.get("result"), dict):
                    return message["result"]
    raise MarketError("Market MCP response did not match the request", code="invalid_response", stage="decode")


def _tool_result(result: dict) -> Any:
    if result.get("isError"):
        raise MarketError("Market search tool reported an error", code="tool_error", stage="tool")
    if "structuredContent" in result:
        return result["structuredContent"]
    texts = [part.get("text", "") for part in result.get("content", [])
             if isinstance(part, dict) and part.get("type") == "text"]
    for text in texts:
        try:
            return json.loads(text)
        except (ValueError, TypeError):
            pass
    return {"content": result.get("content", [])}


def _search_arguments(schema: dict, query: str, limit: int) -> dict:
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    query_name = next((name for name in (
        "query", "keyword", "search_query", "searchKeyword", "searchTerm",
        "search_term", "product_name", "q",
    ) if name in properties), None)
    if query_name is None:
        raise MarketError("Search query field is absent from provider schema", code="unsupported_schema", stage="schema")
    arguments = {query_name: query}
    for name in ("limit", "max_results", "count", "pageSize", "page_size", "size"):
        if name in properties:
            field = properties[name]
            value = min(limit, field.get("maximum", limit))
            value = max(value, field.get("minimum", value))
            arguments[name] = int(value)
            break
    for name in required:
        if name in arguments:
            continue
        field = properties.get(name, {})
        if "default" in field:
            arguments[name] = field["default"]
        elif name in {"page", "pageNo", "page_number"} and field.get("type") == "integer":
            arguments[name] = max(1, field.get("minimum", 1))
        elif len(field.get("enum", [])) == 1:
            arguments[name] = field["enum"][0]
        else:
            raise MarketError("Provider requires an unsupported search argument", code="unsupported_schema", stage="schema")
    return arguments


class MarketClient:
    """Search one fixed provider without reading or sending SaveTax tokens."""

    def __init__(self, provider: str):
        if provider not in PROVIDERS:
            raise MarketError("Market provider must be daiso or danawa")
        self.provider = provider
        self._next_id = 1
        self._session_id = None
        self._protocol = PROTOCOL
        self._schema = None

    def _rpc(self, method: str, params: dict | None = None, *, notification: bool = False) -> dict:
        if method not in {"initialize", "notifications/initialized", "tools/list", "tools/call"}:
            raise MarketError("Only read-only market MCP operations are allowed")
        if method == "tools/call" and (params or {}).get("name") != SEARCH_TOOLS[self.provider]:
            raise MarketError("Only the product search tool is allowed")
        payload = {"jsonrpc": "2.0", "method": method}
        request_id = self._next_id
        if not notification:
            payload["id"] = request_id
            self._next_id += 1
        if params is not None:
            payload["params"] = params
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
                   "User-Agent": "Mozilla/5.0"}
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        if method != "initialize":
            headers["MCP-Protocol-Version"] = self._protocol
        error = None
        try:
            response = requests.post(PROVIDERS[self.provider], json=payload, headers=headers,
                                     auth=_NoCredentials(), timeout=30, allow_redirects=False)
        except requests.RequestException as exc:
            error = MarketError("Market MCP transport failed (" + type(exc).__name__ + ")", stage="transport")
        if error is not None:
            raise error from None
        status = response.status_code
        if not 200 <= status < 300:
            response.close()
            code = "redirect_blocked" if 300 <= status < 400 else "http_error"
            raise MarketError(f"{self.provider} MCP HTTP {status}", status=status, code=code, stage="http")
        session_id = response.headers.get("Mcp-Session-Id")
        if session_id and len(session_id) <= 512 and not any(ord(c) < 33 for c in session_id):
            self._session_id = session_id
        content = response.content
        response.close()
        if notification:
            return {}
        return _parse_rpc(content, request_id)

    def _initialize_danawa(self) -> None:
        result = self._rpc("initialize", {
            "protocolVersion": PROTOCOL, "capabilities": {},
            "clientInfo": {"name": "savetax-research-agent", "version": "0.1.0"},
        })
        protocol = result.get("protocolVersion", PROTOCOL)
        if protocol not in {"2024-11-05", "2025-03-26", "2025-06-18"}:
            raise MarketError("Provider negotiated an unsupported MCP protocol", stage="schema")
        self._protocol = protocol
        self._rpc("notifications/initialized", notification=True)
        tools = self._rpc("tools/list", {}).get("tools", [])
        for tool in tools:
            if isinstance(tool, dict) and tool.get("name") == "search_products":
                self._schema = tool.get("inputSchema", {})
                return
        raise MarketError("Provider does not expose search_products", code="search_tool_missing", stage="schema")

    def search(self, query: str, limit: int = 5) -> dict:
        if not isinstance(query, str) or not query.strip() or SECRET_PATTERN.search(query):
            raise MarketError("A non-sensitive product search query is required")
        if type(limit) is not int or not 1 <= limit <= 50:
            raise MarketError("Search limit must be an integer from 1 to 50")
        if self.provider == "daiso":
            arguments = {"query": query, "pageSize": limit}
        else:
            if self._schema is None:
                self._initialize_danawa()
            arguments = _search_arguments(self._schema, query, limit)
        result = self._rpc("tools/call", {"name": SEARCH_TOOLS[self.provider], "arguments": arguments})
        return {"provider": self.provider, "query": query, "result": _tool_result(result)}
