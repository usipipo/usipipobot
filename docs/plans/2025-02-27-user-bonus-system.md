# Sistema de Bonos Acumulativos - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implementar un sistema completo de bonos acumulativos (bienvenida, fidelidad, referidos, recarga rápida) que se aplican automáticamente en cada compra de paquete de datos.

**Architecture:** Extender la entidad `User` con campos de tracking (`purchase_count`, `loyalty_bonus_percent`, `welcome_bonus_used`), crear un `UserBonusService` para calcular bonos aplicables, y modificar `DataPackageService.purchase_package()` para aplicar el bonus total acumulado a cada compra.

**Tech Stack:** Python 3.13, SQLAlchemy, Alembic (migraciones), pytest

---

## Pre-Implementation

### Task 0: Crear rama de feature desde develop

```bash
git checkout develop
git pull origin develop
git checkout -b feature/user-bonus-system-220
```

---

## Phase 1: Modelos de Datos

### Task 1: Agregar campos a User entity

**Files:**
- Modify: `domain/entities/user.py`
- Test: `tests/domain/entities/test_user.py`

**Step 1: Write the failing test**

```python
def test_user_has_bonus_tracking_fields():
    from domain.entities.user import User
    
    user = User(telegram_id=12345)
    
    # Default values
    assert user.purchase_count == 0
    assert user.loyalty_bonus_percent == 0
    assert user.welcome_bonus_used == False
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/domain/entities/test_user.py::test_user_has_bonus_tracking_fields -v
```
Expected: FAIL with "AttributeError: 'User' object has no attribute 'purchase_count'"

**Step 3: Write minimal implementation**

Add to `domain/entities/user.py` after `free_data_used_bytes`:

```python
    # Bonus tracking fields
    purchase_count: int = 0
    loyalty_bonus_percent: int = 0
    welcome_bonus_used: bool = False
    referred_users_with_purchase: int = 0  # Track referrals who bought
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/domain/entities/test_user.py::test_user_has_bonus_tracking_fields -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add domain/entities/user.py tests/domain/entities/test_user.py
git commit -m "feat(user): add bonus tracking fields (purchase_count, loyalty_bonus, welcome_bonus)"
```

---

### Task 2: Agregar campos a UserModel SQLAlchemy

**Files:**
- Modify: `infrastructure/persistence/postgresql/models/base.py`
- Modify: `infrastructure/persistence/postgresql/user_repository.py` (to_entity/from_entity)
- Test: `tests/infrastructure/persistence/test_user_repository.py`

**Step 1: Write the failing test**

```python
@pytest.mark.asyncio
async def test_user_repository_saves_bonus_fields(db_session):
    from infrastructure.persistence.postgresql.models.base import UserModel
    from infrastructure.persistence.postgresql.user_repository import PostgresUserRepository
    
    repo = PostgresUserRepository(db_session)
    user = User(
        telegram_id=999999,
        purchase_count=5,
        loyalty_bonus_percent=25,
        welcome_bonus_used=True,
        referred_users_with_purchase=3
    )
    
    saved = await repo.save(user, current_user_id=999999)
    retrieved = await repo.get_by_id(999999, current_user_id=999999)
    
    assert retrieved.purchase_count == 5
    assert retrieved.loyalty_bonus_percent == 25
    assert retrieved.welcome_bonus_used == True
    assert retrieved.referred_users_with_purchase == 3
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/infrastructure/persistence/test_user_repository.py::test_user_repository_saves_bonus_fields -v
```
Expected: FAIL - SQL columns don't exist

**Step 3: Add columns to UserModel**

In `infrastructure/persistence/postgresql/models/base.py`, after `free_data_used_bytes`:

```python
    # Bonus tracking fields
    purchase_count: Mapped[int] = mapped_column(Integer, server_default="0")
    loyalty_bonus_percent: Mapped[int] = mapped_column(Integer, server_default="0")
    welcome_bonus_used: Mapped[bool] = mapped_column(Boolean, server_default="false")
    referred_users_with_purchase: Mapped[int] = mapped_column(Integer, server_default="0")
```

**Step 4: Update UserRepository from_entity/to_entity**

In `infrastructure/persistence/postgresql/user_repository.py`, update `from_entity` method to include:

```python
            purchase_count=entity.purchase_count,
            loyalty_bonus_percent=entity.loyalty_bonus_percent,
            welcome_bonus_used=entity.welcome_bonus_used,
            referred_users_with_purchase=entity.referred_users_with_purchase,
```

And in `to_entity` method:

```python
            purchase_count=model.purchase_count,
            loyalty_bonus_percent=model.loyalty_bonus_percent,
            welcome_bonus_used=model.welcome_bonus_used,
            referred_users_with_purchase=model.referred_users_with_purchase,
```

**Step 5: Create Alembic migration**

```bash
alembic revision --autogenerate -m "Add user bonus tracking fields"
alembic upgrade head
```

**Step 6: Run test to verify it passes**

```bash
pytest tests/infrastructure/persistence/test_user_repository.py::test_user_repository_saves_bonus_fields -v
```
Expected: PASS

**Step 7: Commit**

```bash
git add infrastructure/persistence/postgresql/models/base.py infrastructure/persistence/postgresql/user_repository.py tests/infrastructure/persistence/test_user_repository.py
git add alembic/versions/
git commit -m "feat(database): add bonus tracking columns to users table"
```

---

## Phase 2: Servicio de Bonos

### Task 3: Crear UserBonusService

**Files:**
- Create: `application/services/user_bonus_service.py`
- Test: `tests/application/services/test_user_bonus_service.py`

**Step 1: Write the failing test**

```python
import pytest
from domain.entities.user import User
from application.services.user_bonus_service import UserBonusService, BonusCalculation


class TestCalculateWelcomeBonus:
    def test_first_purchase_gets_welcome_bonus(self):
        user = User(telegram_id=123, purchase_count=0, welcome_bonus_used=False)
        service = UserBonusService()
        
        bonus = service.calculate_welcome_bonus(user)
        
        assert bonus.percent == 20
        assert bonus.description == "Bono de Bienvenida (+20%)"

    def test_second_purchase_no_welcome_bonus(self):
        user = User(telegram_id=123, purchase_count=1, welcome_bonus_used=True)
        service = UserBonusService()
        
        bonus = service.calculate_welcome_bonus(user)
        
        assert bonus.percent == 0
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/application/services/test_user_bonus_service.py::TestCalculateWelcomeBonus -v
```
Expected: FAIL - module doesn't exist

**Step 3: Create UserBonusService with welcome bonus**

```python
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timezone, timedelta

from domain.entities.user import User
from domain.entities.data_package import DataPackage


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
        3: 10,   # 3ra compra: +10%
        5: 15,   # 5ta compra: +15% adicional
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
                description=f"Bono de Bienvenida (+{self.WELCOME_BONUS_PERCENT}%)"
            )
        return BonusCalculation(percent=0, description="")
    
    def calculate_loyalty_bonus(self, user: User) -> BonusCalculation:
        """Calcula bono de fidelidad acumulado permanente."""
        if user.loyalty_bonus_percent > 0:
            return BonusCalculation(
                percent=user.loyalty_bonus_percent,
                description=f"Bono de Fidelidad (+{user.loyalty_bonus_percent}%)"
            )
        return BonusCalculation(percent=0, description="")
    
    def calculate_quick_renewal_bonus(
        self, 
        user: User, 
        active_packages: List[DataPackage]
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
                    description=f"Recarga Rápida (+{self.QUICK_RENEWAL_BONUS_PERCENT}%)"
                )
        
        return BonusCalculation(percent=0, description="")
    
    def calculate_referral_bonus_gb(self, user: User) -> BonusCalculation:
        """Calcula bono de GB por referidos que han comprado."""
        if user.referred_users_with_purchase > 0:
            total_gb = user.referred_users_with_purchase * self.REFERRAL_BONUS_GB
            return BonusCalculation(
                percent=0,
                description=f"Bono Referidos (+{total_gb} GB)",
                gb_amount=total_gb
            )
        return BonusCalculation(percent=0, description="")
    
    def calculate_total_bonus(
        self,
        user: User,
        active_packages: List[DataPackage],
        is_referred_user_first_purchase: bool = False
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
            bonuses.append(BonusCalculation(
                percent=self.REFERRED_BONUS_PERCENT,
                description=f"Bono Referido Primera Compra (+{self.REFERRED_BONUS_PERCENT}%)"
            ))
            total_percent += self.REFERRED_BONUS_PERCENT
        
        return total_percent, bonuses
    
    def get_loyalty_bonus_for_purchase_count(self, count: int) -> int:
        """Determina el loyalty bonus a aplicar basado en número de compra."""
        total_bonus = 0
        for threshold, bonus in sorted(self.LOYALTY_THRESHOLDS.items()):
            if count >= threshold:
                total_bonus += bonus
        return total_bonus
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/application/services/test_user_bonus_service.py::TestCalculateWelcomeBonus -v
```
Expected: PASS

**Step 5: Add tests for loyalty bonus**

```python
class TestCalculateLoyaltyBonus:
    def test_no_loyalty_bonus_for_new_user(self):
        user = User(telegram_id=123, purchase_count=0, loyalty_bonus_percent=0)
        service = UserBonusService()
        
        bonus = service.calculate_loyalty_bonus(user)
        
        assert bonus.percent == 0

    def test_loyalty_bonus_applies_when_set(self):
        user = User(telegram_id=123, purchase_count=5, loyalty_bonus_percent=25)
        service = UserBonusService()
        
        bonus = self.calculate_loyalty_bonus(user)
        
        assert bonus.percent == 25
        assert "Fidelidad" in bonus.description

    def test_get_loyalty_bonus_for_purchase_count(self):
        service = UserBonusService()
        
        assert service.get_loyalty_bonus_for_purchase_count(1) == 0
        assert service.get_loyalty_bonus_for_purchase_count(3) == 10
        assert service.get_loyalty_bonus_for_purchase_count(5) == 25  # 10+15
        assert service.get_loyalty_bonus_for_purchase_count(10) == 50  # 10+15+25
```

**Step 6: Run loyalty tests**

```bash
pytest tests/application/services/test_user_bonus_service.py::TestCalculateLoyaltyBonus -v
```
Expected: PASS

**Step 7: Add tests for quick renewal bonus**

```python
from datetime import datetime, timezone, timedelta
from domain.entities.data_package import DataPackage, PackageType


class TestCalculateQuickRenewalBonus:
    def test_quick_renewal_bonus_when_package_expires_soon(self):
        user = User(telegram_id=123)
        expires_soon = datetime.now(timezone.utc) + timedelta(days=3)
        active_packages = [
            DataPackage(
                user_id=123,
                package_type=PackageType.BASIC,
                data_limit_bytes=10*1024**3,
                stars_paid=600,
                expires_at=expires_soon
            )
        ]
        service = UserBonusService()
        
        bonus = service.calculate_quick_renewal_bonus(user, active_packages)
        
        assert bonus.percent == 15
        assert "Recarga Rápida" in bonus.description

    def test_no_quick_renewal_when_package_expires_later(self):
        user = User(telegram_id=123)
        expires_later = datetime.now(timezone.utc) + timedelta(days=15)
        active_packages = [
            DataPackage(
                user_id=123,
                package_type=PackageType.BASIC,
                data_limit_bytes=10*1024**3,
                stars_paid=600,
                expires_at=expires_later
            )
        ]
        service = UserBonusService()
        
        bonus = service.calculate_quick_renewal_bonus(user, active_packages)
        
        assert bonus.percent == 0
```

**Step 8: Run quick renewal tests**

```bash
pytest tests/application/services/test_user_bonus_service.py::TestCalculateQuickRenewalBonus -v
```
Expected: PASS

**Step 9: Add test for total bonus calculation**

```python
class TestCalculateTotalBonus:
    def test_total_bonus_accumulates(self):
        user = User(
            telegram_id=123,
            purchase_count=0,
            welcome_bonus_used=False,
            loyalty_bonus_percent=25
        )
        expires_soon = datetime.now(timezone.utc) + timedelta(days=3)
        active_packages = [
            DataPackage(
                user_id=123,
                package_type=PackageType.BASIC,
                data_limit_bytes=10*1024**3,
                stars_paid=600,
                expires_at=expires_soon
            )
        ]
        service = UserBonusService()
        
        total_percent, bonuses = service.calculate_total_bonus(user, active_packages)
        
        # Welcome (20%) + Loyalty (25%) + Quick Renewal (15%) = 60%
        assert total_percent == 60
        assert len(bonuses) == 3
```

**Step 10: Run total bonus tests**

```bash
pytest tests/application/services/test_user_bonus_service.py::TestCalculateTotalBonus -v
```
Expected: PASS

**Step 11: Commit**

```bash
git add application/services/user_bonus_service.py tests/application/services/test_user_bonus_service.py
git commit -m "feat(bonus): create UserBonusService with welcome, loyalty, and quick renewal bonuses"
```

---

## Phase 3: Integración con DataPackageService

### Task 4: Modificar DataPackageService para aplicar bonos

**Files:**
- Modify: `application/services/data_package_service.py`
- Test: `tests/application/services/test_data_package_service.py`

**Step 1: Add UserBonusService dependency and update purchase logic**

Modify `DataPackageService.__init__` to accept `UserBonusService`:

```python
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
```

**Step 2: Update purchase_package method**

```python
    async def purchase_package(
        self,
        user_id: int,
        package_type: str,
        telegram_payment_id: str,
        current_user_id: int,
        is_referred_first_purchase: bool = False
    ) -> tuple[DataPackage, dict]:
        """
        Compra un paquete aplicando todos los bonos correspondientes.
        
        Returns:
            Tuple de (DataPackage comprado, dict con desglose de bonos)
        """
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
            f"📦 Paquete {option.name} comprado para usuario {user_id} "
            f"con {total_bonus_percent}% bonus adicional"
        )
        
        return saved_package, bonus_breakdown
```

**Step 3: Update tests**

Add test for bonus calculation in purchase:

```python
@pytest.mark.asyncio
async def test_purchase_applies_welcome_bonus_for_first_purchase(
    self, service, mock_package_repo, mock_user_repo
):
    from domain.entities.user import User
    
    user = User(telegram_id=123, purchase_count=0, welcome_bonus_used=False)
    mock_user_repo.get_by_id.return_value = user
    mock_package_repo.get_valid_by_user.return_value = []
    mock_package_repo.save.return_value = DataPackage(
        user_id=123,
        package_type=PackageType.BASIC,
        data_limit_bytes=int(12 * 1024**3),  # 10GB + 20% welcome bonus
        stars_paid=600,
        expires_at=datetime.now(timezone.utc) + timedelta(days=35),
    )

    result, bonus_breakdown = await service.purchase_package(
        user_id=123,
        package_type="basic",
        telegram_payment_id="pay_123",
        current_user_id=123,
    )

    # 10GB base + 20% welcome = 12GB
    assert result.data_limit_bytes == int(12 * 1024**3)
    assert bonus_breakdown["total_bonus_percent"] == 20  # Just welcome bonus
    assert any("Bienvenida" in b.description for b in bonus_breakdown["user_bonuses"])
    
    # User should be updated
    assert user.purchase_count == 1
    assert user.welcome_bonus_used == True
```

**Step 4: Run tests**

```bash
pytest tests/application/services/test_data_package_service.py::TestPurchasePackage -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add application/services/data_package_service.py tests/application/services/test_data_package_service.py
git commit -m "feat(bonus): integrate UserBonusService into DataPackageService"
```

---

## Phase 4: Mejorar Sistema de Referidos

### Task 5: Actualizar ReferralService con nuevos bonos

**Files:**
- Modify: `application/services/referral_service.py`
- Test: `tests/application/services/test_referral_service.py`

**Step 1: Add method to track referred user purchase**

```python
    async def record_referred_user_purchase(
        self,
        referrer_id: int,
        referred_user_id: int,
        current_user_id: int
    ) -> Dict[str, Any]:
        """
        Registra que un usuario referido realizó una compra.
        Otorga +5GB al referidor.
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            referrer = await self.user_repo.get_by_id(referrer_id, current_user_id)
            if not referrer:
                return {"success": False, "error": "referrer_not_found"}

            # Incrementar contador de referidos con compra
            referrer.referred_users_with_purchase += 1
            await self.user_repo.save(referrer, current_user_id)

            # Nota: El +5GB se aplica automáticamente en la próxima compra
            # via UserBonusService.calculate_referral_bonus_gb()

            logger.info(
                f"👥 Referido {referred_user_id} realizó compra. "
                f"Referidor {referrer_id} tiene {referrer.referred_users_with_purchase} "
                f"referidos con compra (+{referrer.referred_users_with_purchase * 5}GB bono)"
            )

            return {
                "success": True,
                "referrer_id": referrer_id,
                "total_referral_bonus_gb": referrer.referred_users_with_purchase * 5
            }

        except Exception as e:
            logger.error(f"Error registrando compra de referido: {e}")
            return {"success": False, "error": str(e)}
```

**Step 2: Add test**

```python
@pytest.mark.asyncio
async def test_record_referred_user_purchase_increments_counter(
    self, service, mock_user_repo
):
    referrer = User(
        telegram_id=123,
        referral_code="ABC123",
        referred_users_with_purchase=2
    )
    mock_user_repo.get_by_id.return_value = referrer

    result = await service.record_referred_user_purchase(123, 456, 123)

    assert result["success"] == True
    assert result["total_referral_bonus_gb"] == 15  # (2+1) * 5
    assert referrer.referred_users_with_purchase == 3
```

**Step 3: Run tests**

```bash
pytest tests/application/services/test_referral_service.py -v
```
Expected: PASS

**Step 4: Commit**

```bash
git add application/services/referral_service.py tests/application/services/test_referral_service.py
git commit -m "feat(referral): add record_referred_user_purchase with +5GB bonus tracking"
```

---

## Phase 5: Actualizar Handlers de Compra

### Task 6: Actualizar mensajes de confirmación con desglose de bonos

**Files:**
- Modify: `telegram_bot/features/buy_gb/messages_buy_gb.py`
- Modify: `telegram_bot/features/buy_gb/handlers_buy_gb.py`

**Step 1: Update confirmation message to show bonus breakdown**

```python
# In BuyGbMessages.Payment, update CONFIRMATION:
CONFIRMATION = (
    "✅ **Compra Exitosa**\n\n"
    "📦 **Paquete:** {package_name}\n"
    "📊 **Datos:** {final_gb:.1f} GB ({base_gb} GB base)\n"
    "{bonus_breakdown}"
    "⭐ **Pagado:** {stars} estrellas\n"
    "📅 **Expira:** {expires_at}\n\n"
    "💎 *Tu paquete esta activo y listo para usar*"
)

# Add method to format bonus breakdown:
@staticmethod
def format_bonus_breakdown(bonuses: list, total_bonus: int) -> str:
    if total_bonus == 0:
        return ""
    
    lines = ["🎁 **Bonos Aplicados:**"]
    for bonus in bonuses:
        lines.append(f"  • {bonus.description}")
    lines.append(f"📈 **Bonus Total:** +{total_bonus}%\n")
    return "\n".join(lines)
```

**Step 2: Update handler to use new return value**

```python
# In handlers_buy_gb.py, update payment completion:
result, bonus_breakdown = await self.data_package_service.purchase_package(
    user_id=user_id,
    package_type=package_type_str,
    telegram_payment_id=payment_id,
    current_user_id=user_id,
)

bonus_text = BuyGbMessages.Payment.format_bonus_breakdown(
    bonus_breakdown["user_bonuses"],
    bonus_breakdown["total_bonus_percent"]
)

message = BuyGbMessages.Payment.CONFIRMATION.format(
    package_name=package_option.name,
    final_gb=bonus_breakdown["final_gb"],
    base_gb=bonus_breakdown["base_gb"],
    bonus_breakdown=bonus_text,
    stars=package_option.stars,
    expires_at=result.expires_at.strftime("%d/%m/%Y"),
)
```

**Step 3: Run tests**

```bash
pytest tests/telegram_bot/features/buy_gb/ -v
```
Expected: PASS

**Step 4: Commit**

```bash
git add telegram_bot/features/buy_gb/
git commit -m "feat(bonus): update purchase messages to show bonus breakdown"
```

---

## Phase 6: Testing y Finalización

### Task 7: Run all tests

```bash
pytest tests/ -v --tb=short
```
Expected: All tests pass

### Task 8: Run linting

```bash
flake8 application/services/user_bonus_service.py
code=" 
        # If there are errors, fix them
        echo "Fixing lint errors..."
        black application/services/user_bonus_service.py
        ```

### Task 9: Final commit and merge

```bash
# Stage all changes
git add .
git commit -m "feat(bonus): complete user bonus system implementation (closes #220)"

# Merge to develop
git checkout develop
git merge feature/user-bonus-system-220 --no-ff -m "Merge feature/user-bonus-system-220: implement user bonus system"

# Push
git push origin develop

# Delete feature branch
git branch -d feature/user-bonus-system-220
git push origin --delete feature/user-bonus-system-220
```

### Task 10: Close GitHub Issue

```bash
gh issue close 220 --comment "✅ Implementación completada y mergeada a develop. Sistema de bonos acumulativos ahora disponible con:
- Bono de bienvenida (+20% primera compra)
- Bono de fidelidad acumulativo (+10%, +15%, +25% en 3ra, 5ta, 10ma compra)
- Bono de recarga rápida (+15% si renueva ≤7 días)
- Bono de referidos (+5GB por cada referido que compre, +10% para referido en primera compra)"
```

---

## Resumen de Cambios

### Archivos Creados
1. `application/services/user_bonus_service.py` - Servicio de cálculo de bonos
2. `tests/application/services/test_user_bonus_service.py` - Tests del servicio
3. `alembic/versions/XXX_add_user_bonus_tracking_fields.py` - Migración DB

### Archivos Modificados
1. `domain/entities/user.py` - Campos de tracking de bonos
2. `infrastructure/persistence/postgresql/models/base.py` - Columnas DB
3. `infrastructure/persistence/postgresql/user_repository.py` - Mapeo entidad/modelo
4. `application/services/data_package_service.py` - Integración de bonos en compra
5. `application/services/referral_service.py` - Tracking de referidos con compra
6. `telegram_bot/features/buy_gb/messages_buy_gb.py` - Mensajes con desglose
7. `telegram_bot/features/buy_gb/handlers_buy_gb.py` - Mostrar bonos en confirmación

### Tests
- Todos los tests existentes deben seguir pasando
- Nuevos tests para UserBonusService
- Tests actualizados para DataPackageService con bonos
