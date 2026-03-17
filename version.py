"""
uSipipo VPN Manager - Version Information

This file is the single source of truth for version information.
It should be updated with each release.

Usage:
    from version import __version__, VERSION_INFO
"""

__version__ = "3.11.0"

VERSION_INFO = {
    "major": 3,
    "minor": 11,
    "patch": 0,
    "release": "2026-03-17",
    "codename": "Android APK Removal",
}

VERSION_HISTORY = """
v3.11.0 (2026-03-17) - Android APK Removal
  - Complete removal of Android APK application from repository
  - Removed android_app/ directory (Kivy + KivyMD)
  - Removed infrastructure/api/android/ REST API endpoints
  - Removed Android CI/CD workflow and documentation
  - Repository now contains only Telegram Bot + Mini App Web
  - Updated QWEN.md, README.md, pyproject.toml
  - Mini App Web fully intact with 27 routes

v3.9.0 (2026-03-11) - Mini App Payment System
  - Mini App payment confirmation system
  - CryptoPaymentService injection with request session
  - Fix admin tickets navigation back button
  - Fix navigation from tickets menu to help center
  - Fix navigation from ticket detail to main menu
  - Resolve CI linting errors

v3.8.1 (2026-03-01) - Release Cleanup
  - Resolve CHANGELOG.md merge conflicts
  - Release cleanup

v3.8.0 (2026-03-01) - Pay-as-you-go VPN Consumption
  - Complete VPN integration for consumption billing
  - Conditional consumption button in VPN keys menu
  - Consumption mode cancellation with debt validation
  - Updated consumption rate from $0.45 to $0.25 per GB
  - Redesigned key management menu with Option B
  - Removed Settings, Statistics, and Suspend buttons from WireGuard menu
  - Automatic crypto order cancellation and wallet reuse
  - Debt check before creating VPN keys
  - Key unblocking on payment processing
  - Key blocking on billing cycle close
  - VPN Server Management Center
  - Ghost key cleanup job
  - VpnInfrastructureService with enable/disable methods

v3.7.0 (2026-02-28) - Transaction History
  - Redesigned operations menu with better visual layout
  - New "📜 History" button in operations menu
  - Transaction status with emojis
  - Pagination for transaction history
  - Paginated methods in CryptoOrderRepository

v3.6.0 (2026-02-28) - Diagnostics & Logging
  - Diagnostics section with real-time logs viewer for admin
  - Comprehensive logging across all bot features
  - Remove key deletion option for users
  - Restrict key deletion endpoint to admins only
  - Remove delete button from miniapp and VPN key actions
  - Add days since join info in /info command
  - Order expiration and wallet reuse implementation
  - TronDealer HTTP client error handling improvements
  - Mini App payment logging and error handling
  - Admin ticket system fixes

v3.5.0 (2026-02-27) - Bonus & Referral System
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
