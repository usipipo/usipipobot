import pytest
from dataclasses import asdict
from datetime import datetime, timezone
from uuid import UUID, uuid4

from domain.entities.ticket import (
    Ticket, TicketCategory, TicketPriority, TicketStatus
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


class TestTicketEntity:
    def test_ticket_creation(self):
        ticket = Ticket(
            user_id=123456,
            category=TicketCategory.VPN_FAIL,
            priority=TicketPriority.HIGH,
            status=TicketStatus.OPEN,
            subject="VPN no conecta"
        )

        assert ticket.user_id == 123456
        assert ticket.category == TicketCategory.VPN_FAIL
        assert ticket.priority == TicketPriority.HIGH
        assert ticket.status == TicketStatus.OPEN
        assert ticket.subject == "VPN no conecta"
        assert isinstance(ticket.id, UUID)
        assert ticket.created_at is not None
        assert ticket.updated_at is not None

    def test_ticket_default_status(self):
        ticket = Ticket(
            user_id=123456,
            category=TicketCategory.PAYMENT,
            priority=TicketPriority.MEDIUM,
            subject="Problema con pago"
        )
        assert ticket.status == TicketStatus.OPEN

    def test_ticket_status_transitions(self):
        ticket = Ticket(
            user_id=123456,
            category=TicketCategory.ACCOUNT,
            priority=TicketPriority.LOW,
            status=TicketStatus.OPEN,
            subject="Cambiar nombre"
        )

        # Can transition to responded
        ticket.status = TicketStatus.RESPONDED
        assert ticket.status == TicketStatus.RESPONDED

        # Can transition to resolved
        ticket.status = TicketStatus.RESOLVED
        ticket.resolved_at = datetime.now(timezone.utc)
        ticket.resolved_by = 999999
        assert ticket.status == TicketStatus.RESOLVED

    def test_ticket_ticket_number_format(self):
        ticket = Ticket(
            user_id=123456,
            category=TicketCategory.OTHER,
            priority=TicketPriority.LOW,
            subject="Consulta"
        )

        ticket_number = f"T-{str(ticket.id)[:8].upper()}"
        assert ticket_number.startswith("T-")
        assert len(ticket_number) == 10  # T- + 8 chars
