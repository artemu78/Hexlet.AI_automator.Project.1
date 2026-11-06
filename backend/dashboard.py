"""Aggregate-only dashboard API. Personal submission fields never leave YDB."""
import hmac
import json
import os
from datetime import datetime, timedelta, time, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

TZ = ZoneInfo('Europe/Moscow')


def period(days, today=None):
    if days not in (7, 30):
        raise ValueError('invalid period')
    today = today or datetime.now(TZ).date()
    first = today - timedelta(days=days - 1)
    start = int(datetime.combine(first, time.min, TZ).timestamp())
    end = int(datetime.combine(today + timedelta(days=1), time.min, TZ).timestamp())
    return first, today, start, end


def day_key(stamp):
    return datetime.fromtimestamp(stamp, timezone.utc).astimezone(TZ).date().isoformat()


def aggregate_sales(rows, dates):
    daily = {d: {'date': d, 'purchases': 0, 'revenue_kopecks': 0} for d in dates}
    types = {}
    for row in rows:
        day = day_key(row['purchased_at'])
        if day not in daily:
            continue
        amount = int(row['amount_kopecks'])
        daily[day]['purchases'] += 1
        daily[day]['revenue_kopecks'] += amount
        kind = row['membership_type']
        entry = types.setdefault(kind, {'membership_type': kind, 'purchases': 0, 'revenue_kopecks': 0})
        entry['purchases'] += 1
        entry['revenue_kopecks'] += amount
    return list(daily.values()), sorted(types.values(), key=lambda x: x['membership_type'])


def ydb_rows(table, start, end):
    from index import get_pool
    import ydb
    # Table and column names come only from this fixed whitelist.
    columns = {'submissions': ('received_at', 'received_at'),
               'demo_sales': ('purchased_at, membership_type, amount_kopecks', 'purchased_at')}
    selected, stamp = columns[table]

    def operation(session):
        query = session.prepare(f'''DECLARE $start AS Uint64; DECLARE $end AS Uint64;
            SELECT {selected} FROM {table} WHERE {stamp} >= $start AND {stamp} < $end;''')
        result = session.transaction(ydb.SerializableReadWrite()).execute(
            query, {'$start': start, '$end': end}, commit_tx=True)
        fields = ['received_at'] if table == 'submissions' else ['purchased_at', 'membership_type', 'amount_kopecks']
        return [{field: row[field] for field in fields} for row in result[0].rows]

    return get_pool().retry_operation_sync(operation)


def metrica_visits(first, last):
    token = os.environ['METRICA_OAUTH_TOKEN']
    query = urlencode({'ids': os.environ.get('METRICA_COUNTER_ID', '113655208'),
                       'metrics': 'ym:s:visits', 'date1': first.isoformat(),
                       'date2': last.isoformat()})
    request = Request('https://api-metrika.yandex.net/stat/v1/data?' + query,
                      headers={'Authorization': 'OAuth ' + token})
    with urlopen(request, timeout=5) as response:
        payload = json.load(response)
    totals = payload.get('totals')
    if not isinstance(totals, list) or not totals or not isinstance(totals[0], (int, float)):
        raise ValueError('invalid Metrica response')
    return int(totals[0])


def build(days, failed=''):
    first, last, start, end = period(days)
    dates = [(first + timedelta(days=i)).isoformat() for i in range(days)]
    result = {'period': {'days': days, 'from': dates[0], 'through': dates[-1],
                        'timezone': 'Europe/Moscow', 'current_day_incomplete': True},
              'generated_at': datetime.now(timezone.utc).isoformat(),
              'sources': {}, 'metrics': {'visits': None, 'submissions': None,
                                        'purchases': None, 'revenue_kopecks': None},
              'sales_daily': [], 'sales_by_type': []}
    for name, label in [('submissions', 'YDB submissions'), ('sales', 'YDB demo_sales'),
                        ('visits', 'Яндекс Метрика')]:
        if name == 'visits' and not os.environ.get('METRICA_OAUTH_TOKEN'):
            result['sources'][name] = {'status': 'not_connected', 'label': label}
            continue
        try:
            if failed == name:
                raise RuntimeError('simulated failure')
            if name == 'submissions':
                result['metrics']['submissions'] = len(ydb_rows('submissions', start, end))
            elif name == 'sales':
                rows = ydb_rows('demo_sales', start, end)
                result['sales_daily'], result['sales_by_type'] = aggregate_sales(rows, dates)
                result['metrics']['purchases'] = sum(item['purchases'] for item in result['sales_daily'])
                result['metrics']['revenue_kopecks'] = sum(item['revenue_kopecks'] for item in result['sales_daily'])
            else:
                result['metrics']['visits'] = metrica_visits(first, last)
            result['sources'][name] = {'status': 'educational' if name == 'sales' else 'real', 'label': label}
        except Exception:
            result['sources'][name] = {'status': 'unavailable', 'label': label}
    return result


def handler(event, context):
    headers = {k.lower(): v for k, v in (event.get('headers') or {}).items()}
    origin = headers.get('origin')
    allowed = os.environ.get('ALLOWED_ORIGINS', '').split(',')
    response_headers = {'Content-Type': 'application/json', 'Cache-Control': 'no-store', 'Vary': 'Origin'}
    if origin in allowed:
        response_headers.update({'Access-Control-Allow-Origin': origin,
                                 'Access-Control-Allow-Headers': 'Authorization',
                                 'Access-Control-Allow-Methods': 'GET, OPTIONS'})

    def reply(status, body):
        return {'statusCode': status, 'headers': response_headers,
                'body': json.dumps(body), 'isBase64Encoded': False}

    if origin and origin not in allowed:
        return reply(403, {'error': 'origin_denied'})
    if event.get('httpMethod') == 'OPTIONS':
        return reply(204, {})
    if event.get('httpMethod') != 'GET':
        return reply(405, {'error': 'method_not_allowed'})
    expected = os.environ.get('DASHBOARD_ACCESS_SECRET', '')
    if not expected or not hmac.compare_digest(headers.get('authorization', ''), 'Bearer ' + expected):
        return reply(401, {'error': 'unauthorized'})
    try:
        days = int((event.get('queryStringParameters') or {}).get('days', '7'))
        period(days)
    except (ValueError, TypeError):
        return reply(400, {'error': 'invalid_period'})
    params = event.get('queryStringParameters') or {}
    failure = params.get('fail', '') if os.environ.get('DASHBOARD_ALLOW_FAILURE_DEMO') == '1' else ''
    return reply(200, build(days, failure))
