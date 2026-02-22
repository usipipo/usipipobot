# Fix MarkdownV2 Escaping for Outline Key Creation

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the MarkdownV2 parsing error when creating Outline VPN keys by properly escaping special characters.

**Architecture:** Use the existing `escape_markdown()` utility function to properly escape all MarkdownV2 special characters before sending messages with `parse_mode="MarkdownV2"`.

**Tech Stack:** Python, python-telegram-bot, MarkdownV2

**Issue:** #136

---

## Root Cause Analysis

### Problem
When creating an Outline VPN key, the bot throws:
```
Can't parse entities: character '!' is reserved and must be escaped with the preceding '\'
```

### Location
`telegram_bot/features/vpn_keys/handlers_vpn_keys.py:170-186`

### Why It Fails
1. Caption uses `parse_mode="MarkdownV2"`
2. `VpnKeysMessages.Success.KEY_CREATED_WITH_DATA` contains unescaped characters: `!`, `.`, `-`, `(`, `)`
3. Manual escaping only handles 4 characters (`*`, `_`, `[`, `]`)
4. MarkdownV2 requires escaping 18+ characters

### Solution
Use `escape_markdown()` from `utils/telegram_utils.py` which properly escapes all MarkdownV2 special characters.

---

### Task 1: Fix Outline Key Creation Caption

**Files:**
- Modify: `telegram_bot/features/vpn_keys/handlers_vpn_keys.py:148-188`

**Step 1: Add import for escape_markdown**

Add import at the top of the file:
```python
from utils.telegram_utils import escape_markdown
```

**Step 2: Replace manual escaping with escape_markdown function**

Replace lines 148-178 with properly escaped caption:

```python
if key_type == "outline":
    escaped_data = escape_markdown(new_key.key_data)
    
    caption = escape_markdown(
        VpnKeysMessages.Success.KEY_CREATED_WITH_DATA.format(
            type="OUTLINE", name=key_name, data_limit=new_key.data_limit_gb
        )
    )
    caption += f"\n\nCopia el siguiente código en tu aplicación Outline:\n```\n{escaped_data}\n```"

    with open(qr_path, "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption=caption,
            parse_mode="MarkdownV2",
            reply_markup=VpnKeysKeyboards.main_menu(is_admin=is_admin),
        )
```

**Step 3: Run tests**

Run: `pytest tests/ -v -k vpn`
Expected: All tests pass

**Step 4: Commit**

```bash
git add telegram_bot/features/vpn_keys/handlers_vpn_keys.py
git commit -m "fix: escape MarkdownV2 characters in Outline key creation caption

Fixes #136

- Use escape_markdown() utility for proper MarkdownV2 escaping
- Remove manual character-by-character escaping
- Ensures all special chars (!, ., -, etc.) are properly escaped"
```

---

### Task 2: Verify No Other MarkdownV2 Issues

**Files:**
- Check: All files using `parse_mode="MarkdownV2"`

**Step 1: Search for other MarkdownV2 usages**

Run: `grep -r "MarkdownV2" --include="*.py" telegram_bot/`

**Step 2: Verify each usage has proper escaping**

Current finding: Only `handlers_vpn_keys.py:185` uses MarkdownV2, which is fixed in Task 1.

**Step 3: Commit verification (if changes needed)**

```bash
git commit -m "docs: verify no other MarkdownV2 issues exist"
```

---

## Testing Checklist

- [ ] Create Outline key - should succeed without parse errors
- [ ] Create WireGuard key - should still work
- [ ] Check that special characters in key data are properly escaped
- [ ] Verify message formatting is preserved (bold, etc.)
