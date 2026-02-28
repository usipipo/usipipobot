import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from domain.entities.data_package import DataPackage, PackageType
from domain.interfaces.idata_package_repository import IDataPackageRepository
from domain.interfaces.iuser_repository import IUserRepository
from utils.logger import logger

from .user_bonus_service import UserBonusService


@dataclass
class PackageOption:
    name: str
    package_type: PackageType
    data_gb: int
    stars: int
    bonus_percent: int = 0
    duration_days: int = 35


@dataclass
class SlotOption:
    name: str
    slots: int
    stars: int


PACKAGE_OPTIONS: List[PackageOption] = [
    PackageOption(
        name="Básico",
        package_type=PackageType.BASIC,
        data_gb=10,
        stars=600,
        bonus_percent=0,
    ),
    PackageOption(
        name="Estándar",
        package_type=PackageType.ESTANDAR,
        data_gb=30,
        stars=960,
        bonus_percent=10,  # +3 GB gratis
    ),
    PackageOption(
        name="Avanzado",
        package_type=PackageType.AVANZADO,
        data_gb=60,
        stars=1320,
        bonus_percent=15,  # +9 GB gratis
    ),
    PackageOption(
        name="Premium",
        package_type=PackageType.PREMIUM,
        data_gb=120,
        stars=1800,
        bonus_percent=20,  # +24 GB gratis
    ),
    PackageOption(
        name="Ilimitado",
        package_type=PackageType.UNLIMITED,
        data_gb=200,
        stars=2400,
        bonus_percent=25,  # +50 GB gratis
    ),
]

SLOT_OPTIONS: List[SlotOption] = [
    SlotOption(name="+1 Clave", slots=1, stars=300),
    SlotOption(name="+3 Claves", slots=3, stars=700),
    SlotOption(name="+5 Claves", slots=5, stars=1000),
]


class DataPackageService:
    def __init__(
        self,
        package_repo: IDataPackageRepository,
        user_repo: IUserRepository,
        bonus_service: Optional[UserBonusService] = None
    ):
        self.package_repo = package_repo
        self.user_repo = user_repo
        self.bonus_service = bonus_service or UserBonusService()

    def get_available_packages(self) -> List[PackageOption]:
        return PACKAGE_OPTIONS.copy()

    def get_available_slots(self) -> List[SlotOption]:
        return SLOT_OPTIONS.copy()

    def _get_package_option(self, package_type: str) -> Optional[PackageOption]:
        try:
            pkg_type = PackageType(package_type.lower())
            for option in PACKAGE_OPTIONS:
                if option.package_type == pkg_type:
                    return option
            return None
        except ValueError:
            return None

    def _get_slot_option(self, slots: int) -> Optional[SlotOption]:
        for option in SLOT_OPTIONS:
            if option.slots == slots:
                return option
        return None

    async def purchase_package(
        self,
        user_id: int,
        package_type: str,
        telegram_payment_id: str,
        current_user_id: int,
        is_referred_first_purchase: bool = False
    ) -> Tuple[DataPackage, Dict[str, Any]]:
        """
        Compra un paquete aplicando todos los bonos correspondientes.

        Returns:
            Tuple de (DataPackage comprado, dict con desglose de bonos)
        """
        logger.info(
            f"📦 Iniciando compra de paquete - user_id={user_id}, "
            f"package_type={package_type}, payment_id={telegram_payment_id}"
        )

        try:
            option = self._get_package_option(package_type)
            if not option:
                raise ValueError(f"Tipo de paquete inválido: {package_type}")

            user = await self.user_repo.get_by_id(user_id, current_user_id)
            if not user:
                raise ValueError(f"Usuario no encontrado: {user_id}")

            # Get active packages for quick renewal bonus calculation
            active_packages = await self.package_repo.get_valid_by_user(user_id, current_user_id)

            # Calculate bonuses
            total_bonus_percent, bonuses = self.bonus_service.calculate_total_bonus(
                user, active_packages, is_referred_first_purchase
            )

            # Calculate data with bonuses
            data_limit_bytes = option.data_gb * (1024**3)

            # Package base bonus + user bonuses
            total_multiplier = 1 + (option.bonus_percent + total_bonus_percent) / 100
            actual_data_bytes = int(data_limit_bytes * total_multiplier)

            expires_at = datetime.now(timezone.utc) + timedelta(days=option.duration_days)

            new_package = DataPackage(
                user_id=user_id,
                package_type=option.package_type,
                data_limit_bytes=actual_data_bytes,
                stars_paid=option.stars,
                expires_at=expires_at,
                telegram_payment_id=telegram_payment_id,
            )

            saved_package = await self.package_repo.save(new_package, current_user_id)

            # Update user stats
            user.purchase_count += 1

            # Mark welcome bonus as used if this was first purchase
            if user.purchase_count == 1:
                user.welcome_bonus_used = True

            # Update loyalty bonus based on new purchase count
            new_loyalty = self.bonus_service.get_loyalty_bonus_for_purchase_count(user.purchase_count)
            if new_loyalty > user.loyalty_bonus_percent:
                user.loyalty_bonus_percent = new_loyalty

            await self.user_repo.save(user, current_user_id)

            # Prepare bonus breakdown
            bonus_breakdown = {
                "base_package_bonus": option.bonus_percent,
                "user_bonuses": bonuses,
                "total_bonus_percent": option.bonus_percent + total_bonus_percent,
                "base_gb": option.data_gb,
                "final_gb": actual_data_bytes / (1024**3)
            }

            logger.info(
                f"✅ Paquete comprado exitosamente - user_id={user_id}, "
                f"package_type={option.name}, data_gb={bonus_breakdown['final_gb']:.2f}, "
                f"stars={option.stars}, total_bonus={bonus_breakdown['total_bonus_percent']}%, "
                f"expires_at={expires_at.isoformat()}"
            )

            return saved_package, bonus_breakdown
        except Exception as e:
            logger.error(
                f"❌ Error en compra de paquete - user_id={user_id}, "
                f"package_type={package_type}, error={e}"
            )
            raise

    async def purchase_key_slots(
        self,
        user_id: int,
        slots: int,
        telegram_payment_id: str,
        current_user_id: int,
    ) -> Dict[str, Any]:
        logger.info(
            f"🔑 Iniciando compra de slots - user_id={user_id}, "
            f"slots={slots}, payment_id={telegram_payment_id}"
        )

        option = self._get_slot_option(slots)
        if not option:
            raise ValueError(f"Cantidad de slots invalida: {slots}")

        user = await self.user_repo.get_by_id(user_id, current_user_id)
        if not user:
            raise ValueError(f"Usuario no encontrado: {user_id}")

        success = await self.user_repo.increment_max_keys(
            user_id, slots, current_user_id
        )

        if not success:
            raise ValueError(f"Error al incrementar slots para usuario {user_id}")

        result = {
            "slots_added": slots,
            "new_max_keys": user.max_keys + slots,
            "stars_paid": option.stars,
        }

        logger.info(
            f"✅ Slots comprados exitosamente - user_id={user_id}, "
            f"slots_added={slots}, new_max_keys={result['new_max_keys']}, "
            f"stars_paid={option.stars}"
        )

        return result

    async def get_user_packages(
        self, user_id: int, current_user_id: int
    ) -> List[DataPackage]:
        return await self.package_repo.get_by_user(user_id, current_user_id)

    async def get_user_active_packages(
        self, user_id: int, current_user_id: int
    ) -> List[DataPackage]:
        return await self.package_repo.get_active_by_user(user_id, current_user_id)

    async def get_user_valid_packages(
        self, user_id: int, current_user_id: int
    ) -> List[DataPackage]:
        return await self.package_repo.get_valid_by_user(user_id, current_user_id)

    async def get_user_data_summary(
        self, user_id: int, current_user_id: int
    ) -> Dict[str, Any]:
        logger.debug(f"📊 Obteniendo resumen de datos - user_id={user_id}")
        packages = await self.package_repo.get_valid_by_user(user_id, current_user_id)
        user = await self.user_repo.get_by_id(user_id, current_user_id)

        now = datetime.now(timezone.utc)
        packages_detail = []

        for pkg in packages:
            expires_at = pkg.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            days_remaining = max(0, (expires_at - now).days)
            hours_remaining = max(0, ((expires_at - now).seconds // 3600))

            option = self._get_package_option(pkg.package_type.value)
            package_name = option.name if option else pkg.package_type.value.title()

            packages_detail.append(
                {
                    "name": package_name,
                    "total_gb": pkg.data_limit_bytes / (1024**3),
                    "used_gb": pkg.data_used_bytes / (1024**3),
                    "remaining_gb": pkg.remaining_bytes / (1024**3),
                    "days_remaining": days_remaining,
                    "hours_remaining": hours_remaining,
                    "expires_at": expires_at,
                }
            )

        total_limit_bytes = sum(p.data_limit_bytes for p in packages)
        total_used_bytes = sum(p.data_used_bytes for p in packages)

        free_plan = {"limit_gb": 0.0, "used_gb": 0.0, "remaining_gb": 0.0}

        if user:
            free_plan = {
                "limit_gb": user.free_data_limit_bytes / (1024**3),
                "used_gb": user.free_data_used_bytes / (1024**3),
                "remaining_gb": user.free_data_remaining_bytes / (1024**3),
            }

        total_remaining = max(0, total_limit_bytes - total_used_bytes) + (
            user.free_data_remaining_bytes if user else 0
        )

        return {
            "active_packages": len(packages),
            "packages": packages_detail,
            "free_plan": free_plan,
            "total_limit_gb": total_limit_bytes / (1024**3),
            "total_used_gb": total_used_bytes / (1024**3),
            "remaining_gb": total_remaining / (1024**3),
        }

    async def consume_data(
        self, user_id: int, bytes_used: int, current_user_id: int
    ) -> bool:
        packages = await self.package_repo.get_valid_by_user(user_id, current_user_id)

        if not packages:
            logger.warning(
                f"Sin paquetes válidos para consumir datos del usuario {user_id}"
            )
            return False

        remaining_to_consume = bytes_used
        for package in packages:
            if remaining_to_consume <= 0:
                break
            if package.id is None:
                continue

            available = package.remaining_bytes
            if available > 0:
                to_use = min(remaining_to_consume, available)
                await self.package_repo.update_usage(
                    package.id, to_use, current_user_id
                )
                remaining_to_consume -= to_use

        if remaining_to_consume > 0:
            logger.warning(
                f"Usuario {user_id} sin datos suficientes. Faltaron {remaining_to_consume} bytes"
            )

        return True

    async def expire_old_packages(self, admin_user_id: int) -> int:
        try:
            expired_packages = await self.package_repo.get_expired_packages(
                admin_user_id
            )

            count = 0
            for pkg in expired_packages:
                if pkg.id is None:
                    continue

                logger.warning(
                    f"⚠️ Paquete expirado - package_id={pkg.id}, "
                    f"user_id={pkg.user_id}, package_type={pkg.package_type.value}, "
                    f"expired_at={pkg.expires_at.isoformat()}"
                )

                success = await self.package_repo.deactivate(pkg.id, admin_user_id)
                if success:
                    count += 1

            logger.info(f"📦 {count} paquetes expirados desactivados")
            return count
        except Exception as e:
            logger.error(f"Error al expirar paquetes: {e}")
            return 0

    async def get_package_by_id(
        self, package_id: uuid.UUID, current_user_id: int
    ) -> Optional[DataPackage]:
        return await self.package_repo.get_by_id(package_id, current_user_id)
