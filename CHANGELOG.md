<<<<<<< HEAD
[0;32m[INFO][0m FASE 4: Generando changelog...
## [v3.6.0] - 2026-03-01

### Features
- conditional consumption button in VPN keys menu
- implementar cancelación del modo de consumo (#cancel-consumption-mode_20250301)
- actualizar tarifa de consumo de $0.45 a $0.25 por GB
- rediseñar menú de gestión de llaves con Opción B
- eliminar botones Ajustes, Estadísticas y Suspender del menú WireGuard
- registro de servicios de consumo billing en contenedor DI
- cancelación automática de órdenes crypto y reutilización de wallets
- complete VPN integration for pay-as-you-go
- check pending debt before creating VPN keys
- integrate key unblocking in process payment
- integrate key blocking in close billing cycle
- register ConsumptionVpnIntegrationService in DI container
- implement route_usage_to_billing method
- implement unblock_user_keys method
- implement block_user_keys method for ConsumptionVpnIntegrationService
- implement check_can_create_key method
- add ConsumptionVpnIntegrationService skeleton
- Fase 5 VPN Server Management Center + Pay-as-you-go consumption
- add ghost key cleanup job
- add VPN server management handlers
- create VpnInfrastructureService
- add disable_key() and enable_key() methods
- add enable_peer() method
- add disable_peer() method
- Phase 6 - Cron Job Script
- Phase 4 - Telegram Handlers
- Phase 3 - Application Services
- Complete Phase 2 - PostgresConsumptionInvoiceRepository
- Phase 2 - Infrastructure Layer (Models & Config)
- Phase 1 - Domain Layer entities and interfaces
- redesign operations menu and add transaction history
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
- show inactive keys in admin panel
- handle 'no text in message' error gracefully
- replace obsolete VpnKeysKeyboards.main_menu with CommonKeyboards.main_menu
- reordena handlers para priorizar ConversationHandler y corrige mensaje de cancelación (#245)
- filter inactive keys from admin server key list (#244)
- telegram callback_data 64 bytes limit in admin VPN handlers
- corrige errores en eliminación de claves y parsing Markdown
- pass billing_service to KeyManagementHandler for consumption button (#243)
- WireGuard usage always shows 0.0GB (#242)
- cancelación modo consumo sin deuda no bloquea claves (#241)
- usar billing como fuente de verdad para cancelación (#240)
- registrar ConsumptionInvoiceService en contenedor de dependencias
- registrar handlers de consumo en handler_initializer (#239)
- include changelog in annotated tag message
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
- cleanup development files and update scripts
- add merge to main script
- remove completed markdown standardization track files

### Other Changes
- add tests for spinner error handling
- update plan - wireguard usage bug fix completed
- update plan.md with Task 5.4 completion - conditional consumption button
- cancelación modo consumo desde feat/cancel-consumption-mode
- eliminar botones Ajustes, Estadísticas y Suspender del menú WireGuard
- cancelación automática de órdenes crypto y reutilización de wallets
- improve consumption billing and invoice services
- update track status after VPN integration completion
- fix flake8 line length in ghost_key_cleanup_job
- complete integration testing
- mark transactions-menu track as completed
- fix linting issues in payment files
- actualizar plan.md con checkpoint SHA
- estandarizar parse_mode a Markdown en todos los mensajes
- add migration notes and plan for bonus system columns (#223)

=======
>>>>>>> develop
## [v3.6.0] - 2026-02-28

### Features
- Rediseño del menú de operaciones con mejor layout visual
- Nuevo botón "📜 Historial" en menú de operaciones
- Implementación de historial completo de transacciones crypto
- Visualización de estados con emojis (⏳ Pendiente, ✅ Completada, ❌ Fallida, ⏰ Expirada)
- Paginación para historial de transacciones (10 por página)
- Métodos paginados en CryptoOrderRepository (`get_by_user_paginated`, `count_by_user`)

### Technical
- Corrección de errores de tipo mypy en inyección de dependencias
- Tests unitarios para nuevos handlers y keyboards
- Limpieza de imports no utilizados

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
