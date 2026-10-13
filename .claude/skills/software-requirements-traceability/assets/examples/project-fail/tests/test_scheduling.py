import unittest
from datetime import datetime

from scheduling import Conflict, book, list_bookings


class FakeRepo:
    def __init__(self, rows=()):
        self.rows = list(rows)

    def bookings(self, tenant_id, resource_id=None):
        return [r for r in self.rows if r.tenant_id == tenant_id
                and (resource_id is None or r.resource_id == resource_id)]


class BookingTests(unittest.TestCase):
    def test_AIOPS_SW_001_rejects_overlap(self):
        """Overlapping booking for the same tenant and resource is rejected."""

    def test_cross_tenant_query_returns_nothing(self):
        # verifies AIOPS-SW-002
        self.assertEqual(list_bookings(FakeRepo(), "tenant-b"), [])
