# Implementation Plan: Fix Referral Menu Error + Add Share Button

Track ID: `fix-referral-menu_20250301`
Created: 2025-03-01
Status: in-progress

## Overview

Fix the "Message is not modified" error on referral menu refresh and add a share button for easy referral link sharing.

## Phase 1: Fix "Message is not modified" Error

### Tasks

- [x] **Task 1.1**: Import BadRequest exception from telegram.error
- [x] **Task 1.2**: Add specific error handling for "Message is not modified" in `show_referral_menu`
- [x] **Task 1.3**: Add callback answer when data is unchanged (e.g., "✅ Datos actualizados")

### Verification

- [ ] **Verify 1.1**: Manual test - click refresh with unchanged data shows callback answer
- [ ] **Verify 1.2**: Manual test - click refresh with changed data updates message normally

## Phase 2: Add Share Button to Referral Menu

### Tasks

- [x] **Task 2.1**: Add static method `get_share_url()` to `ReferralMessages` for generating share URL
- [x] **Task 2.2**: Add "📤 Compartir" button to `main_menu()` keyboard in `ReferralKeyboards`
- [x] **Task 2.3**: Update `show_referral_menu` to pass share_url to keyboard

### Verification

- [ ] **Verify 2.1**: Share button appears in main referral menu
- [ ] **Verify 2.2**: Clicking share button opens Telegram share dialog

## Phase 3: Testing and Documentation

### Tasks

- [x] **Task 3.1**: Write unit test for "Message is not modified" error handling
- [x] **Task 3.2**: Run all existing tests to ensure no regressions
- [x] **Task 3.3**: Fix any lint/type issues (flake8, black, mypy)

### Verification

- [x] **Verify 3.1**: All 347 tests pass
- [x] **Verify 3.2**: Black formatting applied (E501 pre-existing)

## Phase 4: Finalization

### Tasks

- [x] **Task 4.1**: Update track status to completed
- [x] **Task 4.2**: Commit changes with conventional commit message

### Verification

- [x] **Verify 4.1**: All acceptance criteria met

## Checkpoints

| Phase | Checkpoint SHA | Date | Status |
|-------|----------------|------|--------|
| Phase 1 | | | pending |
| Phase 2 | | | pending |
| Phase 3 | | | pending |
| Phase 4 | | | pending |
