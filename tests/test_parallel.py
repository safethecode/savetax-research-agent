"""Parallel searches keep credentials off URLs, results, and error messages."""
import io
import json
import os
import unittest
from unittest.mock import patch

import requests

from savetax.parallel import ParallelClient, ParallelError


KEY = 'parallel-test-only-credential-123456789'
OTHER_KEY = 'other-service-test-credential-123456789'
PAT = 'savetax_' + 'a' * 40


def response(payload=None, status=200, headers=None, body=None):
    result = requests.Response()
    result.status_code = status
    result._content = body if body is not None else json.dumps(payload).encode()
    result.raw = io.BytesIO(result._content)
    result.headers.update(headers or {})
    return result


class ParallelTests(unittest.TestCase):
    def test_fixed_search_transport_normalizes_and_caps_results(self):
        # Break caught: unsupported beta fields, redirects, or unbounded output.
        fixture = {'search_id': 'search_fixture', 'results': [
            {'url': 'https://shop.example/cable', 'title': '케이블',
             'excerpts': ['50m 순동', '일반판매가 100원'], 'publish_date': None},
            {'url': 'https://shop.example/other', 'title': '다른 상품', 'excerpts': []},
        ]}
        with patch('savetax.parallel.requests.post', return_value=response(fixture)) as post:
            result = ParallelClient(KEY).search('IM-PSW-0500', objective='동일 모델 판매가', max_results=1)
        self.assertEqual(result['results'], [{'source_url': 'https://shop.example/cable',
            'title': '케이블', 'excerpt': '50m 순동\n일반판매가 100원'}])
        self.assertEqual(result['search_id'], 'search_fixture')
        self.assertEqual(post.call_args.args, ('https://api.parallel.ai/v1/search',))
        sent = post.call_args.kwargs
        self.assertEqual(sent['json'], {'search_queries': ['IM-PSW-0500'],
            'objective': '동일 모델 판매가', 'mode': 'fast', 'max_chars_total': 8000})
        self.assertEqual(sent['headers']['x-api-key'], KEY)
        self.assertNotIn('Authorization', sent['headers'])
        self.assertFalse(sent['allow_redirects'])
        self.assertEqual(sent['timeout'], 30)
        prepared = requests.Request('POST', 'https://api.parallel.ai/v1/search',
            headers={'Authorization': 'Basic unwanted'}, auth=sent['auth']).prepare()
        self.assertNotIn('Authorization', prepared.headers)

    def test_objective_only_still_supplies_required_search_queries(self):
        # Break caught: objective-only calls produce a schema-invalid request.
        with patch.dict(os.environ, {'PARALLEL_API_KEY': KEY}), patch(
                'savetax.parallel.requests.post', return_value=response({'results': []})) as post:
            result = ParallelClient().search(objective='순동 차폐 케이블 판매처', max_results=10)
        self.assertEqual(result['results'], [])
        self.assertEqual(post.call_args.kwargs['json']['search_queries'], ['순동 차폐 케이블 판매처'])

    def test_invalid_input_or_secret_query_never_reaches_network(self):
        # Break caught: credentials in caller input are sent as search text.
        with patch.dict(os.environ, {'TYPESAFE_API_KEY': OTHER_KEY}), patch(
                'savetax.parallel.requests.post') as post:
            client = ParallelClient(KEY)
            for query in ['', None, '  ', KEY, PAT, 'prefix ' + OTHER_KEY]:
                with self.subTest(query_type=type(query).__name__), self.assertRaises(ParallelError):
                    client.search(query)
            for limit in [0, 11, True, '5']:
                with self.subTest(limit=limit), self.assertRaises(ParallelError):
                    client.search('cable', max_results=limit)
            with self.assertRaises(ParallelError):
                client.search('cable', objective=KEY)
            for key in ['', 'bad\r\nX-Injected: yes', None]:
                with patch.dict(os.environ, {}, clear=True), self.assertRaises(ParallelError):
                    ParallelClient(key)
        post.assert_not_called()

    def test_redacts_known_keys_and_drops_unsafe_result_urls(self):
        # Break caught: a server echo or credential-bearing URL leaks to artifacts.
        fixture = {'search_id': 'echo_' + KEY, 'results': [
            {'url': 'https://shop.example/' + KEY, 'title': 'bad', 'excerpts': []},
            {'url': 'javascript:alert(1)', 'title': 'bad', 'excerpts': []},
            {'url': 'https://user:pass@shop.example/', 'title': 'bad', 'excerpts': []},
            {'url': 'https://shop.example/?token=unrelated', 'title': 'bad', 'excerpts': []},
            {'url': 'https://shop.example/cable', 'title': KEY + OTHER_KEY,
             'excerpts': ['echo ' + PAT + ' ' + KEY]},
        ], 'extra': KEY}
        with patch.dict(os.environ, {'TEXT_MODEL_API_KEY': OTHER_KEY}), patch(
                'savetax.parallel.requests.post', return_value=response(fixture)):
            result = ParallelClient(KEY).search('cable')
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['title'], '[REDACTED][REDACTED]')
        for secret in [KEY, OTHER_KEY, PAT]:
            self.assertNotIn(secret, json.dumps(result))
        self.assertNotIn('extra', result)
        self.assertNotIn(KEY, repr(ParallelClient(KEY)))

    def test_http_errors_are_codes_only_without_retry(self):
        # Break caught: retry loops, response bodies, or redirect targets escape.
        for status in [302, 401, 429, 503]:
            fixture = response({'error': {'message': KEY, 'code': 'echo_' + KEY}},
                status=status, headers={'Retry-After': '17', 'Location': 'https://evil.example/' + KEY})
            with self.subTest(status=status), patch(
                    'savetax.parallel.requests.post', return_value=fixture) as post:
                with self.assertRaises(ParallelError) as raised:
                    ParallelClient(KEY).search('cable')
                self.assertEqual(raised.exception.status, status)
                self.assertEqual(raised.exception.retry_after, 17)
                self.assertEqual(post.call_count, 1)
                self.assertNotIn(KEY, str(raised.exception))
                self.assertIsNone(raised.exception.__cause__)

    def test_transport_and_bad_schema_errors_discard_raw_objects(self):
        # Break caught: request exception context or malformed JSON reaches logs.
        with patch('savetax.parallel.requests.post', side_effect=requests.ConnectionError(KEY)):
            with self.assertRaises(ParallelError) as raised:
                ParallelClient(KEY).search('cable')
        self.assertEqual(raised.exception.code, 'transport_error')
        self.assertIsNone(raised.exception.__context__)
        for payload in [[], {}, {'results': 'bad'}, {'results': [{'url': 'https://x.example',
                'title': 'bad', 'excerpts': [KEY, 12]}]}]:
            with patch('savetax.parallel.requests.post', return_value=response(payload)):
                with self.assertRaises(ParallelError) as raised:
                    ParallelClient(KEY).search('cable')
                self.assertEqual(raised.exception.code, 'invalid_response')
                self.assertNotIn(KEY, str(raised.exception))
        with patch('savetax.parallel.requests.post', return_value=response(body=KEY.encode())):
            with self.assertRaises(ParallelError) as raised:
                ParallelClient(KEY).search('cable')
        self.assertEqual(raised.exception.code, 'invalid_response')


if __name__ == '__main__':
    unittest.main()
