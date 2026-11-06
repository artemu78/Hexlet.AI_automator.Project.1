export function demoDashboard(days, anchor = new Date()) {
  const date = new Date(anchor.toLocaleString('en-US', { timeZone: 'Europe/Moscow' }));
  date.setHours(12, 0, 0, 0);
  const daily = [];
  const kinds = ['Месяц', 'Квартал', 'Год'];
  const prices = [390000, 990000, 2990000];
  const typeMap = Object.fromEntries(kinds.map((kind) => [kind, { membership_type: kind, purchases: 0, revenue_kopecks: 0 }]));
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(date);
    d.setDate(d.getDate() - i);
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    const count = (i * 7 + 3) % 4;
    const row = { date: key, purchases: count, revenue_kopecks: 0 };
    for (let j = 0; j < count; j++) {
      const kind = (i + j) % 3;
      row.revenue_kopecks += prices[kind];
      typeMap[kinds[kind]].purchases++;
      typeMap[kinds[kind]].revenue_kopecks += prices[kind];
    }
    daily.push(row);
  }
  const purchases = daily.reduce((sum, row) => sum + row.purchases, 0);
  const revenue = daily.reduce((sum, row) => sum + row.revenue_kopecks, 0);
  return {
    period: { days, from: daily[0].date, through: daily.at(-1).date, timezone: 'Europe/Moscow', current_day_incomplete: true },
    generated_at: new Date().toISOString(),
    metrics: { visits: days * 43 + 17, submissions: Math.round(days * 1.4), purchases, revenue_kopecks: revenue },
    sources: {
      visits: { status: 'educational', label: 'Подготовленные данные' },
      submissions: { status: 'educational', label: 'Подготовленные данные' },
      sales: { status: 'educational', label: 'Подготовленные данные' },
    },
    sales_daily: daily,
    sales_by_type: Object.values(typeMap),
  };
}
