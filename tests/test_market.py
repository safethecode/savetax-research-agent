"""MCP reads use fixed providers and never carry SaveTax credentials."""
import json
import io
import os
import unittest
from unittest.mock import patch

import requests

from savetax.market import MarketClient, MarketError


def reply(payload=None, status=200, sse=False, session=None):
    response = requests.Response()
    response.status_code = status
    text = json.dumps(payload, ensure_ascii=False) if payload is not None else ""
    if sse:
        text = ": heartbeat\nevent: message\ndata: " + text + "\n\n"
    response._content = text.encode("utf-8")
    response.raw = io.BytesIO(response._content)
    response.headers["Content-Type"] = "text/event-stream" if sse else "application/json"
    if session:
        response.headers["Mcp-Session-Id"] = session
    return response


class MarketTests(unittest.TestCase):
    def test_daiso_stateless_sse_search_preserves_korean_and_has_no_credentials(self):
        fixture = {"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": json.dumps({"products": [{"id": "1012542", "name": "한솔 복사용지", "price": 2000}]}, ensure_ascii=False)}]}}
        with patch.dict(os.environ, {"SAVETAX_TOKEN": "savetax_" + "a" * 40}), patch("savetax.adapters.market.requests.post", return_value=reply(fixture, sse=True)) as post:
            result = MarketClient("daiso").search("복사용지", limit=3)
        self.assertEqual(result["result"]["products"][0]["name"], "한솔 복사용지")
        self.assertEqual(result["provider"], "daiso")
        self.assertEqual(post.call_count, 1)
        self.assertEqual(post.call_args.args, ("https://mcp.aka.page",))
        self.assertEqual(post.call_args.kwargs["json"]["params"], {"name": "daiso_search_products", "arguments": {"query": "복사용지", "pageSize": 3}})
        self.assertNotIn("Authorization", post.call_args.kwargs["headers"])
        self.assertNotIn("savetax_", repr(post.call_args))
        self.assertFalse(post.call_args.kwargs["allow_redirects"])

    def test_danawa_initializes_and_uses_discovered_search_schema(self):
        tools = [{"name": "delete_everything", "inputSchema": {}}, {"name": "search_products", "inputSchema": {"type": "object", "properties": {"keyword": {"type": "string"}, "max_results": {"type": "integer", "maximum": 10}}, "required": ["keyword"]}}]
        fixtures = [
            reply({"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2025-03-26", "capabilities": {"tools": {}}, "serverInfo": {"name": "test", "version": "1"}}}, session="session-test"),
            reply(status=202),
            reply({"jsonrpc": "2.0", "id": 2, "result": {"tools": tools}}),
            reply({"jsonrpc": "2.0", "id": 3, "result": {"structuredContent": {"products": [{"price": 100}]}, "content": []}}),
        ]
        with patch("savetax.adapters.market.requests.post", side_effect=fixtures) as post:
            result = MarketClient("danawa").search("LCM200A", limit=20)
        self.assertEqual(result["result"], {"products": [{"price": 100}]})
        calls = post.call_args_list
        self.assertEqual([call.kwargs["json"]["method"] for call in calls], ["initialize", "notifications/initialized", "tools/list", "tools/call"])
        self.assertEqual(calls[-1].kwargs["json"]["params"], {"name": "search_products", "arguments": {"keyword": "LCM200A", "max_results": 10}})
        self.assertEqual(calls[-1].kwargs["headers"]["Mcp-Session-Id"], "session-test")
        self.assertTrue(all(call.args == ("https://mcp.ai.cowave.kr/mcp",) for call in calls))

    def test_rejects_unknown_provider_and_sensitive_query_before_network(self):
        with patch("savetax.adapters.market.requests.post") as post:
            with self.assertRaises(MarketError):
                MarketClient("https://evil.test")
            for query in ["", "savetax_" + "a" * 40]:
                with self.assertRaises(MarketError):
                    MarketClient("daiso").search(query)
            for limit in [0, 51, True]:
                with self.assertRaises(MarketError):
                    MarketClient("daiso").search("paper", limit=limit)
        post.assert_not_called()

    def test_http_403_is_identified_without_retry_or_response_html(self):
        fixture = reply(status=403)
        fixture._content = b"<html>Forbidden nginx</html>"
        with patch("savetax.adapters.market.requests.post", return_value=fixture) as post:
            with self.assertRaises(MarketError) as raised:
                MarketClient("danawa").search("monitor")
        self.assertEqual(raised.exception.status, 403)
        self.assertEqual(raised.exception.stage, "http")
        self.assertNotIn("<html>", str(raised.exception))
        self.assertEqual(post.call_count, 1)

    def test_redirect_is_never_followed(self):
        with patch("savetax.adapters.market.requests.post", return_value=reply(status=307)) as post:
            with self.assertRaises(MarketError) as raised:
                MarketClient("daiso").search("paper")
        self.assertEqual(raised.exception.code, "redirect_blocked")
        self.assertEqual(post.call_count, 1)

    def test_rpc_and_tool_errors_do_not_masquerade_as_results(self):
        fixtures = [
            {"jsonrpc": "2.0", "id": 1, "error": {"code": -32602, "message": "bad args"}},
            {"jsonrpc": "2.0", "id": 1, "result": {"isError": True, "content": [{"type": "text", "text": "not available"}]}},
        ]
        for fixture in fixtures:
            with self.subTest(fixture=fixture), patch("savetax.adapters.market.requests.post", return_value=reply(fixture)):
                with self.assertRaises(MarketError):
                    MarketClient("daiso").search("paper")

    def test_wrong_rpc_id_or_malformed_sse_cannot_satisfy_request(self):
        for fixture in [reply({"jsonrpc": "2.0", "id": 99, "result": {}}), reply({"id": 1}, sse=True)]:
            with self.subTest(body=fixture.content), patch("savetax.adapters.market.requests.post", return_value=fixture):
                with self.assertRaises(MarketError):
                    MarketClient("daiso").search("paper")

    def test_unrecognized_required_schema_is_not_guessed(self):
        fixtures = [
            reply({"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2025-03-26"}}), reply(status=202),
            reply({"jsonrpc": "2.0", "id": 2, "result": {"tools": [{"name": "search_products", "inputSchema": {"properties": {"keyword": {"type": "string"}, "account": {"type": "string"}}, "required": ["keyword", "account"]}}]}}),
        ]
        with patch("savetax.adapters.market.requests.post", side_effect=fixtures) as post:
            with self.assertRaises(MarketError) as raised:
                MarketClient("danawa").search("paper")
        self.assertEqual(raised.exception.stage, "schema")
        self.assertEqual(post.call_count, 3)


if __name__ == "__main__":
    unittest.main()
