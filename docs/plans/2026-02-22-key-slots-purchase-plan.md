# Compra de Slots de Claves Adicionales - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Permitir a los usuarios comprar slots adicionales de claves VPN con Telegram Stars.

**Architecture:** Se extiende el sistema de pagos existente (BuyGbHandler) para incluir una nueva sección de "Slots de Claves" en el menú de compra. Se reutiliza el patrón de invoice/pre_checkout/successful_payment ya implementado para paquetes de datos.

**Tech Stack:** Python 3.11+, python-telegram-bot, SQLAlchemy Async, Telegram Stars API

---

## Resumen de Cambios

| Archivo | Tipo | Descripción |
|---------|------|-------------|
| `application/services/data_package_service.py` | Modificar | Agregar `SLOT_OPTIONS` y `purchase_key_slots()` |
| `telegram_bot/features/buy_gb/keyboards_buy_gb.py` | Modificar | Agregar teclados para slots |
| `telegram_bot/features/buy_gb/messages_buy_gb.py` | Modificar | Agregar mensajes para slots |
| `telegram_bot/features/buy_gb/handlers_buy_gb.py` | Modificar | Agregar handlers para compra de slots |

---

## Productos de Slots

| Producto | Slots Extra | Stars |
|----------|-------------|-------|
| +1 Clave | 1 | 25 |
| +3 Claves | 3 | 60 |
| +5 Claves | 5 | 90 |

---

## Task 1: Agregar SLOT_OPTIONS en DataPackageService

**Files:**
- Modify: `application/services/data_package_service.py`

**Step 1: Agregar SlotOption dataclass y SLOT_OPTIONS**

```python
@dataclass
class SlotOption:
    name: str
    slots: int
    stars: int


SLOT_OPTIONS: List[SlotOption] = [
    SlotOption(name="+1 Clave", slots=1, stars=25),
    SlotOption(name="+3 Claves", slots=3, stars=60),
    SlotOption(name="+5 Claves", slots=5, stars=90),
]
```

**Step 2: Agregar metodo purchase_key_slots()**

```python
async def purchase_key_slots(
    self,
    user_id: int,
    slots: int,
    telegram_payment_id: str,
    current_user_id: int,
) -> dict:
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

    logger.info(f"🔑 +{slots} slots comprados para usuario {user_id}")
    
    return {
        "slots_added": slots,
        "new_max_keys": user.max_keys + slots,
        "stars_paid": option.stars,
    }

def _get_slot_option(self, slots: int) -> Optional[SlotOption]:
    for option in SLOT_OPTIONS:
        if option.slots == slots:
            return option
    return None

def get_available_slots(self) -> List[SlotOption]:
    return SLOT_OPTIONS.copy()
```

---

## Task 2: Actualizar Keyboards para Slots

**Files:**
- Modify: `telegram_bot/features/buy_gb/keyboards_buy_gb.py`

**Step 1: Modificar packages_menu() para incluir seccion de slots**

```python
@staticmethod
def packages_menu() -> InlineKeyboardMarkup:
    keyboard = []
    row = []

    for pkg in PACKAGE_OPTIONS:
        button_text = f"⭐ {pkg.name} - {pkg.data_gb}GB"
        row.append(
            InlineKeyboardButton(
                button_text, callback_data=f"buy_package_{pkg.package_type.value}"
            )
        )
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("🔑 Comprar Claves Extra", callback_data="buy_slots_menu")])
    keyboard.append(
        [
            InlineKeyboardButton("📊 Ver Mis Datos", callback_data="view_data_summary"),
            InlineKeyboardButton("🔙 Volver", callback_data="operations_menu"),
        ]
    )

    return InlineKeyboardMarkup(keyboard)
```

**Step 2: Agregar slots_menu()**

```python
@staticmethod
def slots_menu() -> InlineKeyboardMarkup:
    keyboard = []
    for slot in SLOT_OPTIONS:
        button_text = f"🔑 {slot.name} - {slot.stars}⭐"
        keyboard.append([
            InlineKeyboardButton(button_text, callback_data=f"buy_slots_{slot.slots}")
        ])
    keyboard.append([InlineKeyboardButton("🔙 Volver a Paquetes", callback_data="buy_gb_menu")])
    return InlineKeyboardMarkup(keyboard)

@staticmethod
def slots_success() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🔑 Comprar Mas", callback_data="buy_slots_menu")],
        [InlineKeyboardButton("📦 Ver Paquetes", callback_data="buy_gb_menu")],
        [InlineKeyboardButton("🔙 Volver", callback_data="operations_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)
```

---

## Task 3: Actualizar Messages para Slots

**Files:**
- Modify: `telegram_bot/features/buy_gb/messages_buy_gb.py`

**Step 1: Agregar clase Slots en BuyGbMessages**

```python
class Slots:
    MENU = (
        "🔑 **Slots de Claves Adicionales**\n\n"
        "Cada slot te permite crear una clave VPN adicional.\n\n"
        "{slots_list}\n\n"
        "💡 *Selecciona cuantas claves extra necesitas*"
    )

    @staticmethod
    def format_slots_list() -> str:
        lines = []
        for slot in SLOT_OPTIONS:
            lines.append(f"🔑 **{slot.name}** - {slot.stars} ⭐")
        return "\n".join(lines)

    INVOICE_TITLE = "Slots de Claves - {slots_name}"
    INVOICE_DESCRIPTION = "{slots} claves VPN adicionales"

    CONFIRMATION = (
        "✅ **Compra Exitosa**\n\n"
        "🔑 **Slots Adquiridos:** +{slots_added}\n"
        "📊 **Total de Claves:** {new_max_keys}\n"
        "⭐ **Pagado:** {stars} estrellas\n\n"
        "💎 *Ya puedes crear mas claves VPN*"
    )

    ERROR_MAX_KEYS = (
        "❌ **Limite Alcanzado**\n\n"
        "Ya tienes el maximo de claves permitidas.\n\n"
        "💡 *Contacta a soporte si necesitas mas*"
    )
```

---

## Task 4: Actualizar Handler para Compra de Slots

**Files:**
- Modify: `telegram_bot/features/buy_gb/handlers_buy_gb.py`

**Step 1: Agregar show_slots_menu()**

```python
async def show_slots_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        slots_list = BuyGbMessages.Slots.format_slots_list()
        message = BuyGbMessages.Slots.MENU.format(slots_list=slots_list)
        keyboard = BuyGbKeyboards.slots_menu()

        await query.edit_message_text(
            text=message, reply_markup=keyboard, parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error en show_slots_menu: {e}")
        await query.edit_message_text(
            text=BuyGbMessages.Error.SYSTEM_ERROR,
            reply_markup=BuyGbKeyboards.back_to_packages(),
            parse_mode="Markdown",
        )
```

**Step 2: Agregar buy_slots()**

```python
async def buy_slots(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    slots_str = query.data.split("_")[-1]
    slots = int(slots_str)

    try:
        slot_option = None
        for slot in SLOT_OPTIONS:
            if slot.slots == slots:
                slot_option = slot
                break

        if not slot_option:
            await query.edit_message_text(
                text=BuyGbMessages.Error.SYSTEM_ERROR,
                reply_markup=BuyGbKeyboards.back_to_packages(),
                parse_mode="Markdown",
            )
            return

        payload = f"key_slots_{slots}_{user_id}"

        await context.bot.send_invoice(
            chat_id=update.effective_chat.id,
            title=BuyGbMessages.Slots.INVOICE_TITLE.format(slots_name=slot_option.name),
            description=BuyGbMessages.Slots.INVOICE_DESCRIPTION.format(slots=slots),
            payload=payload,
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(f"+{slots} Claves", slot_option.stars)],
        )

        logger.info(f"🔑 Invoice enviado: {slot_option.name} para usuario {user_id}")

    except Exception as e:
        logger.error(f"Error en buy_slots: {e}")
        await query.edit_message_text(
            text=BuyGbMessages.Error.SYSTEM_ERROR,
            reply_markup=BuyGbKeyboards.back_to_packages(),
            parse_mode="Markdown",
        )
```

**Step 3: Modificar pre_checkout_callback() para soportar slots**

Actualizar validacion de payload para manejar tanto `data_package_*` como `key_slots_*`:

```python
async def pre_checkout_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query

    try:
        payload = query.invoice_payload
        parts = payload.split("_")

        if len(parts) >= 3 and parts[0] == "key" and parts[1] == "slots":
            slots = int(parts[2])
            user_id = int(parts[3])
            
            slot_option = None
            for slot in SLOT_OPTIONS:
                if slot.slots == slots:
                    slot_option = slot
                    break
            
            if not slot_option:
                await query.answer(ok=False, error_message="Slots no encontrados")
                return
            
            if query.total_amount != slot_option.stars:
                await query.answer(ok=False, error_message="Monto incorrecto")
                return
            
            await query.answer(ok=True)
            logger.info(f"🔑 Pre-checkout exitoso: +{slots} slots para usuario {user_id}")
            return

        if len(parts) != 4 or parts[0] != "data" or parts[1] != "package":
            await query.answer(ok=False, error_message="Payload invalido")
            return

        package_type_str = parts[2]
        user_id = int(parts[3])

        package_option = None
        for pkg in PACKAGE_OPTIONS:
            if pkg.package_type.value == package_type_str:
                package_option = pkg
                break

        if not package_option:
            await query.answer(ok=False, error_message="Paquete no encontrado")
            return

        if query.total_amount != package_option.stars:
            await query.answer(ok=False, error_message="Monto incorrecto")
            return

        await query.answer(ok=True)
        logger.info(f"📦 Pre-checkout exitoso: {package_option.name} para usuario {user_id}")

    except Exception as e:
        logger.error(f"Error en pre_checkout_callback: {e}")
        await query.answer(ok=False, error_message="Error procesando pago")
```

**Step 4: Modificar successful_payment() para soportar slots**

```python
async def successful_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    payment = update.message.successful_payment

    try:
        payload = payment.invoice_payload
        parts = payload.split("_")

        if len(parts) >= 3 and parts[0] == "key" and parts[1] == "slots":
            slots = int(parts[2])
            telegram_payment_id = payment.telegram_payment_charge_id

            result = await self.data_package_service.purchase_key_slots(
                user_id=user_id,
                slots=slots,
                telegram_payment_id=telegram_payment_id,
                current_user_id=user_id,
            )

            success_message = BuyGbMessages.Slots.CONFIRMATION.format(
                slots_added=result["slots_added"],
                new_max_keys=result["new_max_keys"],
                stars=result["stars_paid"],
            )

            await update.message.reply_text(
                text=success_message,
                reply_markup=BuyGbKeyboards.slots_success(),
                parse_mode="Markdown",
            )

            logger.info(f"🔑 Slots comprados exitosamente: +{slots} para usuario {user_id}")
            return

        if len(parts) != 4:
            logger.error(f"Payload invalido: {payload}")
            await update.message.reply_text(
                text=BuyGbMessages.Error.PAYMENT_FAILED, parse_mode="Markdown"
            )
            return

        package_type_str = parts[2]
        telegram_payment_id = payment.telegram_payment_charge_id

        package = await self.data_package_service.purchase_package(
            user_id=user_id,
            package_type=package_type_str,
            telegram_payment_id=telegram_payment_id,
            current_user_id=user_id,
        )

        package_option = None
        for pkg in PACKAGE_OPTIONS:
            if pkg.package_type.value == package_type_str:
                package_option = pkg
                break

        bonus_text = (
            f" (+{package_option.bonus_percent}% bonus)"
            if package_option and package_option.bonus_percent > 0
            else ""
        )
        expires_at = package.expires_at.strftime("%d/%m/%Y %H:%M")

        success_message = BuyGbMessages.Payment.CONFIRMATION.format(
            package_name=package_option.name if package_option else package_type_str,
            gb_amount=package_option.data_gb if package_option else "N/A",
            bonus_text=bonus_text,
            stars=payment.total_amount,
            expires_at=expires_at,
        )

        await update.message.reply_text(
            text=success_message,
            reply_markup=BuyGbKeyboards.payment_success(),
            parse_mode="Markdown",
        )

        logger.info(f"📦 Paquete comprado exitosamente: {package_type_str} para usuario {user_id}")

    except Exception as e:
        logger.error(f"Error en successful_payment: {e}")
        await update.message.reply_text(
            text=BuyGbMessages.Error.PAYMENT_FAILED, parse_mode="Markdown"
        )
```

**Step 5: Actualizar get_buy_gb_callback_handlers()**

```python
def get_buy_gb_callback_handlers(data_package_service: DataPackageService):
    handler = BuyGbHandler(data_package_service)

    return [
        CallbackQueryHandler(handler.show_packages, pattern="^buy_gb_menu$"),
        CallbackQueryHandler(handler.buy_package, pattern="^buy_package_"),
        CallbackQueryHandler(handler.view_data_summary, pattern="^view_data_summary$"),
        CallbackQueryHandler(handler.show_slots_menu, pattern="^buy_slots_menu$"),
        CallbackQueryHandler(handler.buy_slots, pattern="^buy_slots_"),
    ]
```

---

## Tests

Run: `pytest tests/ -v`

---

## Commit

```bash
git add -A
git commit -m "feat: add key slots purchase with Telegram Stars

- Add SLOT_OPTIONS and purchase_key_slots() in DataPackageService
- Add slots menu and buttons in BuyGbKeyboards
- Add slots messages in BuyGbMessages
- Extend BuyGbHandler with show_slots_menu, buy_slots handlers
- Support both data packages and key slots in payment flow

Closes #122"
```
