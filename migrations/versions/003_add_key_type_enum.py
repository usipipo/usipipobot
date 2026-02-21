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
    op.execute("CREATE TYPE key_type_enum AS ENUM ('wireguard', 'outline')")

    op.execute("UPDATE vpn_keys SET key_type = 'outline' WHERE key_type NOT IN ('wireguard', 'outline') OR key_type IS NULL")

    op.alter_column(
        'vpn_keys',
        'key_type',
        existing_type=sa.String(),
        type_=sa.Enum('wireguard', 'outline', name='key_type_enum'),
        postgresql_using='key_type::key_type_enum',
        nullable=False
    )


def downgrade() -> None:
    op.alter_column(
        'vpn_keys',
        'key_type',
        existing_type=sa.Enum('wireguard', 'outline', name='key_type_enum'),
        type_=sa.String(),
        postgresql_using='key_type::text',
        nullable=True
    )

    op.execute('DROP TYPE key_type_enum')
