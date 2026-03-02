import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as SQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from infrastructure.persistence.postgresql.models.base import Base


class TicketMessageModel(Base):
    """Modelo SQLAlchemy para mensajes de tickets."""
    
    __tablename__ = "ticket_messages"
    
    id: Mapped[uuid.UUID] = mapped_column(
        SQLUUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        SQLUUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False
    )
    from_user_id: Mapped[int] = mapped_column(
        BigInteger, 
        nullable=False
    )
    message: Mapped[str] = mapped_column(
        Text, 
        nullable=False
    )
    is_from_admin: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    
    # Relationships
    ticket: Mapped["TicketModel"] = relationship(back_populates="messages")
