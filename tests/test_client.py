"""Network-free regression tests for credential and transport boundaries."""
from pathlib import Path
from tempfile import TemporaryDirectory
import io
import os
import unittest
from unittest.mock import patch
import zipfile

import requests

from savetax.client import SaveTaxClient, SaveTaxError, UnsafeUrlError


TOKEN = "savetax_" + "a" * 40
OTHER_TOKEN = "savetax_" + "b" * 40


def response(status=200, payload=None, body=b"", headers=None):
    result = requests.Response()
    result.status_code = status
    result._content = body
    result.headers.update(headers or {})
    if payload is not None:
        import json
        result._content = json.dumps(payload).encode()
        result.headers["Content-Type"] = "application/json"
    return result


class ClientTests(unittest.TestCase):
    def test_authorized_get_has_no_redirects_and_returns_json(self):
        # Break caught: a transport default follows redirects or drops bearer auth.
        with patch("savetax.client.requests.get", return_value=response(payload={"data": [1]})) as get:
            self.assertEqual(SaveTaxClient(TOKEN).get_json("https://api.savetax.now/v1/listings", {"has_activity": 1}), {"data": [1]})
        args, kwargs = get.call_args
        self.assertEqual(args, ("https://api.savetax.now/v1/listings",))
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer " + TOKEN)
        self.assertEqual(kwargs["params"], {"has_activity": 1})
        self.assertFalse(kwargs["allow_redirects"])
        self.assertEqual(kwargs["timeout"], 30)

    def test_blocks_credentials_outside_exact_https_allowlist(self):
        unsafe = [
            "http://api.savetax.now/v1/me", "https://api.savetax.now.evil.test/v1/me",
            "https://api.savetax.now@evil.test/v1/me", "https://user@api.savetax.now/v1/me",
            "https://api.savetax.now:444/v1/me", "https://api.savetax.now/v10/me",
            "https://api.savetax.now/docs/index.md", "https://hackathon.savetax.now/docs/api.md",
            "https://savetax-dataset.reform-dev-infra.workers.dev/other",
            "https://savetax-dataset.reform-dev-infra.workers.dev/latest/savetax-products.zip?x=1",
            "https://api.savetax.now/v1/../docs", "https://api.savetax.now/v1/%2e%2e/docs",
            "https://api.savetax.now/v1/me#fragment", "https://API.SAVETAX.NOW/v1/me",
            "https://api.savetax.now/v1/me\n",
        ]
        with patch("savetax.client.requests.get") as get:
            for url in unsafe:
                with self.subTest(url=url), self.assertRaises(UnsafeUrlError):
                    SaveTaxClient(TOKEN).get_json(url)
        get.assert_not_called()

    def test_rejects_token_in_query_or_params_without_exposing_it(self):
        with patch("savetax.client.requests.get") as get:
            for url, params in [
                ("https://api.savetax.now/v1/me?token=" + TOKEN, None),
                ("https://api.savetax.now/v1/me", {"q": TOKEN}),
                ("https://api.savetax.now/v1/me", {"Authorization": "something"}),
            ]:
                with self.subTest(params=params):
                    with self.assertRaises(UnsafeUrlError) as raised:
                        SaveTaxClient(TOKEN).get_json(url, params)
                    self.assertNotIn(TOKEN, str(raised.exception))
        get.assert_not_called()

    def test_redirect_is_an_error_without_leaking_location(self):
        with patch("savetax.client.requests.get", return_value=response(302, headers={"Location": "https://evil.test/" + TOKEN})) as get:
            with self.assertRaises(SaveTaxError) as raised:
                SaveTaxClient(TOKEN).get_json("https://hackathon.savetax.now/v1/events/current/me")
        self.assertEqual(raised.exception.status, 302)
        self.assertEqual(raised.exception.stage, "http")
        self.assertNotIn(TOKEN, str(raised.exception))
        self.assertEqual(get.call_count, 1)

    def test_http_error_preserves_status_and_service_code_but_not_body(self):
        fixture = response(401, {"error": {"code": "unauthorized", "message": "Bearer " + TOKEN}})
        with patch("savetax.client.requests.get", return_value=fixture):
            with self.assertRaises(SaveTaxError) as raised:
                SaveTaxClient(TOKEN).get_json("https://api.savetax.now/v1/me")
        self.assertEqual(raised.exception.status, 401)
        self.assertEqual(raised.exception.code, "unauthorized")
        self.assertNotIn(TOKEN, str(raised.exception))
        self.assertIsNone(raised.exception.__cause__)

    def test_error_code_cannot_echo_credential_as_a_substring(self):
        with patch("savetax.client.requests.get", return_value=response(401, {"code": "echo_" + TOKEN})):
            with self.assertRaises(SaveTaxError) as raised:
                SaveTaxClient(TOKEN).get_json("https://api.savetax.now/v1/me")
        self.assertNotIn(TOKEN, str(raised.exception))
        self.assertEqual(raised.exception.code, "http_error")

    def test_transport_error_never_keeps_raw_request_or_exception(self):
        with patch("savetax.client.requests.get", side_effect=requests.ConnectionError("Bearer " + TOKEN)):
            with self.assertRaises(SaveTaxError) as raised:
                SaveTaxClient(TOKEN).get_json("https://api.savetax.now/v1/me")
        self.assertEqual(raised.exception.stage, "transport")
        self.assertNotIn(TOKEN, str(raised.exception))
        self.assertIsNone(raised.exception.__cause__)
        self.assertTrue(raised.exception.__suppress_context__)

    def test_repr_and_response_redaction_hide_credentials(self):
        client = SaveTaxClient(TOKEN)
        fixture = {"echo": TOKEN, "nested": {"Authorization": "Bearer " + TOKEN, "access_token": OTHER_TOKEN}, TOKEN: "bad key"}
        with patch("savetax.client.requests.get", return_value=response(payload=fixture)):
            result = client.get_json("https://api.savetax.now/v1/me")
        self.assertNotIn(TOKEN, repr(client))
        self.assertNotIn(TOKEN, repr(result))
        self.assertNotIn(OTHER_TOKEN, repr(result))

    def test_env_precedes_guide_and_explicit_token_precedes_env(self):
        with TemporaryDirectory() as folder:
            guide = Path(folder) / "private.md"
            guide.write_text("Authorization: Bearer " + OTHER_TOKEN, encoding="utf-8")
            with patch.dict(os.environ, {"SAVETAX_TOKEN": TOKEN}):
                client = SaveTaxClient(guide_path=guide)
                explicit = SaveTaxClient(OTHER_TOKEN, guide_path=guide)
            with patch("savetax.client.requests.get", return_value=response(payload={})) as get:
                client.get_json("https://api.savetax.now/v1/me")
                self.assertEqual(get.call_args.kwargs["headers"]["Authorization"], "Bearer " + TOKEN)
                explicit.get_json("https://api.savetax.now/v1/me")
                self.assertEqual(get.call_args.kwargs["headers"]["Authorization"], "Bearer " + OTHER_TOKEN)

    def test_reads_only_one_unambiguous_guide_credential(self):
        with TemporaryDirectory() as folder, patch.dict(os.environ, {}, clear=True):
            guide = Path(folder) / "private.md"
            guide.write_text("Bearer " + TOKEN + "\nrepeat " + TOKEN, encoding="utf-8")
            client = SaveTaxClient(guide_path=guide)
            with patch("savetax.client.requests.get", return_value=response(payload={})) as get:
                client.get_json("https://api.savetax.now/v1/me")
                self.assertEqual(get.call_args.kwargs["headers"]["Authorization"], "Bearer " + TOKEN)
            guide.write_text(TOKEN + "\n" + OTHER_TOKEN, encoding="utf-8")
            with self.assertRaises(SaveTaxError):
                SaveTaxClient(guide_path=guide)

    def test_missing_invalid_credentials_fail_before_network(self):
        with TemporaryDirectory() as folder, patch.dict(os.environ, {}, clear=True), patch("savetax.client.requests.get") as get:
            for token in ["", "not-a-token", TOKEN + "\r\nX-Evil: yes"]:
                with self.subTest(token_length=len(token)), self.assertRaises(SaveTaxError):
                    SaveTaxClient(token)
            with self.assertRaises(SaveTaxError):
                SaveTaxClient(guide_path=Path(folder) / "missing.md")
        get.assert_not_called()

    def test_invalid_json_is_a_sanitized_error(self):
        with patch("savetax.client.requests.get", return_value=response(body=TOKEN.encode())):
            with self.assertRaises(SaveTaxError) as raised:
                SaveTaxClient(TOKEN).get_json("https://api.savetax.now/v1/me")
        self.assertEqual(raised.exception.stage, "decode")
        self.assertNotIn(TOKEN, str(raised.exception))

    def test_download_streams_zip_from_only_official_url(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("dataset/README.md", "hello")
        fixture = response(body=buffer.getvalue())
        fixture.raw = io.BytesIO(buffer.getvalue())
        with TemporaryDirectory() as folder:
            destination = Path(folder) / "dataset.zip"
            with patch("savetax.client.requests.get", return_value=fixture) as get:
                saved = SaveTaxClient(TOKEN).download_dataset(destination)
            self.assertEqual(saved, destination)
            self.assertTrue(zipfile.is_zipfile(saved))
            self.assertEqual(get.call_args.args, ("https://savetax-dataset.reform-dev-infra.workers.dev/latest/savetax-products.zip",))
            self.assertTrue(get.call_args.kwargs["stream"])
            self.assertFalse(get.call_args.kwargs["allow_redirects"])

    def test_failed_or_invalid_download_leaves_no_partial_or_overwrite(self):
        with TemporaryDirectory() as folder:
            destination = Path(folder) / "dataset.zip"
            destination.write_bytes(b"original")
            for fixture in [response(403, {"code": "forbidden"}), response(body=b"not zip")]:
                fixture.raw = io.BytesIO(fixture.content)
                with patch("savetax.client.requests.get", return_value=fixture):
                    with self.assertRaises(SaveTaxError):
                        SaveTaxClient(TOKEN).download_dataset(destination)
                self.assertEqual(destination.read_bytes(), b"original")
                self.assertEqual(list(Path(folder).iterdir()), [destination])


if __name__ == "__main__":
    unittest.main()
