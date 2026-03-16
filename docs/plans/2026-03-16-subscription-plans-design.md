# Subscription Plans Design - uSipipo VPN Manager

**Date:** March 16, 2026
**Version:** 1.0.0
**Status:** Approved
**Author:** uSipipo Team

---

## 1. Executive Summary

This document outlines the design for implementing **Subscription Plans** in the uSipipo VPN Manager Telegram bot. The subscription model targets free-tier users who enjoy the service and want **unlimited data** without GB restrictions at an affordable price point.

### Key Value Proposition

- ✅ **Unlimited Data (No GB Limits)** - Consume todo el data que quieras
- ✅ **No Long-term Commitment** - Users can cancel anytime
- ✅ **Consistent Pricing** - Sin trucos promocionales, mismo precio siempre
- ✅ **Affordable & Honest** - Precios realistas para infraestructura actual
- ⚠️ **Fair Use Policy** - Velocidad depende de disponibilidad del servidor

### Important Considerations

**Current Infrastructure:** Single 2GB VPS running multiple services (bot, web app, Outline, WireGuard)

**What This Means:**
- ✅ Perfect for: Daily browsing, social media, HD streaming, gaming, remote work
- ⚠️ Not suitable for: 24/7 4K streaming, massive torrenting, commercial use
- 📈 **Future Scaling:** Prices will increase as we add more servers and countries

---

## 2. Market Analysis & Competitive Pricing

### VPN Market Pricing (2025)

| Provider | Monthly | 3-Month | 6-Month | Annual |
|----------|---------|---------|---------|--------|
| **NordVPN** | $12.99/mo | ~$3.99/mo | ~$2.99/mo | $3.39/mo |
| **Surfshark** | $15.45/mo | ~$3.99/mo | ~$2.49/mo | $2.19/mo |
| **ExpressVPN** | $12.99/mo | - | - | - |
| **CyberGhost** | $12.99/mo | - | - | - |
| **Mullvad** | $5.86/mo (flat) | - | - | - |
| **Windscribe** | $9.00/mo | - | - | - |

**Key Insight:** Monthly plans are expensive ($12-15), but long-term plans drop to $2-4/mo.

### uSipipo Competitive Advantage

| Aspect | Traditional VPNs | uSipipo |
|--------|-----------------|---------|
| Commitment | 1-2 years for best price | No commitment |
| Data Limits | Often have fair-use policies | Unlimited GB* |
| Price Stability | Promotional rates increase | Same price always |
| Target Audience | General users | Budget-conscious users |
| Infrastructure | 1000s of servers | Single VPS (scaling) |
| Speed | Guaranteed | Best-effort (fair use) |

\* *Unlimited GB with fair use policy - speed varies by server load*

---

## 3. Subscription Plans

### 3.1 Plan Options (Recommended Pricing - Realistic for Current Infrastructure)

| Plan | Duration | Total Price | Price/Month | Stars | USDT (Crypto) | Savings |
|------|----------|-------------|-------------|-------|---------------|---------|
| **1 Month** | 30 days | **$2.99** | $2.99 | **360 ⭐** | **$2.99** | - |
| **3 Months** | 90 days | **$7.99** | $2.66/mo | **960 ⭐** | **$7.99** | **11%** |
| **6 Months** | 180 days | **$12.99** | $2.16/mo | **1,560 ⭐** | **$12.99** | **28%** |

**Savings vs Monthly:**
- 3 months: Save $0.98 (11% discount)
- 6 months: Save $4.95 (28% discount)

### 3.2 Pricing Strategy Justification

| Plan | Justification |
|------|---------------|
| **1 Month ($2.99)** | Low barrier to entry - attractive for users to try the service without commitment |
| **3 Months ($7.99)** | Real incentive - meaningful discount to encourage longer commitment |
| **6 Months ($12.99)** | Anchor price - best value, positions service as affordable long-term |

### 3.3 Exchange Rate

- **1 USDT = 120 Stars** (consistent with existing system)
- Prices calculated to be **honest with current infrastructure** (single 2GB VPS)
- **Future-proof:** Prices can increase as infrastructure scales (more servers, countries)

### 3.4 Pricing Evolution Strategy

```
Phase 1 (Current - Single VPS):
├─ 1 Month: $2.99
├─ 3 Months: $7.99
└─ 6 Months: $12.99

Phase 2 (2-3 VPS, More Countries):
├─ 1 Month: $4.99 (+67%)
├─ 3 Months: $11.99 (+50%)
└─ 6 Months: $19.99 (+54%)

Phase 3 (5+ VPS, Global Coverage):
├─ 1 Month: $6.99 (+134%)
├─ 3 Months: $16.99 (+113%)
└─ 6 Months: $29.99 (+131%)
```

**Key Principle:** Start affordable, scale prices with infrastructure improvements.

---

## 4. Business Rules

### 4.1 Unlimited Data with Fair Use

- ✅ **NO GB limits** during subscription validity
- ✅ User can consume all data they want
- ⚠️ **Fair Use Policy:** Speed may vary based on server availability and total load
- ⚠️ **Not suitable for:** 24/7 4K streaming, large-scale torrenting, commercial use
- ✅ **Ideal for:** Daily browsing, social media, HD streaming, gaming, remote work

**Fair Use Clause (Honest Messaging):**

```
📋 **Política de Uso Justo**

Tu plan premium es ILIMITADO en GB, pero operamos con servidores
compartidos. Esto significa:

✅ Lo que SÍ puedes hacer:
├─ Navegación ilimitada
├─ Streaming HD (1080p)
├─ Gaming online
├─ Redes sociales
├─ Trabajo remoto / VPN corporativa
└─ Descargas moderadas

⚠️ Lo que NO es recomendado:
├─ Streaming 4K continuo 24/7
├─ Torrenting masivo constante
├─ Servidores proxy públicos
└─ Uso comercial intensivo

📊 **Velocidad:** Depende de la disponibilidad del servidor.
   La mayoría de usuarios obtiene 50-100 Mbps, pero puede variar
   según carga del servidor y tu ubicación.

💡 **Si necesitas alto rendimiento constante:** Considera VPNs
   enterprise con servidores dedicados ($50-100/mes).
```

**Why This Matters:**
- 🎯 **Honesto:** No prometemos lo que no podemos garantizar
- 🛡️ **Protege tu VPS:** Un solo usuario 4K 24/7 = ~500GB/día = satura tu servidor de 2GB RAM
- 📈 **Escalable:** Cuando tengas múltiples VPS, puedes ofrecer tiers premium más caros
- ⚖️ **Legal:** Cláusula de fair use te protege de abusos

### 4.2 Validity & Renewal

| Plan | Duration | Expiration |
|------|----------|------------|
| 1 Month | 30 days | From activation date |
| 3 Months | 90 days | From activation date |
| 6 Months | 180 days | From activation date |

- ⚠️ **NO automatic renewal** (user must manually renew)
- ⚠️ Upon expiration, user returns to FREE tier (5GB)
- ⚠️ Reminder notifications 3 days before expiration

### 4.3 Compatibility with Current System

- ✅ Plans **coexist** with existing GB packages
- ✅ User can have: Active Plan + GB Packages simultaneously
- ✅ If Plan active: uses **UNLIMITED** first
- ✅ If NO Plan: uses GB packages → free tier

### 4.4 Multiple VPN Keys

- ✅ Plan applies to **ALL** user's VPN keys
- ✅ No key limit by default (can purchase extra slots)
- ✅ All keys share same "Premium" status

### 4.5 Payment Methods

- ✅ Same methods as current system:
  - **Telegram Stars** (via invoice system)
  - **Crypto** (USDT/BSC via TronDealer webhook)
- ✅ Exchange rate: 1 USDT = 120 Stars
- ✅ Same payment infrastructure (no new payment providers)

### 4.6 Upgrades & Downgrades

- ✅ Can purchase another plan while one is active
- ✅ Validity is **added** (e.g., 1 month + 3 months = 120 days)
- ✅ No refunds for early cancellation
- ✅ Can switch between plan types on renewal

### 4.7 Ghost Key Cleanup

- ✅ Keys from users with Active Plan are **NOT** deleted for inactivity
- ✅ FREE tier keys still subject to weekly cleanup

### 4.8 Support

- ✅ **Priority support** for users with Active Plan
- ✅ Ticket response time: < 24 hours
- ✅ Dedicated support channel for premium users

---

## 5. Technical Architecture

### 5.1 New Domain Entity: SubscriptionPlan

```python
@dataclass
class SubscriptionPlan:
    """Represents an active subscription plan for a user."""

    id: Optional[uuid.UUID] = None
    user_id: int = None
    plan_type: PlanType = None  # Enum: ONE_MONTH, THREE_MONTHS, SIX_MONTHS
    stars_paid: int = 0
    starts_at: datetime = None
    expires_at: datetime = None
    is_active: bool = True
    created_at: datetime = None
    updated_at: datetime = None

    @property
    def duration_days(self) -> int:
        """Returns plan duration in days."""
        duration_map = {
            PlanType.ONE_MONTH: 30,
            PlanType.THREE_MONTHS: 90,
            PlanType.SIX_MONTHS: 180,
        }
        return duration_map.get(self.plan_type, 0)

    @property
    def days_remaining(self) -> int:
        """Returns days remaining until expiration."""
        now = datetime.now(timezone.utc)
        delta = self.expires_at - now
        return max(0, delta.days)

    @property
    def is_expiring_soon(self) -> bool:
        """True if plan expires in less than 3 days."""
        return self.days_remaining <= 3
```

### 5.2 New Enum: PlanType

```python
class PlanType(str, Enum):
    """Subscription plan types."""

    ONE_MONTH = "one_month"
    THREE_MONTHS = "three_months"
    SIX_MONTHS = "six_months"
```

### 5.3 New Service: SubscriptionService

```python
class SubscriptionService:
    """Manages subscription lifecycle."""

    def __init__(
        self,
        subscription_repo: ISubscriptionRepository,
        user_repo: IUserRepository,
    ):
        self.subscription_repo = subscription_repo
        self.user_repo = user_repo

    async def activate_plan(
        self,
        user_id: int,
        plan_type: PlanType,
        payment_id: str,
        current_user_id: int,
    ) -> SubscriptionPlan:
        """Activate a new subscription plan."""
        pass

    async def get_active_plan(self, user_id: int, current_user_id: int) -> Optional[SubscriptionPlan]:
        """Get user's currently active plan."""
        pass

    async def extend_plan(
        self,
        user_id: int,
        plan_type: PlanType,
        current_user_id: int,
    ) -> SubscriptionPlan:
        """Extend existing plan or create new one."""
        pass

    async def expire_plans(self, admin_user_id: int) -> int:
        """Background job to expire old plans."""
        pass

    def is_premium_user(self, user_id: int) -> bool:
        """Check if user has active subscription."""
        pass

    def get_plan_price(self, plan_type: PlanType) -> PlanPrice:
        """Get pricing information for a plan."""
        pass
```

### 5.4 New Repository Interface: ISubscriptionRepository

```python
class ISubscriptionRepository:
    """Repository interface for subscription operations."""

    async def save(self, plan: SubscriptionPlan, current_user_id: int) -> SubscriptionPlan:
        """Save or update a subscription plan."""
        pass

    async def get_by_id(self, plan_id: uuid.UUID, current_user_id: int) -> Optional[SubscriptionPlan]:
        """Get subscription by ID."""
        pass

    async def get_active_by_user(self, user_id: int, current_user_id: int) -> Optional[SubscriptionPlan]:
        """Get active subscription for a user."""
        pass

    async def get_expiring_plans(self, days: int, current_user_id: int) -> List[SubscriptionPlan]:
        """Get plans expiring within N days."""
        pass

    async def get_expired_plans(self, current_user_id: int) -> List[SubscriptionPlan]:
        """Get all expired plans."""
        pass

    async def deactivate(self, plan_id: uuid.UUID, current_user_id: int) -> bool:
        """Deactivate a subscription plan."""
        pass
```

### 5.5 Database Schema

```sql
-- New table: subscription_plans
CREATE TABLE subscription_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    plan_type VARCHAR(20) NOT NULL CHECK (plan_type IN ('one_month', 'three_months', 'six_months')),
    stars_paid INTEGER NOT NULL,
    starts_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_subscription_plans_user_id ON subscription_plans(user_id);
CREATE INDEX idx_subscription_plans_is_active ON subscription_plans(is_active);
CREATE INDEX idx_subscription_plans_expires_at ON subscription_plans(expires_at);
CREATE INDEX idx_subscription_plans_active_user ON subscription_plans(user_id, is_active) WHERE is_active = TRUE;

-- Add premium flag to VPN keys (for quick lookup)
ALTER TABLE vpn_keys ADD COLUMN is_premium BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX idx_vpn_keys_is_premium ON vpn_keys(is_premium);
```

### 5.6 Pricing Configuration

```python
@dataclass
class PlanPrice:
    """Subscription plan pricing."""

    plan_type: PlanType
    duration_days: int
    stars: int
    usdt: float
    savings_percent: float = 0


PLAN_PRICES: List[PlanPrice] = [
    PlanPrice(
        plan_type=PlanType.ONE_MONTH,
        duration_days=30,
        stars=360,
        usdt=2.99,
        savings_percent=0,
    ),
    PlanPrice(
        plan_type=PlanType.THREE_MONTHS,
        duration_days=90,
        stars=960,
        usdt=7.99,
        savings_percent=11,
    ),
    PlanPrice(
        plan_type=PlanType.SIX_MONTHS,
        duration_days=180,
        stars=1560,
        usdt=12.99,
        savings_percent=28,
    ),
]
```

---

## 6. Integration Points

### 6.1 VPN Key Management

**File:** `application/services/vpn_service.py`

```python
class VpnService:
    async def create_key(self, user_id: int, ...) -> VpnKey:
        # Check if user has active subscription
        active_plan = await self.subscription_service.get_active_plan(user_id)
        is_premium = active_plan is not None

        # Create key with appropriate limits
        if is_premium:
            # Unlimited data for premium users
            key.data_limit_bytes = -1  # Special value for unlimited
            key.is_premium = True
        else:
            # Standard 5GB limit for free users
            key.data_limit_bytes = 5 * (1024 ** 3)
            key.is_premium = False
```

### 6.2 Data Consumption Billing

**File:** `application/services/consumption_billing_service.py`

```python
class ConsumptionBillingService:
    async def consume_data(self, user_id: int, bytes_used: int) -> bool:
        # Check for active subscription first
        active_plan = await self.subscription_service.get_active_plan(user_id)

        if active_plan and active_plan.is_active:
            # Premium user - no consumption tracking needed
            logger.info(f"Premium user {user_id} consuming {bytes_used} bytes (unlimited)")
            return True

        # Non-premium: use existing GB package logic
        return await self._consume_from_packages(user_id, bytes_used)
```

### 6.3 Background Jobs

**File:** `infrastructure/jobs/expire_subscriptions_job.py`

```python
async def expire_subscriptions_job():
    """Daily job to expire old subscription plans."""

    admin_user_id = settings.ADMIN_ID
    subscription_service = get_service(SubscriptionService)

    # Get expired plans
    expired_count = await subscription_service.expire_plans(admin_user_id)

    if expired_count > 0:
        logger.info(f"📦 Expired {expired_count} subscription plans")

    # Send expiration notifications
    notification_service = get_service(NotificationService)
    await notification_service.send_plan_expiration_notifications()
```

**File:** `infrastructure/jobs/subscription_reminder_job.py`

```python
async def subscription_reminder_job():
    """Daily job to send expiration reminders."""

    subscription_repo = get_service(ISubscriptionRepository)

    # Get plans expiring in 3 days
    expiring_plans = await subscription_repo.get_expiring_plans(days=3)

    for plan in expiring_plans:
        await send_expiration_reminder(plan.user_id, plan.days_remaining)
```

### 6.4 Admin Panel

**File:** `telegram_bot/features/admin/`

New admin command: `/subscriptions`

```
╔══════════════════════════╗
║ 📊 SUBSCRIPTION STATS   ║
╠══════════════════════════╣
║                          ║
║ 👥 Active Plans: 127    ║
║ 💰 Monthly Revenue: $X  ║
║ 📈 Growth: +X%          ║
║                          ║
║ Plan Breakdown:         ║
║ ├─ 1 Month: 45 users   ║
║ ├─ 3 Months: 52 users  ║
║ └─ 6 Months: 30 users  ║
║                          ║
╚══════════════════════════╝
```

---

## 7. User Interface & Messages

### 7.1 Shop Menu Update

**File:** `telegram_bot/features/operations/keyboards_operations.py`

Add new button to shop menu:

```python
def shop_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📦 Paquetes de GB", callback_data="buy_gb_menu")],
        [InlineKeyboardButton("🚀 Planes Ilimitados", callback_data="subscription_plans_menu")],  # NEW
        [InlineKeyboardButton("🔑 Slots Adicionales", callback_data="buy_slots_menu")],
        [InlineKeyboardButton("🔙 Volver", callback_data="operations_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)
```

### 7.2 Subscription Plans Menu

**Message:** `SubscriptionMessages.Menu.PLANS_LIST`

```
╔══════════════════════════╗
║ 🚀 PLANES PREMIUM       ║
╠══════════════════════════╣
║                          ║
║  📦 1 MES - $2.99       ║
║     ⭐ 360 Stars         ║
║     💰 $2.99 USDT        ║
║                          ║
║  📦 3 MESES - $7.99     ║
║     ⭐ 960 Stars         ║
║     💰 $7.99 USDT        ║
║     💎 Ahorra 11%        ║
║                          ║
║  📦 6 MESES - $12.99    ║
║     ⭐ 1,560 Stars       ║
║     💰 $12.99 USDT       ║
║     💎 Ahorra 28%        ║
║                          ║
╠══════════════════════════╣
║ ✅ Datos ILIMITADOS     ║
║ ✅ Sin límites de GB    ║
║ ⚠️  Uso Justo (Fair Use)║
║ 💰 Precio fijo siempre  ║
╠══════════════════════════╣
║ 📋 POLÍTICA DE USO JUSTO ║
║                          ║
║ ✅ Ideal para:           ║
║ ├─ Streaming HD (1080p) ║
║ ├─ Gaming online         ║
║ ├─ Redes sociales        ║
║ └─ Trabajo remoto        ║
║                          ║
║ ⚠️ No recomendado para: ║
║ ├─ 4K 24/7 continuo      ║
║ ├─ Torrenting masivo     ║
║ └─ Uso comercial         ║
║                          ║
║ 📊 Velocidad: 50-100 Mbps║
║    (depende del servidor)║
╚══════════════════════════╝

👇 Selecciona tu plan:
[ 1 Mes ] [ 3 Meses ] [ 6 Meses ]
[    Ver Mi Plan Actual    ]
[        🔙 Volver         ]
```

### 7.3 Plan Activation Confirmation

```
✅ **Plan Activado Exitosamente**

🚀 **Plan:** {plan_name}
📅 **Duración:** {duration_days} días
⭐ **Pagado:** {stars} Stars
💰 **Monto:** ${usdt} USDT

🎉 **Beneficios Activos:**
├─ ✅ Datos ILIMITADOS (sin límite de GB)
├─ ✅ Válido hasta: {expires_at}
├─ ✅ Soporte prioritario
└─ ⚠️ Velocidad: 50-100 Mbps (según servidor)

📋 **Política de Uso Justo:**
├─ ✅ Streaming HD (1080p), Gaming, Redes
├─ ⚠️ No 4K continuo 24/7
└─ ⚠️ No torrenting masivo

💡 *Consume todo el data que quieras, sin límites de GB.
    La velocidad puede variar según la carga del servidor.*

💎 *Disfruta de tu experiencia premium*
```

### 7.4 Expiration Reminder (3 days before)

```
⚠️ **Tu Plan Está por Vencer**

🚀 **Plan:** {plan_name}
⏰ **Expira en:** {days_remaining} días
📅 **Fecha:** {expires_at}

💡 *Renueva ahora para mantener tus beneficios:*
├─ ✅ Datos ILIMITADOS
├─ ✅ Sin interrupciones
└─ ✅ Mismo precio siempre

[ 🔁 Renovar Plan ]
[ 📦 Ver Otros Planes ]
[ 🔙 Volver ]
```

### 7.5 Plan Expiration Notification

```
⚠️ **Plan Vencido**

Tu plan premium ha vencido.

📊 **Estado Actual:**
├─ Vuelves al plan FREE (5GB)
├─ Tus claves se mantienen activas
└─ Soporte vuelve a estándar

💡 *Renueva para recuperar beneficios:*

[ 🚀 Renovar Plan ]
[ 📦 Ver Planes ]
```

---

## 8. Error Handling

### 8.1 Payment Failures

```python
class SubscriptionPaymentError(Exception):
    """Raised when subscription payment fails."""
    pass

try:
    plan = await subscription_service.activate_plan(
        user_id=user_id,
        plan_type=plan_type,
        payment_id=payment_id,
    )
except SubscriptionPaymentError as e:
    logger.error(f"Subscription payment failed: {e}")
    await send_payment_failed_message(user_id)
```

### 8.2 Edge Cases

| Scenario | Handling |
|----------|----------|
| Payment succeeds but DB fails | Rollback transaction, refund if crypto |
| User deletes bot during payment | Webhook still processes, notify on return |
| Duplicate payment webhook | Idempotency check on payment_id |
| Plan expires during active session | Grace period until next key sync |
| Timezone issues | All datetimes stored in UTC |

---

## 9. Testing Strategy

### 9.1 Unit Tests

```python
class TestSubscriptionService:
    async def test_activate_plan_creates_subscription(self):
        """Test plan activation creates subscription."""
        pass

    async def test_extend_plan_adds_validity(self):
        """Test extending plan adds days to expiration."""
        pass

    async def test_is_premium_user_returns_true(self):
        """Test premium user detection."""
        pass

    async def test_expire_plans_deactivates_old_plans(self):
        """Test background job expires old plans."""
        pass
```

### 9.2 Integration Tests

```python
class TestSubscriptionFlow:
    async def test_full_purchase_flow_stars(self):
        """Test complete purchase flow with Telegram Stars."""
        pass

    async def test_full_purchase_flow_crypto(self):
        """Test complete purchase flow with crypto."""
        pass

    async def test_premium_user_unlimited_data(self):
        """Test premium users have unlimited data."""
        pass
```

### 9.3 Test Coverage Goals

- **Domain Layer:** 100% coverage
- **Application Services:** 95% coverage
- **Infrastructure:** 90% coverage
- **Handlers:** 85% coverage

---

## 10. Migration Plan

### 10.1 Database Migration

**File:** `migrations/versions/YYYYMMDD_add_subscription_plans.py`

```python
"""Add subscription plans tables

Revision ID: add_subscriptions_001
Revises: previous_revision
Create Date: 2026-03-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Create subscription_plans table
    op.create_table(
        'subscription_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('plan_type', sa.String(length=20), nullable=False),
        sa.Column('stars_paid', sa.Integer(), nullable=False),
        sa.Column('starts_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.telegram_id'], ondelete='CASCADE')
    )

    # Create indexes
    op.create_index('idx_subscription_plans_user_id', 'subscription_plans', ['user_id'])
    op.create_index('idx_subscription_plans_is_active', 'subscription_plans', ['is_active'])
    op.create_index('idx_subscription_plans_expires_at', 'subscription_plans', ['expires_at'])

    # Add is_premium flag to vpn_keys
    op.add_column('vpn_keys', sa.Column('is_premium', sa.Boolean(), nullable=False, default=False))
    op.create_index('idx_vpn_keys_is_premium', 'vpn_keys', ['is_premium'])

def downgrade():
    op.drop_index('idx_vpn_keys_is_premium', table_name='vpn_keys')
    op.drop_column('vpn_keys', 'is_premium')
    op.drop_index('idx_subscription_plans_expires_at', table_name='subscription_plans')
    op.drop_index('idx_subscription_plans_is_active', table_name='subscription_plans')
    op.drop_index('idx_subscription_plans_user_id', table_name='subscription_plans')
    op.drop_table('subscription_plans')
```

### 10.2 Deployment Steps

1. **Backup Database**
   ```bash
   pg_dump vpn_manager > backup_$(date +%Y%m%d).sql
   ```

2. **Run Migrations**
   ```bash
   uv run alembic upgrade head
   ```

3. **Deploy New Code**
   ```bash
   git pull origin main
   uv sync
   sudo systemctl restart usipipo
   ```

4. **Verify Deployment**
   ```bash
   sudo journalctl -u usipipo -f
   # Check for errors
   ```

5. **Enable Background Jobs**
   ```bash
   # Jobs start automatically on next scheduler cycle
   ```

---

## 11. Monitoring & Metrics

### 11.1 Key Metrics to Track

| Metric | Description | Target |
|--------|-------------|--------|
| `active_subscriptions` | Total active plans | Growth MoM |
| `subscription_revenue` | Monthly recurring revenue | Growth MoM |
| `plan_distribution` | % users per plan type | 6-month > 30% |
| `churn_rate` | % plans not renewed | < 20% |
| `conversion_rate` | Free → Premium | > 5% |

### 11.2 Grafana Dashboard

New dashboard: **Subscription Analytics**

```
╔══════════════════════════════════════════╗
║ SUBSCRIPTION ANALYTICS                   ║
╠══════════════════════════════════════════╣
║                                          ║
║ Active Plans: 127 ▲ 15%                 ║
║ MRR: $1,234 ▲ 12%                       ║
║ Churn: 8% ▼ 2%                          ║
║                                          ║
║ [Plan Distribution Pie Chart]           ║
║ ├─ 1 Month: 35%                         ║
║ ├─ 3 Months: 41%                        ║
║ └─ 6 Months: 24%                        ║
║                                          ║
║ [Revenue Trend - Last 30 Days]          ║
║                                          ║
║ [Conversion Funnel]                     ║
║ Free → View Plans → Purchase            ║
║                                          ║
╚══════════════════════════════════════════╝
```

---

## 12. Security Considerations

### 12.1 Payment Security

- ✅ Same security as existing payment system
- ✅ Webhook signature verification (TronDealer)
- ✅ Idempotency checks on payment processing
- ✅ Audit log for all payment events

### 12.2 Access Control

- ✅ Only admin users can view all subscriptions
- ✅ Users can only view their own subscriptions
- ✅ Repository methods require `current_user_id`
- ✅ SQL injection prevention via SQLAlchemy ORM

### 12.3 Data Protection

- ✅ All PII encrypted at rest
- ✅ Database connections use SSL
- ✅ No sensitive data in logs
- ✅ GDPR compliance for EU users

---

## 13. Future Enhancements

### Phase 2 (Post-Launch)

1. **Auto-Renewal** - Optional automatic renewal
2. **Family Plans** - Share premium across multiple accounts
3. **Referral Bonuses** - Earn free months for referrals
4. **Corporate Plans** - Bulk discounts for businesses
5. **Payment Methods** - Add PayPal, credit cards

### Phase 3 (Advanced)

1. **Usage Analytics** - Show users their data consumption
2. **Speed Tiers** - Different speed limits per plan
3. **Server Selection** - Premium servers for 6-month plans
4. **Mobile App Integration** - Show plan status in Android APK

---

## 14. Success Criteria

### Launch Goals (First 30 Days)

- [ ] 50+ active subscriptions
- [ ] < 1% payment failure rate
- [ ] < 5% churn rate
- [ ] Positive user feedback (> 4/5 rating)
- [ ] Server stability maintained (< 80% avg load)

### Business Goals (First 90 Days)

- [ ] 200+ active subscriptions
- [ ] $500+ MRR (at $2.99-12.99 price points)
- [ ] 30% of users on 6-month plans
- [ ] < 15% churn rate
- [ ] < 10% support tickets related to speed

### Infrastructure Goals (First 90 Days)

- [ ] Monitor server load patterns
- [ ] Identify heavy users (> 100GB/month)
- [ ] Document average speed per user
- [ ] Plan VPS upgrade path if > 70% capacity

### Revenue Projections (Conservative)

```
Month 1:
├─ 50 subscribers × $5 avg = $250 MRR
└─ Focus: Stability & feedback

Month 3:
├─ 200 subscribers × $5 avg = $1,000 MRR
└─ Focus: Optimize infrastructure

Month 6:
├─ 500 subscribers × $5 avg = $2,500 MRR
├─ Upgrade to 2-3 VPS
└─ Consider price increase to $4.99-19.99
```

**Key Metric:** Keep server load < 70% to maintain quality of service.

---

## 15. Appendix

### A. Glossary

| Term | Definition |
|------|------------|
| **Premium User** | User with active subscription plan |
| **Free Tier** | Default 5GB limit for non-paying users |
| **MRR** | Monthly Recurring Revenue |
| **Churn** | % of users who don't renew |

### B. References

- [Domain Entities Pattern](../QWEN.md#domain-entities)
- [Repository Pattern](../AGENTS.md#repository-pattern)
- [Telegram Stars Documentation](https://core.telegram.org/bots/payments/telegram-stars)
- [TronDealer API](../docs/trondealer-api.md)

### C. Related Documents

- [PRD.md](../PRD.md) - Product Requirements
- [TECHNOLOGY.md](../TECHNOLOGY.md) - Technology Stack
- [database_schema_v3.md](../database_schema_v3.md) - Database Schema

---

## 16. Approval

| Role | Name | Date | Status |
|------|------|------|--------|
| Product Owner | | 2026-03-16 | ✅ Approved |
| Tech Lead | | 2026-03-16 | ✅ Approved |
| Development | | 2026-03-16 | ✅ Approved |

---

**Document Version:** 1.0.0
**Last Updated:** March 16, 2026
**Next Review:** After implementation phase
