# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v3.9.0] - 2026-03-11

### Features
- **Mini App Payment System** - Complete crypto payment integration for Mini App
  - Payment confirmation for Mini App purchases
  - CryptoPaymentService injection with request session
  - Secure payment flow with transaction tracking

### Bug Fixes
- **Admin Tickets** - Fix navigation back button in ticket management
- **Navigation** - Fix navigation from tickets menu to help center
- **Navigation** - Fix navigation from ticket detail to main menu
- **CI/CD** - Resolve linting errors in CI pipeline

### Technical
- Improved error handling in TronDealer API client
- Code formatting and line length fixes
- Import organization and cleanup

## [v3.8.1] - 2026-03-01

### Bug Fixes
- Resolve CHANGELOG.md merge conflicts
- Release cleanup

## [v3.8.0] - 2026-03-01

### Features
- **Pay-as-you-go VPN Consumption** - Complete VPN integration for consumption billing
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

### Bug Fixes
- Show inactive keys in admin panel
- Handle 'no text in message' error gracefully
- Replace obsolete VpnKeysKeyboards.main_menu with CommonKeyboards.main_menu
- Reorder handlers to prioritize ConversationHandler and fix cancellation message
- Filter inactive keys from admin server key list
- Telegram callback_data 64 bytes limit in admin VPN handlers
- Fix key deletion and Markdown parsing errors
- Pass billing_service to KeyManagementHandler for consumption button
- WireGuard usage always shows 0.0GB
- Consumption mode cancellation without debt not blocking keys
- Use billing as source of truth for cancellation
- Register ConsumptionInvoiceService in dependency container
- Register consumption handlers in handler_initializer

### Chores
- Cleanup development files and update scripts
- Add merge to main script
- Remove completed markdown standardization track files

## [v3.7.0] - 2026-02-28

### Features
- **Transaction History** - Complete crypto transaction history
  - Redesigned operations menu with better visual layout
  - New "📜 History" button in operations menu
  - Transaction status with emojis (⏳ Pending, ✅ Completed, ❌ Failed, ⏰ Expired)
  - Pagination for transaction history (10 per page)
  - Paginated methods in CryptoOrderRepository

### Technical
- Fix mypy type errors in dependency injection
- Unit tests for new handlers and keyboards
- Cleanup unused imports

## [v3.6.0] - 2026-02-28

### Features
- **Diagnostics Section** - Real-time logs viewer for admin (#234)
- **Comprehensive Logging** - Logging across all bot features (#233)

### Changed
- Remove key deletion option for users (#229)
- Restrict key deletion endpoint to admins only
- Remove delete button from miniapp
- Remove delete button from vpn key actions keyboard
- Update messages to remove delete key references
- Remove delete key handler for users
- Add days since join info and key management improvements
- Show days since join in /info command

### Bug Fixes
- Implement order expiration and wallet reuse
- 'There is no text in the message to edit' error in handlers
- Resolve invalid escape sequence warnings
- Resolve LSP type error in show_buy_slots_menu
- Improve TronDealer HTTP client error handling and logging
- Create user in DB when authenticating from Mini App (#231)
- Improve logging and error handling in Mini App payments (#231)
- Validate product_type and product_id in payments (#230)
- Admin ticket response not working + Missing close ticket button
- Improve key limit reached message
- Preserve created_at when loading existing users

## [v3.5.0] - 2026-02-27

### Features
- **Bonus & Referral System**
  - User bonus system with welcome, loyalty and quick renewal bonuses
  - Referral system with +5GB bonus for referred user purchases
  - FAQ button fixes with bonus information
  - Updated payment flow and tests for buy GB feature
  - Updated key slot pricing

## [v3.4.0] - 2026-02-27

### Features
- **Business Model Refactor**
  - Reduced data limit to 5GB per key (from 10GB)
  - One key per server type limit (Outline/WireGuard)
  - Crypto payments for key slots (USDT/BSC)
  - Payment QR codes (EIP-681 format)
  - Order expiration notifications (30 min timeout)
  - Transaction history with expired orders
  - 42 tests passing, flake8 clean

## [v3.3.0] - 2026-02-26

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

## [v3.2.0] - 2026-02-27

### Features
- **Transaction System**
  - Transaction repository with balance tracking
  - Crypto payment improvements
  - Code quality fixes (black, isort)
  - 20 commits ahead of main

## [v3.1.0] - 2026-02-25

### Features
- **Mini App Enhanced**
  - Privacy Policy page for Telegram Mini App compliance
  - User Profile page with statistics and transaction history
  - Settings page with preferences and support options
  - Dropdown navigation from header avatar
  - CCPA rights for California users
  - 25+ new tests for Mini App endpoints

## [v3.0.0] - 2026-02-25

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

## [v2.1.0] - 2026-02-24

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

## [v2.0.0] - 2026-02-20

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

## [v1.0.0] - 2026-01-15

### Added
- Initial release
- Basic Telegram bot functionality
- WireGuard VPN management
- User management system
