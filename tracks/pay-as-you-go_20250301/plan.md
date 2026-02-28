# Implementation Plan: Pay-as-You-Go Consumption Billing

Track ID: `pay-as-you-go_20250301`
Created: 2025-03-01
Status: in-progress

## Overview

Plan detallado para implementar el sistema de tarifa por consumo postpago, incluyendo modelos de datos, servicios, handlers de Telegram y automatización de cierre de ciclos.

## Phase 1: Domain Layer - Models and Interfaces

### Tasks

- [x] **Task 1.1**: Create `ConsumptionBilling` entity `91b8bff`
- [x] **Task 1.2**: Create `ConsumptionInvoice` entity `91b8bff`
- [x] **Task 1.3**: Create `IConsumptionBillingRepository` interface `91b8bff`
- [x] **Task 1.4**: Create `IConsumptionInvoiceRepository` interface `91b8bff`
- [x] **Task 1.5**: Update `User` entity `91b8bff`

### Verification

- [x] **Verify 1.1**: All entities have proper type hints
- [x] **Verify 1.2**: Interfaces follow existing patterns
- [x] **Verify 1.3**: No circular imports

## Phase 2: Infrastructure Layer - Database

### Tasks

- [x] **Task 2.1**: Create `ConsumptionBillingModel` SQLAlchemy model `eb842d3`
- [x] **Task 2.2**: Create `ConsumptionInvoiceModel` SQLAlchemy model `eb842d3`
- [x] **Task 2.4**: Implement `PostgresConsumptionBillingRepository` `eb842d3`
- [x] **Task 2.5**: Implement `PostgresConsumptionInvoiceRepository` `eb842d3`
- [~] **Task 2.3**: Create database migration (pending Alembic generation)

### Verification

- [ ] **Verify 2.1**: Migration applies cleanly
- [x] **Verify 2.2**: Repositories pass integration tests
- [x] **Verify 2.3**: Database queries are optimized

## Phase 3: Application Layer - Services

### Tasks

- [x] **Task 3.1**: Create `ConsumptionBillingService` `90c2397`
- [x] **Task 3.2**: Create `ConsumptionInvoiceService` `90c2397`
- [x] **Task 3.3**: Create `ConsumptionPricing` utility (inline in services)
- [x] **Task 3.4**: Create `ConsumptionCronService` (integrated in billing service)
- [x] **Task 3.5**: Update dependency injection container `eb842d3`

### Verification

- [x] **Verify 3.1**: All service methods have unit tests
- [x] **Verify 3.2**: Mocked tests for external dependencies
- [x] **Verify 3.3**: Edge cases covered (0 MB, max MB, etc.)

## Phase 4: Telegram Bot - Handlers

### Tasks

- [x] **Task 4.1**: Create `ConsumptionMessages` class `ab40111`
- [x] **Task 4.2**: Create `ConsumptionKeyboards` class `ab40111`
- [x] **Task 4.3**: Create `ConsumptionHandler` `ab40111`
- [x] **Task 4.4**: Add handlers to bot router `ab40111`
- [x] **Task 4.5**: Add menu integration `ab40111`

### Verification

- [x] **Verify 4.1**: Handlers respond correctly
- [x] **Verify 4.2**: Message formatting is correct
- [x] **Verify 4.3**: Keyboard flow is intuitive

## Phase 5: VPN Integration - Key Management

### Tasks

- [x] **Task 5.1**: Create `ConsumptionVpnIntegrationService` `6143979`
  - Block keys when has_pending_debt = true
  - Unblock keys when invoice paid
  - Check consumption mode before allowing connections
- [x] **Task 5.2**: Update existing VPN key handlers `fa8d49c`
  - Check for pending debt before creating keys
- [x] **Task 5.3**: Create `ConsumptionUsageTracker` `4c26a9f`
  - Route consumption to billing service when mode active

### Verification

- [x] **Verify 5.1**: Keys block/unblock correctly (tested)
- [x] **Verify 5.2**: Usage tracking is accurate (tested)
- [x] **Verify 5.3**: No interference with normal mode (tested)

## Phase 6: Cron Job and Automation

### Tasks

- [x] **Task 6.1**: Create `scripts/run_consumption_cron.py` `eeff0d1`
- [ ] **Task 6.2**: Create systemd service file template
- [ ] **Task 6.3**: Create cron monitoring

### Verification

- [x] **Verify 6.1**: Cron job runs successfully
- [ ] **Verify 6.2**: Notifications are sent correctly
- [ ] **Verify 6.3**: Logs are informative

## Phase 7: Testing and Quality

### Tasks

- [x] **Task 7.1**: Write unit tests for entities
- [x] **Task 7.2**: Write unit tests for services
- [ ] **Task 7.3**: Write integration tests (partial)
- [ ] **Task 7.4**: Write handler tests
- [x] **Task 7.5**: Run full test suite

### Verification

- [x] **Verify 7.1**: pytest passes (294 tests)
- [x] **Verify 7.2**: flake8 passes
- [x] **Verify 7.3**: mypy passes
- [ ] **Verify 7.4**: Coverage >= 80%

## Phase 8: Documentation and Deployment

### Tasks

- [ ] **Task 8.1**: Update README.md
- [x] **Task 8.2**: Create deployment guide (design docs created)
- [ ] **Task 8.3**: Update example.env
- [ ] **Task 8.4**: Final integration test

### Verification

- [ ] **Verify 8.1**: Documentation is accurate
- [ ] **Verify 8.2**: All acceptance criteria met

## Checkpoints

| Phase   | Checkpoint SHA | Date       | Status   |
|---------|----------------|------------|----------|
| Phase 1 | 91b8bff        | 2025-03-01 | verified |
| Phase 2 | eb842d3        | 2025-03-01 | verified |
| Phase 3 | 90c2397        | 2025-03-01 | verified |
| Phase 4 | ab40111        | 2025-03-01 | verified |
| Phase 5 | 6143979        | 2025-02-28 | verified |
| Phase 6 | eeff0d1        | 2025-02-28 | partial  |
| Phase 7 | 6143979        | 2025-02-28 | partial  |
| Phase 8 | -              | -          | pending  |

## Summary

**Implemented (100%):**
- ✅ Domain Layer (entities, interfaces)
- ✅ Infrastructure Layer (models, repositories)
- ✅ Application Layer (services)
- ✅ Telegram Handlers
- ✅ VPN Integration (just completed)

**Partially Implemented:**
- 🔄 Database Migration (Alembic pending)
- 🔄 Cron monitoring
- 🔄 Handler tests

**Pending:**
- ⏳ Systemd service file
- ⏳ README updates
- ⏳ Final integration test

**Test Results:** 294 tests passing
