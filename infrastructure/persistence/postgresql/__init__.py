"""
Modulo de persistencia PostgreSQL auto-alojado.

Este modulo reemplaza completamente la integracion con Supabase,
usando SQLAlchemy 2.0 async con PostgreSQL puro.

Author: uSipipo Team
Version: 2.1.0
"""

from .base_repository import BasePostgresRepository
from .user_repository import PostgresUserRepository
from .key_repository import PostgresKeyRepository
from .ticket_repository import PostgresTicketRepository
from .transaction_repository import PostgresTransactionRepository
from .achievement_repository import PostgresAchievementRepository, PostgresUserStatsRepository
from .conversation_repository import PostgresConversationRepository
from .task_repository import PostgresTaskRepository
from .models import (
    Base,
    UserModel,
    VpnKeyModel,
    TicketModel,
    TransactionModel,
    AchievementModel,
    UserStatsModel,
    UserAchievementModel,
    TaskModel,
    UserTaskModel,
    ConversationModel,
)

__all__ = [
    "BasePostgresRepository",
    "PostgresUserRepository",
    "PostgresKeyRepository",
    "PostgresTicketRepository",
    "PostgresTransactionRepository",
    "PostgresAchievementRepository",
    "PostgresUserStatsRepository",
    "PostgresConversationRepository",
    "PostgresTaskRepository",
    "Base",
    "UserModel",
    "VpnKeyModel",
    "TicketModel",
    "TransactionModel",
    "AchievementModel",
    "UserStatsModel",
    "UserAchievementModel",
    "TaskModel",
    "UserTaskModel",
    "ConversationModel",
]
