"""
Audit log service: records all agent tool calls for transparency and debugging.
Never stores sensitive payment credentials.
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from app.models import AuditLog


# Fields to redact from audit logs
SENSITIVE_KEYS = {"razorpay_key_secret", "api_key", "password", "token", "secret"}


def _sanitize(data: Any) -> Any:
    """Remove sensitive fields from data before logging."""
    if isinstance(data, dict):
        return {
            k: "***REDACTED***" if k.lower() in SENSITIVE_KEYS else _sanitize(v)
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [_sanitize(item) for item in data]
    return data


def log_action(
    db: Session,
    tool_name: str,
    input_summary: str,
    result_status: str,
    session_id: Optional[str] = None,
    order_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """Write an audit log entry. Automatically sanitizes sensitive data."""
    sanitized_details = _sanitize(details) if details else None

    entry = AuditLog(
        timestamp=datetime.now(timezone.utc),
        session_id=session_id,
        tool_name=tool_name,
        input_summary=input_summary[:500],  # cap length
        result_status=result_status,
        order_id=order_id,
        details=sanitized_details,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_audit_logs(
    db: Session,
    session_id: Optional[str] = None,
    tool_name: Optional[str] = None,
    limit: int = 100,
) -> List[AuditLog]:
    """Retrieve audit logs with optional filters."""
    query = db.query(AuditLog)

    if session_id:
        query = query.filter(AuditLog.session_id == session_id)
    if tool_name:
        query = query.filter(AuditLog.tool_name == tool_name)

    return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
