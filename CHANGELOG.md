[0;32m[INFO][0m FASE 4: Generando changelog...
## [v3.5.0] - 2026-02-28

### Features
- Add Diagnostics section with real-time logs viewer for admin (#234)
- implement comprehensive logging across all bot features (#233)
- add comprehensive logging to referral_service.py
- add comprehensive logging to VpnService
- add comprehensive logging to basic commands handlers
- add comprehensive logging to key management handlers
- add logs to VPN keys handlers
- add logs to operations handlers
- add comprehensive logs to referral handlers
- remove key deletion option for users (#229)
- restrict key deletion endpoint to admins only
- remove delete button and function from miniapp
- remove delete button from vpn key actions keyboard
- update messages to remove delete key references
- remove delete key handler for users
- remove delete button from user key management keyboard
- add days since join info and key management improvements
- show days since join in /info command

### Bug Fixes
- implement order expiration and wallet reuse
- 'There is no text in the message to edit' error in handlers
- resolve invalid escape sequence warnings
- resolve LSP type error in show_buy_slots_menu
- improve TronDealer HTTP client error handling and logging
- Crear usuario en BD al autenticar desde Mini App (#231)
- Mejorar logging y manejo de errores en pagos Mini App (#231)
- validación product_type y product_id en pagos (#230)
- Admin ticket response not working + Missing close ticket button
- Mejora mensaje de límite de claves alcanzado
- preserve created_at when loading existing users

### Chores
- remove completed markdown standardization track files

### Other Changes
- fix linting issues in payment files
- actualizar plan.md con checkpoint SHA
- estandarizar parse_mode a Markdown en todos los mensajes
- add migration notes and plan for bonus system columns (#223)

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.3.0] - 2026-02-26

### Added
- **Crypto Payments for Slots** - Buy key slots with USDT (BSC)
  - Payment method selection (Stars or Crypto)
  - QR code generation for easy wallet scanning
  - Automatic slot delivery after payment confirmation
- **Payment QR Codes** - EIP-681 format for wallet compatibility
  - BSC/BEP20 USDT support
  - Auto-cleanup of old QR files
- **Order Expiration Notifications** - Users notified when orders expire
  - 30-minute timeout for crypto payments
  - Automatic order cancellation and status update
  - Transaction history including expired orders

### Changed
- **Free Plan Data Limit** - Reduced from 10GB to 5GB per key
  - Total free data remains 10GB (5GB x 2 keys)
- **One Key Per Server Type** - Users limited to 1 Outline and 1 WireGuard key
  - Enforced at key creation time
  - Clear error messages for users

## [3.0.0] - 2026-02-25

### Added
- **Telegram Mini App Web** - Complete web interface with cyberpunk design
  - Dashboard with data usage visualization
  - Key management interface (create, rename, download, toggle)
  - Purchase flow for data packages
  - Authentication via Telegram Web App SDK
  - FAB button with quick actions
- **Tron Dealer Webhook API** - Cryptocurrency payment support
  - Secure webhook endpoint with layered security
  - Rate limiting and IP validation
  - HMAC signature verification
  - Transaction tracking and status management
- **DuckDNS + Caddy Integration** - Replaced ngrok for tunneling
  - Dynamic DNS updates
  - Automatic HTTPS with Caddy
  - No more ngrok tunnel conflicts
- **Ticket System** - User support tickets
  - Create tickets from bot
  - Admin ticket management
  - Status tracking and responses
- **Key Slots Purchase** - Buy additional VPN key slots with Telegram Stars

### Changed
- Removed VIP logic from services and UI
- Removed balance_stars and total_deposited fields
- Refactored admin panel with improved UX
- Enhanced operations flow with credits and shop redesign
- Improved user profile with history view

### Fixed
- **SECURITY**: Patched privilege escalation vulnerability in admin panel
- WireGuard subprocess NotImplementedError during sync job (#183)
- WireGuard metrics error showing empty string (#178)
- FAB button CSS visual issues in Mini App
- MarkdownV2 escaping in ticket handlers
- Missing admin_tickets callback handler
- VPN key creation blocked by ticket handler (#140)
- Multiple duplicate handler fixes
- Mobile design and button bugs (#152)
- Various LSP/mypy type errors (449 fixes)

### Security
- Added webhook security service with multiple validation layers
- Implemented rate limiting middleware
- Removed hardcoded webhook secrets from documentation

### Removed
- Obsolete docs/plans/ directory from version control
- ngrok integration (replaced with DuckDNS + Caddy)
- Unused GROQ variables from configuration
- Obsolete game, referral announcer, broadcast features

## [2.1.0] - 2026-02-24

### Added
- Mini App Web interface for Telegram
  - Dashboard with data usage metrics
  - Key management interface
  - Purchase flow for data packages
  - Authentication via Telegram Web App SDK

### Changed
- Improved logging throughout the application
- Enhanced error handling in VPN service layer

### Fixed
- Various minor bug fixes and performance improvements

## [2.0.0] - 2026-02-20

### Added
- Complete refactor to Clean Architecture
- PostgreSQL database integration
- Telegram Stars payment integration
- WireGuard and Outline VPN support
- Data package system
- Referral system
- Admin center

### Changed
- Migrated from SQLite to PostgreSQL
- Implemented dependency injection with Punq
- Added comprehensive test coverage

## [1.0.0] - 2026-01-15

### Added
- Initial release
- Basic Telegram bot functionality
- WireGuard VPN management
- User management system
