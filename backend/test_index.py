import json
import os
import unittest
import uuid
from unittest.mock import patch

import index as api


class HandlerTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'ALLOWED_ORIGINS': 'https://example.com', 'IP_HASH_SECRET': 'test-secret'})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.data = {'id': str(uuid.uuid4()), 'message': ' hello ', 'contacts': ' @test '}

    def request(self, **changes):
        event = {'httpMethod': 'POST', 'headers': {'Origin': 'https://example.com'},
                 'body': json.dumps(self.data), 'requestContext': {'identity': {'sourceIp': '192.0.2.1'}}}
        event.update(changes)
        return api.handler(event, None)

    def test_save_confirmation_and_ip_hash(self):
        with patch.object(api, 'save') as save:
            response = self.request()
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), {'status': 'saved', 'id': self.data['id']})
        args = save.call_args.args
        self.assertEqual(args[:3], (self.data['id'], 'hello', '@test'))
        self.assertEqual(len(args[3]), 64)
        self.assertNotIn('192.0.2.1', args[3])

    def test_boundaries_and_types(self):
        for field, maximum in [('message', 1000), ('contacts', 100)]:
            for value, expected in [('a' * maximum, 200), ('😀' * maximum, 200),
                                    ('a' * (maximum + 1), 400), ('   ', 400), (None, 400), (1, 400)]:
                with self.subTest(field=field, length=len(str(value))):
                    data = {**self.data, field: value}
                    with patch.object(api, 'save') as save:
                        result = self.request(body=json.dumps(data))
                    self.assertEqual(result['statusCode'], expected)
                    self.assertEqual(save.called, expected == 200)

    def test_honeypot_and_malformed_input(self):
        for data in [{**self.data, 'website': 'bot'}, {**self.data, 'id': 'bad'}, [], None]:
            with patch.object(api, 'save') as save:
                self.assertEqual(self.request(body=json.dumps(data))['statusCode'], 400)
                save.assert_not_called()

    def test_errors_do_not_leak_data(self):
        with patch.object(api, 'save', side_effect=RuntimeError('secret database details')):
            result = self.request()
        self.assertEqual(result['statusCode'], 503)
        self.assertNotIn('secret', result['body'])

    def test_gateway_identity_required_and_no_read_endpoint(self):
        with patch.object(api, 'save') as save:
            self.assertEqual(self.request(requestContext={}, headers={'X-Forwarded-For': '192.0.2.1'})['statusCode'], 400)
            self.assertEqual(self.request(httpMethod='GET')['statusCode'], 405)
            save.assert_not_called()

    def test_cors(self):
        result = self.request(httpMethod='OPTIONS')
        self.assertEqual(result['statusCode'], 204)
        self.assertEqual(result['headers']['Access-Control-Allow-Origin'], 'https://example.com')
        result = self.request(headers={'Origin': 'https://evil.example'})
        self.assertEqual(result['statusCode'], 403)
        self.assertNotIn('Access-Control-Allow-Origin', result['headers'])

    def test_duplicate_precedes_limit_and_conflict(self):
        existing = {'message': 'hello', 'contacts': '@test'}
        self.assertFalse(api.decide(existing, [999] * 5, 'hello', '@test', 1000))
        with self.assertRaises(api.Rejected) as error:
            api.decide(existing, [], 'changed', '@test', 1000)
        self.assertEqual(error.exception.status, 409)

    def test_rolling_limit_and_expiry(self):
        self.assertTrue(api.decide(None, [401] * 4, '', '', 1000))
        with self.assertRaises(api.Rejected) as error:
            api.decide(None, [401] * 5, '', '', 1000)
        self.assertEqual(error.exception.status, 429)
        self.assertTrue(api.decide(None, [400] * 5, '', '', 1000))


class TransactionTests(unittest.TestCase):
    """Verify the production adapter keeps reads and both writes in one transaction."""
    def test_atomic_write_and_duplicate_path(self):
        from types import SimpleNamespace
        from unittest.mock import MagicMock
        import sys
        fake_sdk = SimpleNamespace(SerializableReadWrite=MagicMock())
        session = MagicMock()
        session.prepare.side_effect = lambda query: query
        tx = session.transaction.return_value.__enter__.return_value
        pool = MagicMock()
        pool.retry_operation_sync.side_effect = lambda fn: fn(session)
        with patch.dict(sys.modules, {'ydb': fake_sdk}), patch.object(api, 'get_pool', return_value=pool):
            tx.execute.side_effect = [[SimpleNamespace(rows=[]), SimpleNamespace(rows=[])], []]
            api.save('id', 'message', 'contacts', 'hash')
            self.assertEqual(session.transaction.call_count, 1)
            self.assertEqual(tx.execute.call_count, 2)
            query = tx.execute.call_args.args[0]
            self.assertIn('UPSERT INTO submissions', query)
            self.assertIn('UPSERT INTO rate_limits', query)
            self.assertTrue(tx.execute.call_args.kwargs['commit_tx'])
            self.assertEqual(tx.execute.call_args.args[1]['$key'], 'hash')
            tx.reset_mock()
            tx.execute.side_effect = [[SimpleNamespace(rows=[{'message': 'message', 'contacts': 'contacts'}]),
                                       SimpleNamespace(rows=[{'recent': '[999,999,999,999,999]'}])]]
            api.save('id', 'message', 'contacts', 'hash')
            self.assertEqual(tx.execute.call_count, 1)
            tx.commit.assert_called_once()


if __name__ == '__main__':
    unittest.main()
