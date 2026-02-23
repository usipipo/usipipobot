# Fix MarkdownV2 Formatting Bug in Outline Key Creation

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix broken Markdown formatting in Outline VPN key creation message so bold text renders correctly.

**Architecture:** Create a selective escape function that preserves Markdown formatting markers while escaping user-provided content. This approach separates static template formatting from dynamic user data.

**Tech Stack:** Python, python-telegram-bot, MarkdownV2

**Issue:** #141

---

## Root Cause Analysis

### Problem
The `escape_markdown()` function escapes ALL special characters, including the `**` markers intended for bold formatting. This causes the message to display literal asterisks instead of formatted text.

### Location
`telegram_bot/features/vpn_keys/handlers_vpn_keys.py:148-166`

### Why It Fails
1. `escape_markdown()` escapes `*` → `\*`
2. Bold markers `**text**` become `\*\*text\*\*`
3. Telegram renders literal `**` instead of bold

### Solution
1. Escape ONLY user-provided data (key_name, key_data)
2. Keep template formatting markers unescaped
3. Use the existing template with escaped dynamic values

---

### Task 1: Fix Outline Key Creation Caption

**Files:**
- Modify: `telegram_bot/features/vpn_keys/handlers_vpn_keys.py:148-166`

**Step 1: Modify the caption building logic**

Replace lines 148-157 with properly escaped dynamic values:

```python
if key_type == "outline":
    escaped_name = escape_markdown(key_name)
    escaped_data = escape_markdown(new_key.key_data)
    
    caption = (
        VpnKeysMessages.Success.KEY_CREATED_WITH_DATA.format(
            type="OUTLINE", name=escaped_name, data_limit=new_key.data_limit_gb
        )
        + f"\n\nCopia el siguiente código en tu aplicación Outline:\n```\n{escaped_data}\n```"
    )

    with open(qr_path, "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption=caption,
            parse_mode="MarkdownV2",
            reply_markup=VpnKeysKeyboards.main_menu(is_admin=is_admin),
        )
```

**Step 2: Update the message template in messages_vpn_keys.py**

Modify `telegram_bot/features/vpn_keys/messages_vpn_keys.py:62-68`:

```python
KEY_CREATED_WITH_DATA = (
    "✅ \\*\\*¡Llave creada exitosamente\\!\\*\\*\n\n"
    "📡 \\*\\*Protocolo:\\*\\* {type}\n"
    "🔑 \\*\\*Nombre:\\*\\* {name}\n"
    "📊 \\*\\*Datos disponibles:\\*\\* {data_limit:.1f} GB\n\n"
    "Sigue las instrucciones para conectarte\\."
)
```

**Step 3: Run tests**

Run: `pytest tests/ -v -k vpn`
Expected: All tests pass

**Step 4: Manual verification**

Create an Outline key via Telegram bot and verify:
- Bold text renders correctly
- User-provided name displays properly
- QR code and ss:// link work

**Step 5: Commit**

```bash
git add telegram_bot/features/vpn_keys/handlers_vpn_keys.py telegram_bot/features/vpn_keys/messages_vpn_keys.py
git commit -m "fix: preserve MarkdownV2 formatting in Outline key creation message

Fixes #141

- Escape only user-provided data, not template formatting
- Update message template with properly escaped MarkdownV2 characters
- Bold text now renders correctly in Telegram"
```

---

### Task 2: Verify WireGuard Message Format

**Files:**
- Check: `telegram_bot/features/vpn_keys/handlers_vpn_keys.py:167-191`

**Step 1: Verify WireGuard still uses parse_mode='Markdown'**

The WireGuard section at lines 167-191 uses `parse_mode="Markdown"` (not V2), so it should work correctly.

**Step 2: Confirm no changes needed for WireGuard**

No changes needed - WireGuard uses regular Markdown which doesn't have the strict escaping requirements of MarkdownV2.

---

## Testing Checklist

- [ ] Create Outline key - bold text renders correctly
- [ ] Create Outline key with special characters in name - properly escaped
- [ ] Create WireGuard key - still works correctly
- [ ] QR code generates properly for both types
- [ ] ss:// link works in Outline client

## Files Changed

1. `telegram_bot/features/vpn_keys/handlers_vpn_keys.py` - Fix caption building
2. `telegram_bot/features/vpn_keys/messages_vpn_keys.py` - Escape template for MarkdownV2
