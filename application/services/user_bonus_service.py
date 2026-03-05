from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List

from domain.entities.data_package import DataPackage
from domain.entities.user import User


@dataclass
class BonusCalculation:
    """Representa un bono calculado."""

    percent: int
    description: str
    gb_amount: float = 0  # Para bonos de GB fijos


class UserBonusService:
    """
    Servicio para calcular bonos aplicables a compras de paquetes.

    Bonos soportados:
    - Welcome Bonus: +20% en primera compra
    - Loyalty Bonus: Acumulativo permanente (3ra, 5ta, 10ma compra)
    - Quick Renewal Bonus: +15% si renueva ≤7 días antes de vencer
    - Referral Bonus: +5 GB por referido que compró
    """

    # Thresholds para loyalty bonus (compra N -> bonus %)
    LOYALTY_THRESHOLDS = {
        3: 10,  # 3ra compra: +10%
        5: 15,  # 5ta compra: +15% adicional
        10: 25,  # 10ma compra: +25% adicional
    }

    WELCOME_BONUS_PERCENT = 20
    QUICK_RENEWAL_BONUS_PERCENT = 15
    QUICK_RENEWAL_DAYS = 7
    REFERRAL_BONUS_GB = 5
    REFERRED_BONUS_PERCENT = 10

    def calculate_welcome_bonus(self, user: User) -> BonusCalculation:
        """Calcula bono de bienvenida para primera compra."""
        if user.purchase_count == 0 and not user.welcome_bonus_used:
            return BonusCalculation(
                percent=self.WELCOME_BONUS_PERCENT,
                description=f"Bono de Bienvenida (+{self.WELCOME_BONUS_PERCENT}%)",
            )
        return BonusCalculation(percent=0, description="")

    def calculate_loyalty_bonus(self, user: User) -> BonusCalculation:
        """Calcula bono de fidelidad acumulado permanente."""
        if user.loyalty_bonus_percent > 0:
            return BonusCalculation(
                percent=user.loyalty_bonus_percent,
                description=f"Bono de Fidelidad (+{user.loyalty_bonus_percent}%)",
            )
        return BonusCalculation(percent=0, description="")

    def calculate_quick_renewal_bonus(
        self, user: User, active_packages: List[DataPackage]
    ) -> BonusCalculation:
        """
        Calcula bono por renovación rápida.
        Aplica si algún paquete activo vence en ≤7 días.
        """
        now = datetime.now(timezone.utc)
        renewal_threshold = now + timedelta(days=self.QUICK_RENEWAL_DAYS)

        for pkg in active_packages:
            expires_at = pkg.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            # Si hay un paquete que vence pronto
            if expires_at <= renewal_threshold and expires_at > now:
                return BonusCalculation(
                    percent=self.QUICK_RENEWAL_BONUS_PERCENT,
                    description=f"Recarga Rápida (+{self.QUICK_RENEWAL_BONUS_PERCENT}%)",
                )

        return BonusCalculation(percent=0, description="")

    def calculate_referral_bonus_gb(self, user: User) -> BonusCalculation:
        """Calcula bono de GB por referidos que han comprado."""
        if user.referred_users_with_purchase > 0:
            total_gb = user.referred_users_with_purchase * self.REFERRAL_BONUS_GB
            return BonusCalculation(
                percent=0,
                description=f"Bono Referidos (+{total_gb} GB)",
                gb_amount=total_gb,
            )
        return BonusCalculation(percent=0, description="")

    def calculate_total_bonus(
        self,
        user: User,
        active_packages: List[DataPackage],
        is_referred_user_first_purchase: bool = False,
    ) -> tuple[int, List[BonusCalculation]]:
        """
        Calcula el bonus total acumulado y retorna desglose.

        Returns:
            Tuple de (bonus_percent_total, lista_de_bonos_aplicados)
        """
        bonuses = []
        total_percent = 0

        # Welcome bonus
        welcome = self.calculate_welcome_bonus(user)
        if welcome.percent > 0:
            bonuses.append(welcome)
            total_percent += welcome.percent

        # Loyalty bonus
        loyalty = self.calculate_loyalty_bonus(user)
        if loyalty.percent > 0:
            bonuses.append(loyalty)
            total_percent += loyalty.percent

        # Quick renewal bonus
        renewal = self.calculate_quick_renewal_bonus(user, active_packages)
        if renewal.percent > 0:
            bonuses.append(renewal)
            total_percent += renewal.percent

        # Referred user first purchase bonus
        if is_referred_user_first_purchase:
            bonuses.append(
                BonusCalculation(
                    percent=self.REFERRED_BONUS_PERCENT,
                    description=f"Bono Referido Primera Compra (+{self.REFERRED_BONUS_PERCENT}%)",
                )
            )
            total_percent += self.REFERRED_BONUS_PERCENT

        return total_percent, bonuses

    def get_loyalty_bonus_for_purchase_count(self, count: int) -> int:
        """Determina el loyalty bonus a aplicar basado en número de compra."""
        total_bonus = 0
        for threshold, bonus in sorted(self.LOYALTY_THRESHOLDS.items()):
            if count >= threshold:
                total_bonus += bonus
        return total_bonus
