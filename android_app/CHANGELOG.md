# Changelog - uSipipo VPN Android APK

All notable changes to the Android APK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Initial release structure for Android APK
- OTP authentication flow with Telegram integration
- Cyberpunk-themed UI with KivyMD
- Secure JWT storage using keyring
- VPN key management interface
- Data package purchase flow
- Support ticket system

### Changed
- Moved CI/CD workflow to root `.github/workflows/` for proper GitHub Actions execution

### Fixed
- Buildozer configuration for CI/CD pipeline

---

## [1.0.0] - 2026-03-14

### Added
- **Initial Release** of uSipipo VPN Android APK
- **Authentication System**:
  - OTP login via Telegram
  - Secure JWT token storage
  - Automatic token refresh
- **Dashboard**:
  - User profile summary
  - Active VPN keys overview
  - Quick access to features
- **VPN Management**:
  - View WireGuard and Outline keys
  - Connection status indicators
  - QR code display for easy import
- **Data Packages**:
  - Browse available packages (10GB - 100GB)
  - Purchase flow with crypto payments
  - Transaction history
- **Support System**:
  - Create support tickets
  - View ticket history
  - Real-time message updates
- **UI/UX**:
  - Cyberpunk theme with neon colors
  - Responsive layouts for all screen sizes
  - Smooth animations and transitions
  - Dark mode optimized
- **Offline Support**:
  - Local data caching
  - Session persistence
  - Offline mode indicators

### Technical
- Built with Kivy 2.3.1 and KivyMD 1.2.0
- Python 3.13+
- Async HTTP client with httpx
- Secure storage with keyring
- CI/CD pipeline with GitHub Actions
- Automated APK build (debug & release)
- Unit tests with pytest

---

## Version History

| Version | Release Date | Description |
|---------|--------------|-------------|
| 1.0.0 | 2026-03-14 | Initial Release |

---

## Upcoming Features (Roadmap)

### v1.1.0
- [ ] Biometric authentication (fingerprint/face)
- [ ] Push notifications for ticket updates
- [ ] Connection speed test
- [ ] Server selection interface

### v1.2.0
- [ ] Automatic connection on app start
- [ ] Connection statistics and charts
- [ ] Data usage monitoring
- [ ] Widget for home screen

### v2.0.0
- [ ] Multi-account support
- [ ] Split tunneling configuration
- [ ] Custom DNS settings
- [ ] Kill switch implementation

---

## Known Issues

- Build time in CI can take 20-30 minutes for full APK build
- First app launch may be slower due to initial data loading

---

## Support

- **Telegram Bot**: @usipipo_bot
- **Email**: soporte@usipipo.com
- **Documentation**: [README.md](README.md)
