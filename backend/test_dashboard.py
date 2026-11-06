import json
import os
import sys
import unittest
from datetime import date, datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(__file__))
import dashboard
import seed_sales


class DashboardTests(unittest.TestCase):
    def test_period_and_moscow_midnight(self):
        first, last, start, end = dashboard.period(7, date(2026, 11, 6))
        self.assertEqual((str(first), str(last)), ('2026-10-31', '2026-11-06'))
        self.assertEqual(dashboard.day_key(start - 1), '2026-10-30')
        self.assertEqual(dashboard.day_key(start), '2026-10-31')
        self.assertEqual(dashboard.day_key(end - 1), '2026-11-06')
        self.assertEqual(dashboard.day_key(end), '2026-11-07')

    def test_sales_totals(self):
        stamp = int(datetime(2026, 11, 6, 0, 0, tzinfo=ZoneInfo('Europe/Moscow')).timestamp())
        daily, types = dashboard.aggregate_sales([
            {'purchased_at': stamp - 1, 'membership_type': 'Месяц', 'amount_kopecks': 100},
            {'purchased_at': stamp, 'membership_type': 'Год', 'amount_kopecks': 250}],
            ['2026-11-05', '2026-11-06'])
        self.assertEqual([x['revenue_kopecks'] for x in daily], [100, 250])
        self.assertEqual(sum(x['revenue_kopecks'] for x in types), 350)

    def test_seed_repeatable_unique_and_sparse(self):
        a = seed_sales.make_rows(date(2026, 11, 6), 42)
        self.assertEqual(a, seed_sales.make_rows(date(2026, 11, 6), 42))
        self.assertEqual(len(a), len({row['id'] for row in a}))
        self.assertGreater(len(a), 30)
        self.assertLess(len({dashboard.day_key(row['purchased_at']) for row in a}), 30)

    def test_access_and_invalid_period(self):
        with patch.dict(os.environ, {'DASHBOARD_ACCESS_SECRET': 'test-secret'}, clear=True):
            event = {'httpMethod': 'GET', 'headers': {}, 'queryStringParameters': {'days': '7'}}
            self.assertEqual(dashboard.handler(event, None)['statusCode'], 401)
            event['headers']['Authorization'] = 'Bearer test-secret'
            event['queryStringParameters']['days'] = '90'
            self.assertEqual(dashboard.handler(event, None)['statusCode'], 400)

    def test_partial_failure_no_personal_data_or_false_zero(self):
        with patch.dict(os.environ, {'METRICA_OAUTH_TOKEN': 'fake'}, clear=True), \
             patch.object(dashboard, 'ydb_rows', side_effect=lambda table, *_: [
                 {'received_at': 1, 'message': 'private', 'contacts': 'private'}] if table == 'submissions' else []), \
             patch.object(dashboard, 'metrica_visits', side_effect=TimeoutError):
            result = dashboard.build(7)
        self.assertEqual(result['metrics']['submissions'], 1)
        self.assertEqual(result['metrics']['purchases'], 0)
        self.assertIsNone(result['metrics']['visits'])
        self.assertEqual(result['sources']['visits']['status'], 'unavailable')
        self.assertNotIn('private', json.dumps(result))


if __name__ == '__main__':
    unittest.main()
