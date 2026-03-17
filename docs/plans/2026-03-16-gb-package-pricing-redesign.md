# GB Package Pricing Redesign - Value-Based Pricing

**Date:** 2026-03-16
**Author:** uSipipo VPN Manager Team
**Status:** ✅ Implemented
**Version:** 3.9.1

---

## Executive Summary

This document describes the redesign of GB data package pricing to align with subscription plans and consumption mode, creating a coherent value proposition across all product tiers.

---

## Problem Statement

### Original Pricing Issues

The original GB package pricing had significant inconsistencies:

| Package | GB | Original Stars | Original USD | $/GB | Problem |
|---------|-----|----------------|--------------|------|---------|
| Básico | 10 GB | 600 ⭐ | ~$6.00 | $0.60/GB | 2.4x more expensive than consumption |
| Estándar | 30 GB | 960 ⭐ | ~$9.60 | $0.29/GB | Slightly more expensive than consumption |
| Avanzado | 60 GB | 1320 ⭐ | ~$13.20 | $0.19/GB | Reasonable value |
| Premium | 120 GB | 1800 ⭐ | ~$18.00 | $0.125/GB | Good value |
| Ilimitado | 200 GB | 2400 ⭐ | ~$24.00 | $0.096/GB | Best package value |

### Comparison with Other Products

**Subscription Plans:**
- 1 Month: 360 ⭐ ($2.99) → **Unlimited data**
- 3 Months: 960 ⭐ ($7.99) → **Unlimited data** (~$2.66/month)
- 6 Months: 1560 ⭐ ($12.99) → **Unlimited data** (~$2.17/month)

**Consumption Mode:**
- Pay-as-you-go: $0.25/GB

### Key Issues Identified

1. **Value Inconsistency**: A subscription user ($2.99/month) gets unlimited data, while a package user pays $6.00 for only 10GB.

2. **Consumption Misalignment**: Consumption mode ($0.25/GB) is cheaper than the Básico package ($0.60/GB).

3. **No Incentive for Packages**: No rational reason to buy packages when subscriptions offer better value.

4. **Bonus Misalignment**: Package bonuses (0-25%) don't compete with "unlimited" subscription value.

---

## Solution: Value-Based Pricing

### Pricing Philosophy

**Packages as "Top-ups"**: Position data packages as complementary products for users who:
- Don't want a subscription commitment
- Have unpredictable usage patterns
- Prefer pay-as-you-go flexibility
- Need additional data alongside free tier

### New Pricing Structure

| Package | GB | Bonus | Final GB | New Stars | New USD | $/GB | Discount vs Consumption |
|---------|-----|-------|----------|-----------|---------|------|------------------------|
| **Básico** | 10 GB | 0% | 10 GB | 250 ⭐ | $2.50 | $0.25/GB | 0% (aligned) |
| **Estándar** | 30 GB | 10% | 33 GB | 600 ⭐ | $6.00 | $0.18/GB | 28% |
| **Avanzado** | 60 GB | 15% | 69 GB | 960 ⭐ | $9.60 | $0.14/GB | 44% |
| **Premium** | 120 GB | 20% | 144 GB | 1440 ⭐ | $14.40 | $0.10/GB | 60% |
| **Ilimitado** | 200 GB | 25% | 250 GB | 1800 ⭐ | $18.00 | $0.07/GB | 72% |

### Product Positioning

```
┌─────────────────────────────────────────────────────────────┐
│                    VALUE LADDER                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📊 CONSUMPTION MODE                                        │
│     $0.25/GB • Pay only what you use • No commitment       │
│     → Best for: Unpredictable usage, <10GB/month           │
│                                                             │
│  📦 DATA PACKAGES                                           │
│     Básico: $0.25/GB • No invoice hassle • Prepaid         │
│     → Best for: Light users, vacation, temporary needs      │
│                                                             │
│     Estándar+: $0.18-0.07/GB • Volume discounts • Bonus GB │
│     → Best for: Regular users, predictable consumption      │
│                                                             │
│  💎 SUBSCRIPTION PLANS                                      │
│     $2.99-12.99/month • UNLIMITED data • Premium features  │
│     → Best for: Power users, daily VPN usage, >100GB/month │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Details

### Code Changes

**File: `application/services/data_package_service.py`**

```python
PACKAGE_OPTIONS: List[PackageOption] = [
    PackageOption(
        name="Básico",
        package_type=PackageType.BASIC,
        data_gb=10,
        stars=250,  # Changed from 600
        bonus_percent=0,
    ),
    PackageOption(
        name="Estándar",
        package_type=PackageType.ESTANDAR,
        data_gb=30,
        stars=600,  # Changed from 960
        bonus_percent=10,
    ),
    PackageOption(
        name="Avanzado",
        package_type=PackageType.AVANZADO,
        data_gb=60,
        stars=960,  # Changed from 1320
        bonus_percent=15,
    ),
    PackageOption(
        name="Premium",
        package_type=PackageType.PREMIUM,
        data_gb=120,
        stars=1440,  # Changed from 1800
        bonus_percent=20,
    ),
    PackageOption(
        name="Ilimitado",
        package_type=PackageType.UNLIMITED,
        data_gb=200,
        stars=1800,  # Changed from 2400
        bonus_percent=25,
    ),
]
```

### Crypto Payment Calculation

Crypto payments use the formula: `USDT = stars / 120`

| Package | Stars | USDT (Stars/120) |
|---------|-------|------------------|
| Básico | 250 ⭐ | $2.08 USDT |
| Estándar | 600 ⭐ | $5.00 USDT |
| Avanzado | 960 ⭐ | $8.00 USDT |
| Premium | 1440 ⭐ | $12.00 USDT |
| Ilimitado | 1800 ⭐ | $15.00 USDT |

---

## Testing

All tests updated and passing (446 tests total):

- ✅ `test_data_package_service.py` - 13 tests
- ✅ `test_user_bonus_service.py` - 13 tests
- ✅ `test_vpn_service.py` - 20 tests
- ✅ `test_handlers_buy_gb_crypto.py` - 2 tests
- ✅ `test_payment_endpoints.py` (Mini App) - 19 tests
- ✅ All other existing tests - 379 tests

### Test Files Modified

1. `tests/application/services/test_data_package_service.py`
2. `tests/application/services/test_user_bonus_service.py`
3. `tests/application/services/test_vpn_service.py`
4. `tests/conftest.py`
5. `tests/miniapp/test_payment_endpoints.py`
6. `tests/telegram_bot/features/buy_gb/test_handlers_buy_gb_crypto.py`

---

## Business Impact

### Revenue Analysis

**Before (per package):**
- Básico: $6.00 (but low conversion due to poor value)
- Premium: $18.00

**After (per package):**
- Básico: $2.50 (competitive with consumption)
- Premium: $14.40 (still profitable at $0.10/GB)

**Expected Outcomes:**
1. **Higher Conversion**: Lower entry price (Básico $2.50) attracts more users
2. **Better Retention**: Clear upgrade path from Básico → Premium
3. **Subscription Upsell**: Users who outgrow packages naturally migrate to subscriptions
4. **Consumption Alternative**: Users who want flexibility have a fair prepaid option

### Customer Segments

| Segment | Recommended Product | Monthly Cost | Value Prop |
|---------|---------------------|--------------|------------|
| Light User (<10GB) | Consumption Mode | ~$2.50 | Pay only what you use |
| Casual User (10-30GB) | Básico/Estándar | $2.50-6.00 | Prepaid, no invoice |
| Regular User (30-100GB) | Avanzado/Premium | $9.60-14.40 | Best $/GB ratio |
| Power User (>100GB) | Subscription | $2.99-12.99 | Unlimited data |

---

## Migration Plan

### For Existing Users

**No changes to active packages** - existing purchases retain their original terms.

**New purchases** automatically use the new pricing structure.

### Communication Strategy

1. **Announcement Message**: Notify all users of "New Lower Prices!"
2. **Highlight Básico**: Emphasize the new $2.50 entry point
3. **Comparison Chart**: Show value vs subscriptions and consumption
4. **Limited-Time Bonus**: Consider extra loyalty bonus for first post-change purchase

---

## Future Considerations

### Dynamic Pricing

Consider implementing:
- **Seasonal promotions** (holiday discounts)
- **Flash sales** (24-hour package deals)
- **Personalized offers** (based on usage patterns)

### Bundle Options

Potential future products:
- **Family Plan**: Shared data pool across multiple users
- **Business Plan**: Higher priority, static IPs
- **Gaming Plan**: Optimized for low latency

---

## Conclusion

This pricing redesign creates a coherent, value-based structure that:

✅ Aligns package pricing with consumption mode ($0.25/GB base)
✅ Maintains subscription value proposition (unlimited data)
✅ Provides clear upgrade paths for all user segments
✅ Improves conversion potential with lower entry price
✅ Preserves margin through volume-based bonuses

**Result**: A sustainable pricing ecosystem that serves all customer types fairly while maintaining healthy unit economics.

---

## References

- Original Issue: Pricing inconsistency between packages, subscriptions, and consumption mode
- Related Files: `application/services/data_package_service.py`, `application/services/subscription_service.py`
- Database Schema: `domain/entities/data_package.py`, `domain/entities/subscription_plan.py`
