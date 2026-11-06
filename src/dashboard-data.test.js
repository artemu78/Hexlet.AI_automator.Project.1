import assert from 'node:assert/strict';
import test from 'node:test';
import { demoDashboard } from './dashboard-data.js';

test('demo totals match daily series and types for both periods', () => {
  for (const days of [7, 30]) {
    const data = demoDashboard(days, new Date('2026-11-06T12:00:00Z'));
    assert.equal(data.sales_daily.length, days);
    assert.equal(data.metrics.purchases, data.sales_daily.reduce((n, x) => n + x.purchases, 0));
    assert.equal(data.metrics.revenue_kopecks, data.sales_by_type.reduce((n, x) => n + x.revenue_kopecks, 0));
    assert.equal(data.period.through, '2026-11-06');
  }
});
