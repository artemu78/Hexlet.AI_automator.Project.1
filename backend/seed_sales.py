"""Deterministic synthetic sales. Preview by default; --write performs only UPSERTs."""
import argparse
import hashlib
import json
import random
from datetime import date, datetime, timedelta, time
from zoneinfo import ZoneInfo


def make_rows(anchor, seed=42):
    rng = random.Random(seed)
    kinds = [('Месяц', 390000), ('Квартал', 990000), ('Год', 2990000)]
    rows = []
    for offset in range(30):
        day = anchor - timedelta(days=29 - offset)
        for number in range(rng.randrange(4)):
            kind, amount = kinds[rng.randrange(len(kinds))]
            stamp = int(datetime.combine(day, time(10 + rng.randrange(11), rng.randrange(60)),
                                         ZoneInfo('Europe/Moscow')).timestamp())
            identifier = hashlib.sha256(f'{seed}:{day}:{number}'.encode()).hexdigest()[:32]
            rows.append({'id': identifier, 'purchased_at': stamp,
                         'membership_type': kind, 'amount_kopecks': amount})
    return rows


def write_rows(rows, pool):
    import ydb
    query_text = '''DECLARE $id AS Utf8; DECLARE $at AS Uint64; DECLARE $kind AS Utf8; DECLARE $amount AS Uint64;
        UPSERT INTO demo_sales (id, purchased_at, membership_type, amount_kopecks)
        VALUES ($id, $at, $kind, $amount);'''
    def operation(session):
        query = session.prepare(query_text)
        for row in rows:
            session.transaction(ydb.SerializableReadWrite()).execute(query, {
                '$id': row['id'], '$at': row['purchased_at'],
                '$kind': row['membership_type'], '$amount': row['amount_kopecks']}, commit_tx=True)
    pool.retry_operation_sync(operation)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--anchor', type=date.fromisoformat, required=True)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    rows = make_rows(args.anchor, args.seed)
    if not args.write:
        print(json.dumps({'count': len(rows), 'rows': rows}, ensure_ascii=False, indent=2))
        return
    import os
    import ydb
    with ydb.Driver(endpoint=os.environ['YDB_ENDPOINT'], database=os.environ['YDB_DATABASE'],
                    credentials=ydb.credentials_from_env_variables()) as driver:
        driver.wait(timeout=5, fail_fast=True)
        with ydb.SessionPool(driver, size=5) as pool:
            write_rows(rows, pool)
    print(f'Upserted {len(rows)} synthetic rows')


if __name__ == '__main__':
    main()
