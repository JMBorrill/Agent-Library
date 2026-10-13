"""Booking service for the AI Operations Platform (synthetic example)."""


class Conflict(Exception):
    pass


def book(repo, tenant_id, resource_id, start, end):
    """Create a booking.

    Implements AIOPS-SW-001: reject overlaps for the same tenant and resource.
    """
    for existing in repo.bookings(tenant_id=tenant_id, resource_id=resource_id):
        if existing.start < end and start < existing.end:
            raise Conflict("slot taken")
    return repo.insert(tenant_id=tenant_id, resource_id=resource_id, start=start, end=end)


def list_bookings(repo, tenant_id):
    # @req AIOPS-SW-002 every query is scoped by tenant_id
    return repo.bookings(tenant_id=tenant_id)
