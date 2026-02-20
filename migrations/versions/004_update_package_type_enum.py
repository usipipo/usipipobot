"""
Update package_type_enum with ESTANDAR and AVANZADO

Revision ID: 004_update_package_type_enum
Revises: 003_add_key_type_enum
Create Date: 2026-02-20 08:10:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = '004_update_package_type_enum'
down_revision: Union[str, None] = '003_add_key_type_enum'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE package_type_enum ADD VALUE IF NOT EXISTS 'estandar'")
    op.execute("ALTER TYPE package_type_enum ADD VALUE IF NOT EXISTS 'avanzado'")


def downgrade() -> None:
    pass
