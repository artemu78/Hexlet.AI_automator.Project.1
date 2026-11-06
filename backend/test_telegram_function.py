import errno
import io
import json
import os
import socket
import ssl
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import telegram_function as api


class DiagnosticsTests(unittest.TestCase):
    def invoke(self, error):
        with patch.dict(os.environ, {'BOT_TOKEN': 'secret-token', 'ADMIN_CHAT_ID': '123'}), patch.object(api, 'urlopen', side_effect=error):
            result = api.handler({'httpMethod': 'GET'}, None)
        self.assertNotIn('secret-token', result['body'])
        return result, json.loads(result['body'])

    def test_network_categories(self):
        for reason, category in [
            (socket.gaierror(-2, 'DNS failed'), 'dns_error'),
            (TimeoutError('secret-token'), 'timeout'),
            (ssl.SSLCertVerificationError(1, 'bad certificate'), 'tls_certificate_error'),
            (ssl.SSLError(1, 'TLS failed'), 'tls_error'),
            (ConnectionRefusedError(errno.ECONNREFUSED, 'refused'), 'connection_refused'),
            (ConnectionResetError(errno.ECONNRESET, 'reset'), 'connection_reset'),
            (OSError(errno.ENETUNREACH, 'no route'), 'network_unreachable'),
            ('secret-token in arbitrary exception text', 'network_error'),
        ]:
            with self.subTest(category=category):
                result, body = self.invoke(URLError(reason))
                self.assertEqual(body['diagnostics']['category'], category)
                self.assertEqual(body['diagnostics']['host'], api.PROXY_HOST)
                self.assertEqual(body['diagnostics']['route'], 'aws-proxy')
                self.assertEqual(body['diagnostics']['restriction_assessment'], 'inconclusive')
                self.assertEqual(result['statusCode'], 504 if category == 'timeout' else 502)

    def test_unwrapped_timeout_and_tls_error(self):
        for error, category in [(TimeoutError(), 'timeout'), (ssl.SSLError(), 'tls_error')]:
            _, body = self.invoke(error)
            self.assertEqual(body['diagnostics']['category'], category)

    def test_http_error_does_not_expose_secret_url(self):
        _, body = self.invoke(HTTPError('https://api.telegram.org/botsecret-token/sendMessage', 401, 'secret-token', {}, None))
        self.assertEqual(body['diagnostics']['upstream_http_status'], 401)
        self.assertEqual(body['diagnostics']['category'], 'http_error')

    def test_success(self):
        with patch.dict(os.environ, {'BOT_TOKEN': 'secret-token', 'ADMIN_CHAT_ID': '123'}), patch.object(api, 'urlopen', return_value=io.BytesIO(b'{"ok":true,"result":{"message_id":42}}')) as request:
            result = api.handler({'httpMethod': 'GET'}, None)
        self.assertEqual(result['statusCode'], 200)
        outgoing = request.call_args.args[0]
        self.assertEqual(outgoing.full_url, f'https://{api.PROXY_HOST}/botsecret-token/sendMessage?destination=telegram')
        self.assertEqual(outgoing.get_method(), 'POST')
        self.assertEqual(json.loads(outgoing.data), {'chat_id': '123', 'text': 'Привет из Yandex Cloud Functions!'})
        self.assertEqual(json.loads(result['body']), {'ok': True, 'message_id': 42})


class VersionTests(unittest.TestCase):
    def test_version_does_not_require_credentials_or_send_message(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(api, "send_message") as send:
            for value in ("", "1", None):
                with self.subTest(value=value):
                    result = api.handler({"httpMethod": "GET", "queryStringParameters": {"version": value, "text": ""}}, None)
                    self.assertEqual(result["statusCode"], 200)
                    self.assertEqual(result["headers"]["Cache-Control"], "no-store")
                    self.assertEqual(json.loads(result["body"]), {"service": "telegram-function", "version": api.FUNCTION_VERSION})
            send.assert_not_called()

    def test_post_version_keeps_method_restriction(self):
        with patch.object(api, "send_message") as send:
            result = api.handler({"httpMethod": "POST", "queryStringParameters": {"version": ""}}, None)
            self.assertEqual(result["statusCode"], 405)
            send.assert_not_called()
