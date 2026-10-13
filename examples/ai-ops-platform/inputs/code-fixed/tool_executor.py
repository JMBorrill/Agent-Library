"""Assistant tool executor (synthetic MVP snippet, fixed version)."""
import os

GATEWAY_KEY = os.environ.get("SMS_GATEWAY_KEY", "")  # real key lives in the secret manager


def thread_customer(db, tenant_id, thread_id):
    return db.execute(
        "SELECT customer_id, phone FROM messages WHERE tenant_id = %s AND thread_id = %s LIMIT 1",
        (tenant_id, thread_id),
    ).fetchone()


def send_sms(gateway, approval, to_number, body):
    if approval is None or not approval.granted_by_owner:
        raise PermissionError("send_sms requires owner approval")
    return gateway.send(to=to_number, body=body, api_key=GATEWAY_KEY)
