# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **CRITICAL**: WireGuard metrics error now shows detailed error message instead of empty string (#178)
  - Improved error handling in `WireGuardClient.get_usage()` to capture actual error messages
  - Added `exc_info=True` to logger for full stack trace
- Added caching with TTL (10 seconds) to `WireGuardClient.get_usage()` to prevent race conditions during sync
  - Implemented async locking to prevent concurrent `wg show` commands
  - Cache reduces unnecessary WireGuard API calls during sync job
- Added favicon to Mini App web to prevent 404 errors (#178)
  - Created SVG favicon in `miniapp/static/favicon.svg`
  - Added `/favicon.ico` endpoint in FastAPI server

### Added
- Comprehensive test suite for WireGuard client with 7 new test cases
  - Tests for caching functionality
  - Tests for error handling
  - Tests for edge cases (empty exceptions, invalid data)

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
