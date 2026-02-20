# [Fase 3] Eliminar características no esenciales

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Eliminar servicios, entidades, handlers y features de Telegram no esenciales del sistema simplificado.

**Architecture:** Eliminación sistemática de features obsoletas comenzando desde las capas más externas (Telegram handlers) hacia las capas internas (servicios, entidades), actualizando el contenedor DI y main.py para evitar referencias rotas.

**Tech Stack:** Python, Telegram Bot API, punq (DI), SQLAlchemy, Alembic

---

## Resumen de Archivos a Eliminar

### Application Services (5 archivos)
- `application/services/game_service.py`
- `application/services/referral_service.py`
- `application/services/announcer_service.py`
- `application/services/broadcast_service.py`

**MANTENER:**
- `application/services/vpn_service.py` (core)
- `application/services/payment_service.py` (core - actualizar para data_packages)
- `application/services/admin_service.py` (core - simplificar)

### Domain Entities (5 archivos)
- `domain/entities/achievement.py`
- `domain/entities/game.py`
- `domain/entities/task.py`
- `domain/entities/ticket.py`
- `domain/entities/conversation.py`

**MANTENER:**
- `domain/entities/user.py`
- `domain/entities/vpn_key.py`
- `domain/entities/data_package.py`
- `domain/entities/admin.py`

### Domain Interfaces (2 archivos)
- `domain/interfaces/igame_service.py`
- `domain/interfaces/ireferral_service.py`

### Infrastructure (1 archivo)
- `infrastructure/api_clients/groq_client.py`

### Telegram Features (8 directorios)
- `telegram_bot/features/game/`
- `telegram_bot/features/referral/`
- `telegram_bot/features/announcer/`
- `telegram_bot/features/broadcast/`
- `telegram_bot/features/vip/`
- `telegram_bot/features/shop/`
- `telegram_bot/features/admin/` (simplificar, no eliminar)

**MANTENER:**
- `telegram_bot/features/vpn_keys/`
- `telegram_bot/features/key_management/`
- `telegram_bot/features/operations/`
- `telegram_bot/features/payments/`
- `telegram_bot/features/user_management/`

---

## Task 1: Eliminar features de Telegram no esenciales

**Files:**
- Delete: `telegram_bot/features/game/` (directorio completo)
- Delete: `telegram_bot/features/referral/` (directorio completo)
- Delete: `telegram_bot/features/announcer/` (directorio completo)
- Delete: `telegram_bot/features/broadcast/` (directorio completo)
- Delete: `telegram_bot/features/vip/` (directorio completo)
- Delete: `telegram_bot/features/shop/` (directorio completo)

**Step 1: Eliminar directorios de features**

```bash
rm -rf telegram_bot/features/game
rm -rf telegram_bot/features/referral
rm -rf telegram_bot/features/announcer
rm -rf telegram_bot/features/broadcast
rm -rf telegram_bot/features/vip
rm -rf telegram_bot/features/shop
```

**Step 2: Verificar eliminación**

Run: `ls telegram_bot/features/`
Expected: Solo deben quedar: admin, key_management, operations, payments, user_management, vpn_keys

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: remove obsolete telegram features (game, referral, announcer, broadcast, vip, shop)"
```

---

## Task 2: Eliminar entidades de dominio obsoletas

**Files:**
- Delete: `domain/entities/achievement.py`
- Delete: `domain/entities/game.py`
- Delete: `domain/entities/task.py`
- Delete: `domain/entities/ticket.py`
- Delete: `domain/entities/conversation.py`

**Step 1: Eliminar archivos de entidades**

```bash
rm domain/entities/achievement.py
rm domain/entities/game.py
rm domain/entities/task.py
rm domain/entities/ticket.py
rm domain/entities/conversation.py
```

**Step 2: Verificar eliminación**

Run: `ls domain/entities/`
Expected: Solo deben quedar: __init__.py, admin.py, data_package.py, user.py, vpn_key.py

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: remove obsolete domain entities (achievement, game, task, ticket, conversation)"
```

---

## Task 3: Eliminar interfaces de dominio obsoletas

**Files:**
- Delete: `domain/interfaces/igame_service.py`
- Delete: `domain/interfaces/ireferral_service.py`

**Step 1: Eliminar archivos de interfaces**

```bash
rm domain/interfaces/igame_service.py
rm domain/interfaces/ireferral_service.py
```

**Step 2: Verificar eliminación**

Run: `ls domain/interfaces/`
Expected: Solo deben quedar las interfaces esenciales

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: remove obsolete domain interfaces (igame_service, ireferral_service)"
```

---

## Task 4: Eliminar servicios de aplicación obsoletos

**Files:**
- Delete: `application/services/game_service.py`
- Delete: `application/services/referral_service.py`
- Delete: `application/services/announcer_service.py`
- Delete: `application/services/broadcast_service.py`

**Step 1: Eliminar archivos de servicios**

```bash
rm application/services/game_service.py
rm application/services/referral_service.py
rm application/services/announcer_service.py
rm application/services/broadcast_service.py
```

**Step 2: Verificar eliminación**

Run: `ls application/services/`
Expected: Solo deben quedar: __init__.py, admin_service.py, common/, payment_service.py, vpn_service.py

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: remove obsolete application services (game, referral, announcer, broadcast)"
```

---

## Task 5: Eliminar cliente de infraestructura obsoleto

**Files:**
- Delete: `infrastructure/api_clients/groq_client.py`

**Step 1: Eliminar cliente Groq**

```bash
rm infrastructure/api_clients/groq_client.py
```

**Step 2: Verificar eliminación**

Run: `ls infrastructure/api_clients/`
Expected: Solo deben quedar: __init__.py, client_outline.py, client_wireguard.py

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: remove groq_client (AI support feature removed)"
```

---

## Task 6: Actualizar handler_initializer.py

**Files:**
- Modify: `telegram_bot/handlers/handler_initializer.py`

**Step 1: Eliminar imports obsoletos**

Eliminar las siguientes líneas del archivo:

```python
# ELIMINAR estas líneas (aprox. líneas 15-50):
from telegram_bot.features.announcer.handlers_announcer import (
    get_announcer_handlers, get_announcer_callback_handlers
)
from telegram_bot.features.broadcast.handlers_broadcast import (
    get_broadcast_handlers, get_broadcast_callback_handlers
)
from telegram_bot.features.game.handlers_game import (
    get_game_handlers, get_game_callback_handlers
)
from telegram_bot.features.referral.handlers_referral import (
    get_referral_handlers, get_referral_callback_handlers
)
from telegram_bot.features.shop.handlers_shop import (
    get_shop_handlers, get_shop_callback_handlers
)
from telegram_bot.features.vip.handlers_vip import (
    get_vip_handlers, get_vip_callback_handlers
)

# ELIMINAR estas líneas de imports de servicios:
from application.services.announcer_service import AnnouncerService
from application.services.broadcast_service import BroadcastService
from application.services.game_service import GameService
```

**Step 2: Simplificar función `_get_service_handlers`**

Eliminar completamente la función `_get_service_handlers` (líneas 72-91).

**Step 3: Simplificar función `_get_core_handlers`**

Actualizar la función para eliminar referencias a referral, shop, vip:

```python
def _get_core_handlers(vpn_service, payment_service) -> List[BaseHandler]:
    handlers = []

    handlers.extend(get_key_management_handlers(vpn_service))
    handlers.extend(get_key_management_callback_handlers(vpn_service))
    logger.info("Key management handlers configured")

    handlers.extend(get_operations_handlers(vpn_service, payment_service))
    handlers.extend(get_operations_callback_handlers(vpn_service, payment_service))
    logger.info("Operations handlers configured")

    handlers.extend(get_payments_handlers(payment_service, vpn_service))
    handlers.extend(get_payments_callback_handlers(payment_service, vpn_service))
    logger.info("Payments handlers configured")

    handlers.extend(get_user_management_handlers(vpn_service, None))
    handlers.extend(get_user_callback_handlers(vpn_service, None))
    logger.info("User management handlers configured")

    handlers.extend(get_vpn_keys_handlers(vpn_service))
    handlers.extend(get_vpn_keys_callback_handlers(vpn_service))
    logger.info("VPN keys handlers configured")

    return handlers
```

**Step 4: Actualizar función `initialize_handlers`**

```python
def initialize_handlers(
    vpn_service: VpnService,
    payment_service: PaymentService
) -> List[BaseHandler]:
    logger.info("Initializing bot handlers...")
    handlers = []

    try:
        container = get_container()

        handlers.extend(_get_admin_handlers(container))
        handlers.extend(_get_core_handlers(vpn_service, payment_service))

        logger.info(f"Total handlers configured: {len(handlers)}")
        return handlers

    except Exception as e:
        logger.error(f"Error initializing handlers: {e}")
        raise
```

**Step 5: Commit**

```bash
git add telegram_bot/handlers/handler_initializer.py
git commit -m "refactor: simplify handler_initializer removing obsolete features"
```

---

## Task 7: Actualizar container.py

**Files:**
- Modify: `application/services/common/container.py`

**Step 1: Eliminar imports obsoletos**

Eliminar:
```python
from infrastructure.api_clients.groq_client import GroqClient
from application.services.referral_service import ReferralService
from application.services.broadcast_service import BroadcastService
from application.services.announcer_service import AnnouncerService
from application.services.game_service import GameService
from telegram_bot.features.announcer import get_announcer_handlers
from telegram_bot.features.referral import (
    get_referral_handlers,
    get_referral_callback_handlers
)
from telegram_bot.features.broadcast import get_broadcast_handlers
from telegram_bot.features.game import (
    get_game_handlers,
    get_game_callback_handlers
)
from telegram_bot.features.shop import (
    get_shop_handlers,
    get_shop_callback_handlers
)
from telegram_bot.features.vip import (
    get_vip_handlers,
    get_vip_callback_handlers
)
```

**Step 2: Actualizar `_configure_infrastructure_clients`**

Eliminar la línea:
```python
container.register(GroqClient, scope=punq.Scope.singleton)
```

**Step 3: Actualizar `_configure_application_services`**

Eliminar las funciones factory y registros de:
- `create_referral_service`
- `create_broadcast_service`
- `create_announcer_service`
- `create_game_service`

Y sus correspondientes `container.register()`.

**Step 4: Actualizar `_configure_handlers`**

Eliminar todas las funciones factory y registros relacionados con:
- announcer_handlers
- referral_handlers
- broadcast_handlers
- game_handlers
- shop_handlers
- vip_handlers

**Step 5: Commit**

```bash
git add application/services/common/container.py
git commit -m "refactor: simplify DI container removing obsolete services and handlers"
```

---

## Task 8: Actualizar main.py

**Files:**
- Modify: `main.py`

**Step 1: Eliminar import obsoleto**

Eliminar:
```python
from application.services.referral_service import ReferralService
```

**Step 2: Actualizar resolución de servicios**

```python
container = get_container()
vpn_service = container.resolve(VpnService)
payment_service = container.resolve(PaymentService)
logger.info("Dependency container configured correctly.")
```

**Step 3: Actualizar llamada a initialize_handlers**

```python
handlers = initialize_handlers(vpn_service, payment_service)
```

**Step 4: Commit**

```bash
git add main.py
git commit -m "refactor: simplify main.py removing referral service dependency"
```

---

## Task 9: Verificar que el bot inicia sin errores

**Step 1: Verificar imports**

Run: `python -c "from main import main; print('OK')"`
Expected: `OK` sin errores de import

**Step 2: Verificar sintaxis Python**

Run: `python -m py_compile main.py application/services/common/container.py telegram_bot/handlers/handler_initializer.py`
Expected: Sin output (éxito)

**Step 3: Commit final**

```bash
git add -A
git commit -m "chore: complete removal of non-essential features for issue #74"
```

---

## Task 10: Actualizar payment_service.py para data_packages

**Files:**
- Modify: `application/services/payment_service.py`

**Nota:** Este task es opcional y depende de si payment_service necesita actualizaciones para trabajar con data_packages en lugar de VIP/referrals. Revisar el archivo y actualizar según sea necesario.

---

## Criterios de Aceptación

- [ ] No hay archivos de características eliminadas
- [ ] El bot inicia sin errores
- [ ] No hay imports rotos
- [ ] El contenedor DI solo registra servicios esenciales
- [ ] Los handlers solo incluyen features esenciales (vpn_keys, key_management, operations, payments, user_management)

---

## Features a Mantener (Core)

| Feature | Handlers | Servicio |
|---------|----------|----------|
| VPN Keys | ✅ | VpnService |
| Key Management | ✅ | VpnService |
| Operations | ✅ | VpnService, PaymentService |
| Payments | ✅ | PaymentService |
| User Management | ✅ | VpnService |
| Admin | ✅ (simplificado) | AdminService |
