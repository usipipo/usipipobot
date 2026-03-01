# Fix Referral Menu: Error on Refresh + Add Share Button

## Overview

Fix the "Message is not modified" error that occurs when users click the refresh button in the referral menu without any stats having changed. Additionally, add a "Share" button to allow users to easily share their referral link with other Telegram users.

## Functional Requirements

### FR-1: Handle "Message is not modified" Error Gracefully

The referral menu currently throws an error when users click the refresh button but the referral stats (credits, total referrals) haven't changed since the last refresh. This happens because Telegram's API rejects edit operations when the new content is identical to the current content.

- **Acceptance**: When a user clicks refresh and the data hasn't changed, the bot should acknowledge the action with a brief callback answer (e.g., "✅ Datos actualizados") instead of throwing an error.

### FR-2: Add Share Button to Referral Menu

Add a new button "📤 Compartir" to the referral menu that allows users to share their referral link with other Telegram users. The button should use Telegram's share URL feature to open the share dialog with a pre-filled message.

- **Acceptance**: The share button should open Telegram's native share dialog with a pre-filled message containing the referral link and a brief description.

## Non-Functional Requirements

### NFR-1: User Experience

The fix should provide immediate visual feedback to the user when refreshing, even if data hasn't changed.

- **Target**: Callback answer displayed within 500ms
- **Verification**: Manual testing of refresh button

### NFR-2: Code Maintainability

The error handling should be clean and not add unnecessary complexity to the handler.

- **Target**: Single try-catch block for the specific Telegram error
- **Verification**: Code review

## Acceptance Criteria

- [ ] Clicking refresh button with unchanged data shows a friendly callback answer instead of an error
- [ ] Clicking refresh button with changed data updates the message normally
- [ ] Share button is visible in the main referral menu
- [ ] Share button opens Telegram share dialog with pre-filled message
- [ ] All existing tests pass
- [ ] New tests cover the error handling scenario

## Scope

### In Scope

- Fix "Message is not modified" error in `show_referral_menu` handler
- Add share button to `ReferralKeyboards.main_menu()`
- Create share URL with pre-filled message
- Add appropriate error handling
- Write/update tests

### Out of Scope

- Changes to referral logic or credit calculations
- UI/UX redesign of the referral menu
- New referral features beyond sharing

## Dependencies

### Internal

- `telegram_bot/features/referral/handlers_referral.py`
- `telegram_bot/features/referral/keyboards_referral.py`
- `telegram_bot/features/referral/messages_referral.py`

### External

- python-telegram-bot library

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Share URL format changes in Telegram API | Low | Use standard t.me share format |
| BadRequest exception handling catches wrong errors | Low | Check error message string specifically |

## Open Questions

- [x] What should the share message say? - "¡Usa mi código de referido y obtén créditos gratis para uSipipo VPN! {link}"
