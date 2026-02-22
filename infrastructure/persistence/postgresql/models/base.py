"""
Modelos SQLAlchemy unificados para PostgreSQL auto-alojado.

Todos los modelos comparten la misma Base declarativa para
asegurar integridad referencial y relaciones correctas.

Author: uSipipo Team
Version: 3.0.0
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import BigInteger, Boolean, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Clase base única para todos los modelos de SQLAlchemy."""

    pass


class UserModel(Base):
    """Modelo de usuarios del sistema."""

    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    language_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    status: Mapped[Optional[str]] = mapped_column(String, server_default="active")
    role: Mapped[Optional[str]] = mapped_column(String, server_default="user")
    max_keys: Mapped[int] = mapped_column(Integer, server_default="2")
    
    balance_stars: Mapped[int] = mapped_column(Integer, server_default="0")
    total_deposited: Mapped[int] = mapped_column(Integer, server_default="0")
    
    referral_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    referred_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    total_referral_earnings: Mapped[int] = mapped_column(Integer, server_default="0")
    
    is_vip: Mapped[bool] = mapped_column(Boolean, server_default="false")
    vip_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    free_data_limit_bytes: Mapped[int] = mapped_column(
        BigInteger, server_default="10737418240"
    )
    free_data_used_bytes: Mapped[int] = mapped_column(BigInteger, server_default="0")

    keys: Mapped[List["VpnKeyModel"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    data_packages: Mapped[List["DataPackageModel"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class VpnKeyModel(Base):
    """Modelo de llaves VPN."""

    __tablename__ = "vpn_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE")
    )
    key_type: Mapped[str] = mapped_column(
        SQLEnum("wireguard", "outline", name="key_type_enum"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    key_data: Mapped[str] = mapped_column(String, nullable=False)
    external_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    used_bytes: Mapped[int] = mapped_column(BigInteger, server_default="0")
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    data_limit_bytes: Mapped[int] = mapped_column(
        BigInteger, server_default="10737418240"
    )
    billing_reset_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    owner: Mapped["UserModel"] = relationship(back_populates="keys")


class DataPackageModel(Base):
    """Modelo de paquetes de datos comprados."""

    __tablename__ = "data_packages"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE")
    )
    package_type: Mapped[str] = mapped_column(
        SQLEnum(
            "basic",
            "estandar",
            "avanzado",
            "premium",
            "unlimited",
            name="package_type_enum",
        ),
        nullable=False,
    )
    data_limit_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    data_used_bytes: Mapped[int] = mapped_column(BigInteger, server_default="0")
    stars_paid: Mapped[int] = mapped_column(Integer, nullable=False)
    purchased_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    telegram_payment_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    user: Mapped["UserModel"] = relationship(back_populates="data_packages")


class TransactionModel(Base):
    """Modelo de transacciones de estrellas."""

    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE")
    )
    transaction_type: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    reference_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    telegram_payment_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
