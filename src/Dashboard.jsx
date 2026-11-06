import React, { useEffect, useState } from 'react';
import { Activity, RefreshCw } from 'lucide-react';
import { demoDashboard } from './dashboard-data';
import './dashboard.css';

const labels = { real: 'Реальные данные', educational: 'Учебные данные', unavailable: 'Источник недоступен', not_connected: 'Источник не подключён' };
const money = (kopecks) => `${new Intl.NumberFormat('ru-RU').format(kopecks / 100)} ₽`;

export default function Dashboard() {
  const [days, setDays] = useState(7);
  const [mode, setMode] = useState('demo');
  const [secret, setSecret] = useState('');
  const [data, setData] = useState(null);
  const [lastSuccess, setLastSuccess] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [refresh, setRefresh] = useState(0);
  const [failure, setFailure] = useState('');
  const api = import.meta.env.VITE_DASHBOARD_API_URL;

  useEffect(() => {
    if (mode === 'demo') {
      const result = demoDashboard(days);
      if (failure) {
        result.sources[failure] = { status: 'unavailable', label: 'Имитация отказа' };
        if (failure === 'visits') result.metrics.visits = null;
        if (failure === 'submissions') result.metrics.submissions = null;
        if (failure === 'sales') {
          result.metrics.purchases = null;
          result.metrics.revenue_kopecks = null;
          result.sales_daily = [];
          result.sales_by_type = [];
        }
      }
      setData(result);
      setLastSuccess(result.generated_at);
      setError('');
      return;
    }
    if (!api || !secret) {
      setData(null);
      setError(!api ? 'URL API дашборда не настроен.' : 'Введите ключ доступа к агрегатам.');
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError('');
    const url = new URL(api);
    url.searchParams.set('days', String(days));
    if (failure) url.searchParams.set('fail', failure);
    fetch(url, { headers: { Authorization: `Bearer ${secret}` }, signal: controller.signal, cache: 'no-store' })
      .then(async (response) => {
        if (!response.ok) throw new Error(response.status === 401 ? 'Неверный ключ доступа.' : `API вернул HTTP ${response.status}.`);
        return response.json();
      })
      .then((result) => { setData(result); setLastSuccess(result.generated_at); })
      .catch((cause) => { if (cause.name !== 'AbortError') { setData(null); setError(cause.message || 'Не удалось загрузить данные.'); } })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [days, mode, api, secret, refresh, failure]);

  const status = (name) => data?.sources[name];
  const card = (title, value, source) => <article className="dashboard-card" key={title}>
    <span>{title}</span><strong>{value == null ? '—' : value}</strong>
    <small>{status(source)?.label || 'Источник'} · {labels[status(source)?.status] || 'Нет данных'}</small>
  </article>;
  const sales = data?.sales_daily || [];
  const maxSales = Math.max(1, ...sales.map((row) => row.revenue_kopecks));

  return <main className="dashboard-page">
    <header className="dashboard-header"><a href={import.meta.env.BASE_URL} className="dashboard-brand"><Activity /> импульс<span>.</span></a><span>ПАНЕЛЬ УПРАВЛЯЮЩЕГО</span></header>
    <section className="dashboard-intro"><div><p className="dashboard-kicker">ОБЗОР КЛУБА</p><h1>Дашборд фитнес-клуба<span>.</span></h1><p>Посещения сайта, сохранённые заявки и учебные продажи абонементов.</p></div><div className="dashboard-mode">
      <label htmlFor="mode">Источник данных</label><select id="mode" value={mode} onChange={(event) => { setMode(event.target.value); setFailure(''); setLastSuccess(null); }}><option value="demo">Демонстрационные данные</option><option value="live">Подключённые источники</option></select>
    </div></section>
    <section className="dashboard-controls" aria-label="Управление дашбордом"><div className="dashboard-period"><span>Период</span>{[7, 30].map((value) => <button type="button" key={value} className={days === value ? 'active' : ''} onClick={() => setDays(value)}>{value} дней</button>)}</div><button type="button" className="dashboard-refresh" onClick={() => setRefresh((value) => value + 1)}><RefreshCw size={17} /> Обновить</button></section>
    {mode === 'live' && <section className="dashboard-access"><label htmlFor="dashboard-secret">Ключ доступа</label><input id="dashboard-secret" type="password" autoComplete="off" value={secret} onChange={(event) => setSecret(event.target.value)} placeholder="Введите ключ" /><small>Ключ хранится только в памяти вкладки. При закрытии потребуется ввод снова.</small></section>}
    {mode === 'demo' && <p className="dashboard-banner">Демонстрационные данные · подготовленный пример, не фактические показатели клуба</p>}
    <p className="dashboard-updated">{loading ? 'Загрузка… · ' : ''}{lastSuccess ? `Последнее успешное получение: ${new Date(lastSuccess).toLocaleString('ru-RU', { timeZone: 'Europe/Moscow' })} МСК` : 'Данные ещё не получены'}</p>
    {error && <p role="alert" className="dashboard-error">{error}</p>}
    {data && <><section className="dashboard-grid" aria-label="Показатели">
      {card('Визиты на сайт', data.metrics.visits, 'visits')}
      {card('Сохранённые заявки', data.metrics.submissions, 'submissions')}
      {card('Покупки абонементов', data.metrics.purchases, 'sales')}
      {card('Выручка', data.metrics.revenue_kopecks == null ? null : money(data.metrics.revenue_kopecks), 'sales')}
    </section>
    {Object.values(data.sources).some((item) => item.status === 'unavailable') && <p role="status" className="dashboard-error">Часть источников недоступна. Доступные показатели показаны отдельно.</p>}
    <section className="dashboard-panels"><article className="dashboard-panel"><h2>Продажи по дням</h2><p>Выручка, ₽ · Москва</p>{status('sales')?.status === 'unavailable' ? <div className="dashboard-empty">Данные о продажах недоступны</div> : sales.length && data.metrics.purchases ? <div className="dashboard-chart">{sales.map((row) => <div className="dashboard-bar-wrap" key={row.date} title={`${row.date}: ${money(row.revenue_kopecks)}, ${row.purchases} покупок`}><div className="dashboard-bar" style={{ height: `${Math.max(2, row.revenue_kopecks / maxSales * 100)}%` }} /><span>{row.date.slice(8)}</span></div>)}</div> : <div className="dashboard-empty">За период продаж нет</div>}</article>
    <article className="dashboard-panel"><h2>Типы абонементов</h2><p>Учебные покупки · количество и выручка</p>{data.sales_by_type.length ? <div className="dashboard-types">{data.sales_by_type.map((item) => <div key={item.membership_type}><span>{item.membership_type}</span><strong>{item.purchases} · {money(item.revenue_kopecks)}</strong></div>)}</div> : <div className="dashboard-empty">{status('sales')?.status === 'unavailable' ? 'Источник недоступен' : 'За период продаж нет'}</div>}</article></section>
    <p className="dashboard-footnote">Период: {data.period.from} — {data.period.through}, Europe/Moscow. Сегодняшний день ещё не завершён. Заявки считаются по сохранённым строкам, независимо от доставки Telegram.</p></>}
    <details className="dashboard-failure"><summary>Проверка отказа источника</summary><label htmlFor="failure">Источник</label><select id="failure" value={failure} onChange={(event) => setFailure(event.target.value)}><option value="">Без отказа</option><option value="visits">Визиты</option><option value="submissions">Заявки</option><option value="sales">Продажи</option></select></details>
  </main>;
}
