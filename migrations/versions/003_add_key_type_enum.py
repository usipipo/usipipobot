"""
Add key_type enum to vpn_keys

Revision ID: 003_add_key_type_enum
Revises: 002_add_data_packages
Create Date: 2026-02-19 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '003_add_key_type_enum'
down_revision: Union[str, None] = '002_add_data_packages'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
