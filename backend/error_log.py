"""Best-effort operational error logging without request or credential contents."""
from datetime import datetime, timezone
import uuid


def log_error(source, error, request_id=None):
    """Persist an error category; logging failure must not change the API response."""
    try:
        from index import get_pool
        import ydb

        def operation(session):
            query = session.prepare('''
                DECLARE $id AS Utf8; DECLARE $at AS Timestamp;
                DECLARE $source AS Utf8; DECLARE $message AS Utf8;
                DECLARE $type AS Utf8; DECLARE $request AS Utf8;
                UPSERT INTO error_logs (id, occurred_at, source, message, error_type, request_id)
                VALUES ($id, $at, $source, $message, $type, $request);
            ''')
            session.transaction(ydb.SerializableReadWrite()).execute(query, {
                '$id': str(uuid.uuid4()), '$at': datetime.now(timezone.utc),
                '$source': source, '$message': f'{source} failed',
                '$type': type(error).__name__, '$request': request_id or '',
            }, commit_tx=True)

        get_pool().retry_operation_sync(operation)
    except Exception:
        pass
