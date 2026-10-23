"""Write-only contact API. Never log request bodies or database exceptions."""
import base64
import hashlib
import hmac
import ipaddress
import json
import os
import time
import uuid

_pool = None


class Rejected(Exception):
    def __init__(self, status, code):
        self.status, self.code = status, code


def normalize(data):
    if not isinstance(data, dict):
        raise Rejected(400, 'invalid_input')
    try:
        identifier = str(uuid.UUID(data['id']))
    except (KeyError, ValueError, TypeError, AttributeError):
        raise Rejected(400, 'invalid_input') from None
    values = []
    for field, maximum in [('message', 1000), ('contacts', 100)]:
        value = data.get(field)
        if not isinstance(value, str) or not 0 < len(value.strip()) <= maximum:
            raise Rejected(400, 'invalid_input')
        values.append(value.strip())
    if not isinstance(data.get('website', ''), str) or data.get('website', ''):
        raise Rejected(400, 'invalid_input')
    return identifier, *values


def decide(existing, recent, message, contacts, now):
    """Called inside the serializable transaction, before either table is written."""
    if existing:
        if existing['message'] != message or existing['contacts'] != contacts:
            raise Rejected(409, 'id_conflict')
        return False
    if len([stamp for stamp in recent if stamp > now - 600]) >= 5:
        raise Rejected(429, 'rate_limited')
    return True


def get_pool():
    global _pool
    if _pool is None:
        import ydb
        driver = ydb.Driver(endpoint=os.environ['YDB_ENDPOINT'],
                            database=os.environ['YDB_DATABASE'],
                            credentials=ydb.iam.MetadataUrlCredentials())
        driver.wait(timeout=5, fail_fast=True)
        _pool = ydb.SessionPool(driver, size=5)
    return _pool


def save(identifier, message, contacts, ip_key):
    import ydb

    def operation(session):
        now = int(time.time())
        with session.transaction(ydb.SerializableReadWrite()) as tx:
            lookup = session.prepare('''
                DECLARE $id AS Utf8; DECLARE $key AS Utf8;
                SELECT message, contacts FROM submissions WHERE id = $id;
                SELECT recent FROM rate_limits WHERE ip_key = $key;
            ''')
            result = tx.execute(lookup, {'$id': identifier, '$key': ip_key})
            existing = result[0].rows[0] if result[0].rows else None
            recent = json.loads(result[1].rows[0]['recent']) if result[1].rows else []
            if not decide(existing, recent, message, contacts, now):
                tx.commit()
                return
            recent = [stamp for stamp in recent if stamp > now - 600] + [now]
            insert = session.prepare('''
                DECLARE $id AS Utf8; DECLARE $message AS Utf8;
                DECLARE $contacts AS Utf8; DECLARE $now AS Uint64;
                DECLARE $key AS Utf8; DECLARE $recent AS Utf8;
                UPSERT INTO submissions (id, received_at, message, contacts)
                VALUES ($id, $now, $message, $contacts);
                UPSERT INTO rate_limits (ip_key, recent, updated_at)
                VALUES ($key, $recent, $now);
            ''')
            tx.execute(insert, {'$id': identifier, '$message': message,
                               '$contacts': contacts, '$now': now,
                               '$key': ip_key, '$recent': json.dumps(recent)}, commit_tx=True)

    get_pool().retry_operation_sync(operation)


def handler(event, context):
    headers = {k.lower(): v for k, v in (event.get('headers') or {}).items()}
    origin = headers.get('origin')
    allowed = os.environ.get('ALLOWED_ORIGINS', '').split(',')
    response_headers = {'Content-Type': 'application/json', 'Cache-Control': 'no-store',
                        'Vary': 'Origin'}
    if origin in allowed:
        response_headers.update({'Access-Control-Allow-Origin': origin,
                                 'Access-Control-Allow-Methods': 'POST, OPTIONS',
                                 'Access-Control-Allow-Headers': 'Content-Type'})

    def response(status, body):
        if status == 429:
            response_headers['Retry-After'] = '600'
        return {'statusCode': status, 'headers': response_headers,
                'body': json.dumps(body), 'isBase64Encoded': False}

    try:
        if origin and origin not in allowed:
            raise Rejected(403, 'origin_denied')
        method = event.get('httpMethod')
        if method == 'OPTIONS':
            return response(204, {})
        if method != 'POST':
            raise Rejected(405, 'method_not_allowed')
        raw = event.get('body') or ''
        if not isinstance(raw, str) or len(raw) > 16384:
            raise Rejected(413, 'body_too_large')
        if event.get('isBase64Encoded'):
            raw = base64.b64decode(raw, validate=True).decode('utf-8')
        identifier, message, contacts = normalize(json.loads(raw))
        # Only gateway service account can invoke this private function. Never use X-Forwarded-For.
        source = event.get('requestContext', {}).get('identity', {}).get('sourceIp')
        try:
            source = str(ipaddress.ip_address(source))
        except ValueError:
            raise Rejected(400, 'missing_source_ip') from None
        key = hmac.new(os.environ['IP_HASH_SECRET'].encode(), source.encode(), hashlib.sha256).hexdigest()
        save(identifier, message, contacts, key)
        return response(200, {'status': 'saved', 'id': identifier})
    except Rejected as error:
        return response(error.status, {'error': error.code})
    except (ValueError, UnicodeError):
        return response(400, {'error': 'invalid_input'})
    except Exception:
        return response(503, {'error': 'unavailable'})
