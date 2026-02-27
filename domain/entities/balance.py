"""
Entidad Balance para el sistema de pagos.

Author: uSipipo Team
Version: 1.0.0
"""

from dataclasses import dataclass


@dataclass
class Balance:
    """
    Representa el saldo de un usuario en el sistema.
    
    El saldo se mide en 'stars' (unidades de pago de Telegram).
    """

    user_id: int
    stars: int = 0

    def __post_init__(self):
        """Asegura que stars sea siempre un entero no negativo."""
        if self.stars < 0:
            self.stars = 0

    def add(self, amount: int) -> "Balance":
        """Agrega una cantidad al saldo y retorna un nuevo Balance."""
        return Balance(user_id=self.user_id, stars=self.stars + amount)

    def subtract(self, amount: int) -> "Balance":
        """Resta una cantidad del saldo y retorna un nuevo Balance."""
        new_balance = self.stars - amount
        return Balance(user_id=self.user_id, stars=max(0, new_balance))

    def has_sufficient(self, amount: int) -> bool:
        """Verifica si hay saldo suficiente para una operación."""
        return self.stars >= amount

    def __repr__(self) -> str:
        return f"<Balance(user_id={self.user_id}, stars={self.stars})>"
