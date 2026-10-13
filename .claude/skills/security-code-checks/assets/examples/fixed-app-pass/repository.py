"""Appointment repository (synthetic, fixed version)."""

UPCOMING = """
    SELECT id, contact_id, starts_at
    FROM appointments
    WHERE tenant_id = %(tenant_id)s AND starts_at > now()
    ORDER BY starts_at
"""


def upcoming(db, tenant_id):
    return db.execute(UPCOMING, {"tenant_id": tenant_id}).fetchall()
