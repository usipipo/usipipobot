"""
uSipipo VPN Manager - Version Information

This file is the single source of truth for version information.
It should be updated with each release.

Usage:
    from version import __version__, VERSION_INFO
"""

__version__ = "3.4.0"

VERSION_INFO = {
    "major": 3,
    "minor": 4,
    "patch": 0,
    "release": "2026-02-27",
    "codename": "Bonus & Referral System",
}

VERSION_HISTORY = """
v3.4.0 (2026-02-27) - Bonus & Referral System
  - User bonus system with welcome, loyalty and quick renewal bonuses
  - Referral system with +5GB bonus for referred user purchases
  - FAQ button fixes with bonus information
  - Updated payment flow and tests for buy GB feature
  - Updated key slot pricing

v3.3.0 (2026-02-26) - Business Model Refactor
  - Reduced data limit to 5GB per key (from 10GB)
  - One key per server type limit (Outline/WireGuard)
  - Crypto payments for key slots (USDT/BSC)
  - Payment QR codes (EIP-681 format)
  - Order expiration notifications (30 min timeout)
  - Transaction history with expired orders
  - 42 tests passing, flake8 clean

v3.2.0 (2026-02-27) - Transaction System
  - Transaction repository with balance tracking
  - Crypto payment improvements
  - Code quality fixes (black, isort)
  - 20 commits ahead of main

v3.1.0 (2026-02-25) - Mini App Enhanced
  - Privacy Policy page for Telegram Mini App compliance
  - User Profile page with statistics and transaction history
  - Settings page with preferences and support options
  - Dropdown navigation from header avatar
  - CCPA rights for California users
  - 25+ new tests for Mini App endpoints

v3.0.0 (2026-02-25) - Mini App
  - Telegram Mini App Web with cyberpunk design
  - Tron Dealer Webhook API for crypto payments
  - DuckDNS + Caddy integration (ngrok replacement)
  - Ticket system for user support
  - Key slots purchase with Telegram Stars
  - Security fixes and 50+ bug fixes

v2.1.0 (2026-02-24)
  - Mini App Web interface beta
  - Improved logging and error handling

v2.0.0 (2026-02-20)
  - Complete refactor to Clean Architecture
  - PostgreSQL database integration
  - Telegram Stars payment integration
  - WireGuard and Outline VPN support

v1.0.0 (2026-01-15)
  - Initial release
  - Basic Telegram bot functionality
"""
