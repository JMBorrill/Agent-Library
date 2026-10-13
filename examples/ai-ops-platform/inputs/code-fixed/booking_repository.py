"""Booking repository for the AI scheduling assistant (synthetic MVP snippet, fixed version)."""


def free_slots(db, tenant_id, day):
    return db.execute(
        "SELECT starts_at FROM bookings WHERE tenant_id = %s AND day = %s AND status = 'free'",
        (tenant_id, day),
    ).fetchall()


def get_booking_for_reschedule(db, tenant_id, booking_id):
    # Tenant comes from the authenticated session (threat AIOPS-TM-T01/T02), never from the message.
    return db.execute(
        "SELECT id, customer_id, starts_at FROM bookings WHERE tenant_id = %s AND id = %s",
        (tenant_id, booking_id),
    ).fetchone()


def create_booking(db, tenant_id, customer_id, starts_at):
    return db.execute(
        "INSERT INTO bookings (tenant_id, customer_id, starts_at) VALUES (%s, %s, %s)",
        (tenant_id, customer_id, starts_at),
    )
