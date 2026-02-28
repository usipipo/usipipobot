# Implementation Plan: Pay-as-You-Go Consumption Billing

Track ID: `pay-as-you-go_20250301`
Created: 2025-03-01
Status: pending

## Overview

Plan detallado para implementar el sistema de tarifa por consumo postpago, incluyendo modelos de datos, servicios, handlers de Telegram y automatización de cierre de ciclos.

## Phase 1: Domain Layer - Models and Interfaces

### Tasks

- [x] **Task 1.1**: Create `ConsumptionBilling` entity `91b8bff`
  - Define dataclass with all required fields
  - Add property methods for calculations
  - Add validation methods

- [x] **Task 1.2**: Create `ConsumptionInvoice` entity `91b8bff`
  - Define dataclass with payment fields
  - Add status transitions methods
  - Add expiration check property

- [x] **Task 1.3**: Create `IConsumptionBillingRepository` interface `91b8bff`
  - Define protocol for billing operations
  - Include CRUD methods
  - Include query methods for active billing cycles

- [x] **Task 1.4**: Create `IConsumptionInvoiceRepository` interface `91b8bff`
  - Define protocol for invoice operations
  - Include payment verification methods

- [x] **Task 1.5**: Update `User` entity `91b8bff`
  - Add `consumption_mode_enabled` field
  - Add `has_pending_debt` field
  - Add `current_billing_id` field
  - Add `consumption_mode_activated_at` field

### Verification

- [x] **Verify 1.1**: All entities have proper type hints
- [x] **Verify 1.2**: Interfaces follow existing patterns
- [x] **Verify 1.3**: No circular imports

## Phase 2: Infrastructure Layer - Database

### Tasks

- [x] **Task 2.1**: Create `ConsumptionBillingModel` SQLAlchemy model `eb842d3`
  - Map entity to database table
  - Add indexes for performance
  - Set up relationships

- [x] **Task 2.2**: Create `ConsumptionInvoiceModel` SQLAlchemy model `eb842d3`
  - Map entity to database table
  - Add indexes on user_id and status
  - Set up foreign keys

- [~] **Task 2.3**: Create database migration (pending Alembic generation)
  - Generate Alembic migration for new tables
  - Include migration for User table alterations
  - Test migration rollback

- [x] **Task 2.4**: Implement `PostgresConsumptionBillingRepository` `eb842d3`
  - Implement all interface methods
  - Add transaction handling
  - Add error handling

- [ ] **Task 2.5**: Implement `PostgresConsumptionInvoiceRepository`
  - Implement all interface methods
  - Add transaction handling
  - Add error handling

### Verification

- [ ] **Verify 2.1**: Migration applies cleanly
- [ ] **Verify 2.2**: Repositories pass integration tests
- [ ] **Verify 2.3**: Database queries are optimized

## Phase 3: Application Layer - Services

### Tasks

- [ ] **Task 3.1**: Create `ConsumptionBillingService`
  - `activate_consumption_mode()` - Activa modo con validaciones
  - `record_data_usage()` - Registra consumo de MB
  - `get_current_consumption()` - Obtiene consumo actual
  - `close_billing_cycle()` - Cierra ciclo de 30 días
  - `can_activate_consumption()` - Valida si puede activar

- [ ] **Task 3.2**: Create `ConsumptionInvoiceService`
  - `generate_invoice()` - Genera factura con wallet y monto
  - `verify_payment()` - Verifica pago en blockchain
  - `process_payment()` - Procesa pago exitoso
  - `cancel_expired_invoices()` - Cancela facturas vencidas

- [ ] **Task 3.3**: Create `ConsumptionPricing` utility
  - Calculate cost from MB consumed
  - Constants for pricing ($0.45/GB)
  - Formatting utilities for display

- [ ] **Task 3.4**: Create `ConsumptionCronService`
  - Daily job to close expired cycles
  - Query for cycles older than 30 days
  - Block VPN keys for users with closed cycles
  - Send notifications

- [ ] **Task 3.5**: Update dependency injection container
  - Register new services in container
  - Wire up repositories

### Verification

- [ ] **Verify 3.1**: All service methods have unit tests
- [ ] **Verify 3.2**: Mocked tests for external dependencies
- [ ] **Verify 3.3**: Edge cases covered (0 MB, max MB, etc.)

## Phase 4: Telegram Bot - Handlers

### Tasks

- [ ] **Task 4.1**: Create `ConsumptionMessages` class
  - Warning/activation message with terms
  - Consumption status message
  - Invoice generation message
  - Payment confirmation message
  - Deactivation notification

- [ ] **Task 4.2**: Create `ConsumptionKeyboards` class
  - Activate consumption button
  - Confirm activation button (with checkbox)
  - Generate invoice button
  - View consumption button
  - Back to menu buttons

- [ ] **Task 4.3**: Create `ConsumptionHandler`
  - `show_consumption_menu()` - Menú principal
  - `activate_consumption()` - Inicia activación
  - `confirm_activation()` - Confirma con términos
  - `view_my_consumption()` - Muestra consumo actual
  - `generate_invoice()` - Genera factura
  - `handle_payment_callback()` - Recibe confirmación pago

- [ ] **Task 4.4**: Add handlers to bot router
  - Register callback handlers
  - Register command handlers (/mi_consumo)
  - Set up handler dependencies

- [ ] **Task 4.5**: Add menu integration
  - Add button in main menu
  - Add button in user management menu
  - Show/hide based on eligibility

### Verification

- [ ] **Verify 4.1**: Handlers respond correctly
- [ ] **Verify 4.2**: Message formatting is correct
- [ ] **Verify 4.3**: Keyboard flow is intuitive

## Phase 5: VPN Integration - Key Management

### Tasks

- [ ] **Task 5.1**: Create `VpnKeyConsumptionService`
  - Block keys when has_pending_debt = true
  - Unblock keys when invoice paid
  - Check consumption mode before allowing connections

- [ ] **Task 5.2**: Update existing VPN key handlers
  - Check for pending debt before creating keys
  - Check for pending debt before showing keys
  - Show warning if mode consumption active

- [ ] **Task 5.3**: Create `ConsumptionUsageTracker`
  - Hook into existing data usage tracking
  - Route consumption to billing service when mode active
  - Skip free data limit when mode active

### Verification

- [ ] **Verify 5.1**: Keys block/unblock correctly
- [ ] **Verify 5.2**: Usage tracking is accurate
- [ ] **Verify 5.3**: No interference with normal mode

## Phase 6: Cron Job and Automation

### Tasks

- [ ] **Task 6.1**: Create `scripts/run_consumption_cron.py`
  - Entry point for cron job
  - Calls ConsumptionCronService
  - Error handling and logging

- [ ] **Task 6.2**: Create systemd service file template
  - Daily execution at 00:00 UTC
  - Logging to dedicated file
  - Error alerting

- [ ] **Task 6.3**: Create cron monitoring
  - Track last execution time
  - Alert if job hasn't run in 25 hours
  - Log success/failure metrics

### Verification

- [ ] **Verify 6.1**: Cron job runs successfully
- [ ] **Verify 6.2**: Notifications are sent correctly
- [ ] **Verify 6.3**: Logs are informative

## Phase 7: Testing and Quality

### Tasks

- [ ] **Task 7.1**: Write unit tests for entities
  - Test ConsumptionBilling calculations
  - Test ConsumptionInvoice status transitions
  - Test User entity new methods

- [ ] **Task 7.2**: Write unit tests for services
  - Mock repositories
  - Test all service methods
  - Test edge cases

- [ ] **Task 7.3**: Write integration tests
  - Test with real database
  - Test cron job end-to-end
  - Test payment flow

- [ ] **Task 7.4**: Write handler tests
  - Mock update and context
  - Test handler responses
  - Test keyboard flows

- [ ] **Task 7.5**: Run full test suite
  - All tests must pass
  - Coverage >= 80%

### Verification

- [ ] **Verify 7.1**: pytest passes
- [ ] **Verify 7.2**: flake8 passes
- [ ] **Verify 7.3**: mypy passes
- [ ] **Verify 7.4**: Coverage >= 80%

## Phase 8: Documentation and Deployment

### Tasks

- [ ] **Task 8.1**: Update README.md
  - Document new feature
  - Add usage instructions
  - Add pricing information

- [ ] **Task 8.2**: Create deployment guide
  - Migration instructions
  - Cron job setup
  - Configuration changes

- [ ] **Task 8.3**: Update example.env
  - Add any new environment variables

- [ ] **Task 8.4**: Final integration test
  - Test complete flow manually
  - Verify all components work together

### Verification

- [ ] **Verify 8.1**: Documentation is accurate
- [ ] **Verify 8.2**: All acceptance criteria met

## Checkpoints

| Phase   | Checkpoint SHA | Date       | Status   |
|---------|----------------|------------|----------|
| Phase 1 | 91b8bff        | 2025-03-01 | verified |
| Phase 2 |                |            | pending  |
| Phase 3 |                |      | pending |
| Phase 4 |                |      | pending |
| Phase 5 |                |      | pending |
| Phase 6 |                |      | pending |
| Phase 7 |                |      | pending |
| Phase 8 |                |      | pending |

## Estimates

| Phase | Estimated Duration | Complexity |
|-------|-------------------|------------|
| Phase 1 | 2 hours | Low |
| Phase 2 | 4 hours | Medium |
| Phase 3 | 6 hours | High |
| Phase 4 | 4 hours | Medium |
| Phase 5 | 3 hours | Medium |
| Phase 6 | 2 hours | Low |
| Phase 7 | 4 hours | Medium |
| Phase 8 | 2 hours | Low |
| **Total** | **27 hours** | - |
