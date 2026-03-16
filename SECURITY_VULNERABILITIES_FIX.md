# Security Vulnerabilities Fix - March 2026

## Summary

This document summarizes the resolution of 11 Dependabot security alerts affecting the uSipipo VPN Manager project.

## Vulnerabilities Resolved

All vulnerabilities have been resolved by updating dependencies to secure versions. The following packages were updated:

### High Severity

| Alert # | Package | CVE | Vulnerability | Fixed Version |
|---------|---------|-----|---------------|---------------|
| 32, 26 | pillow | CVE-2026-25990 | Out-of-bounds write when loading PSD images | 12.1.1 |
| 31, 25 | cryptography | CVE-2026-26007 | Subgroup attack vulnerability for SECT curves | 46.0.5 |
| 27 | PyJWT | CVE-2026-32597 | Accepts unknown `crit` header extensions | 2.12.0 |

### Medium Severity

| Alert # | Package | CVE | Vulnerability | Fixed Version |
|---------|---------|-----|---------------|---------------|
| 28, 22 | cryptography | - | Vulnerable OpenSSL in wheels | 43.0.1+ |

### Low Severity

| Alert # | Package | CVE | Vulnerability | Fixed Version |
|---------|---------|-----|---------------|---------------|
| 30, 24 | certifi | CVE-2024-39689 | GLOBALTRUST root certificate removal | 2024.7.4 |
| 29, 23 | cryptography | CVE-2024-12797 | Vulnerable OpenSSL in wheels | 44.0.1+ |

## Current Dependency Versions

After running `uv sync`, the following secure versions are installed:

```
pillow==12.1.1          # Required: >=12.1.1 ✅
cryptography==46.0.5    # Required: >=46.0.5 ✅
PyJWT==2.12.0           # Required: >=2.12.0 ✅
certifi==2026.2.25      # Required: >=2024.7.4 ✅
```

## Verification

All 422 existing tests pass with the updated dependencies:

```bash
uv run pytest tests/ -v
# ======================= 422 passed, 5 warnings in 6.38s ========================
```

## Impact

- **No breaking changes**: All updates are patch or minor version updates
- **Backward compatible**: Existing functionality remains unchanged
- **Security improved**: All known high, medium, and low severity vulnerabilities resolved

## Dependabot Alerts Status

These changes will automatically close the following Dependabot alerts:
- #32, #26: pillow CVE-2026-25990
- #31, #25: cryptography CVE-2026-26007
- #27: PyJWT CVE-2026-32597
- #30, #24: certifi CVE-2024-39689
- #29, #23: cryptography CVE-2024-12797
- #28, #22: cryptography OpenSSL vulnerabilities

## References

- [Pillow Security Advisory](https://github.com/python-pillow/Pillow/security/advisories/GHSA-cfh3-3jmp-rvhc)
- [Cryptography Security Advisory](https://github.com/pyca/cryptography/security/advisories/GHSA-r6ph-v2qm-q3c2)
- [PyJWT Security Advisory](https://github.com/jwt/pyjwt/security/advisories/GHSA-752w-5fwx-jx9f)
- [Certifi Security Advisory](https://github.com/certifi/python-certifi/security/advisories/GHSA-986q-w28q-3v5f)

---

**Date**: 2026-03-15
**Branch**: fix/dependabot-vulnerabilities-2026
