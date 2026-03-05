import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as SQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from infrastructure.persistence.postgresql.models.base import Base

if TYPE_CHECKING:
    from infrastructure.persistence.postgresql.models.base import UserModel
    from infrastructure.persistence.postgresql.models.ticket_message import (
        TicketMessageModel,
    )


class TicketModel(Base):
    """Modelo SQLAlchemy para tickets."""

    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    priority: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(
        String(15), nullable=False, server_default="open"
    )
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_by: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="SET NULL"), nullable=True
    )
    admin_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["UserModel"] = relationship(
        back_populates="tickets", foreign_keys="TicketModel.user_id"
    )
    messages: Mapped[list["TicketMessageModel"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketMessageModel.created_at.asc()",
    )
