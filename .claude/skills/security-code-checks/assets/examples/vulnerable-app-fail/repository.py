"""Appointment repository (synthetic, deliberately vulnerable)."""

UPCOMING = """
    SELECT id, contact_id, starts_at
    FROM appointments
    WHERE starts_at > now()
    ORDER BY starts_at
"""


def upcoming(db):
    return db.execute(UPCOMING).fetchall()
