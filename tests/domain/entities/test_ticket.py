import pytest
from datetime import datetime, timezone
from uuid import uuid4

from domain.entities.ticket import (
    TicketCategory, TicketPriority, TicketStatus
)


class TestTicketEnums:
    def test_ticket_category_values(self):
        assert TicketCategory.VPN_FAIL == "vpn_fail"
        assert TicketCategory.PAYMENT == "payment"
        assert TicketCategory.ACCOUNT == "account"
        assert TicketCategory.OTHER == "other"

    def test_ticket_priority_values(self):
        assert TicketPriority.HIGH == "high"
        assert TicketPriority.MEDIUM == "medium"
        assert TicketPriority.LOW == "low"

    def test_ticket_status_values(self):
        assert TicketStatus.OPEN == "open"
        assert TicketStatus.RESPONDED == "responded"
        assert TicketStatus.RESOLVED == "resolved"
        assert TicketStatus.CLOSED == "closed"
