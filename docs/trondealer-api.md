# TronDealer API v2 Documentation

## Overview

TronDealer es una pasarela de pagos con stablecoins (USDT, USDC) que soporta más de 15 blockchains. La API v2 permite gestionar billeteras, comprar energía TRON, y procesar pagos. Esta documentación se centra en la gestión de billeteras BSC (BNB Smart Chain).

## Base URL

```
https://trondealer.com/api/v2
```

## Autenticación

Todos los endpoints requieren el header `x-api-key`:

```
x-api-key: TU_API_KEY
```

## Endpoints para Gestión de Billeteras BSC

### 1. Asignar Nueva Billetera BSC

Genera una nueva billetera BSC y la asigna al cliente autenticado. Acepta opcionalmente una etiqueta para identificación.

**Endpoint:** `POST /api/v2/wallets/assign`

**Headers:**
```
x-api-key: TU_API_KEY
Content-Type: application/json
```

**Request Body:**
```json
{
  "label": "user-deposit-42"
}
```

**Respuesta Exitosa (201):**
```json
{
  "success": true,
  "wallet": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "address": "0xAbC1234567890DEF1234567890abcdef12345678",
    "label": "user-deposit-42",
    "status": "active",
    "created_at": "2026-02-26T01:05:44.710Z"
  }
}
```

**Errores Comunes:**
- **401 Unauthorized:** API key inválida o faltante
- **403 Forbidden:** Cliente desactivado
- **500 Internal Server Error:** Error en el servidor

---

### 2. Obtener Saldo de Billetera

Devuelve los saldos de BNB, USDT y USDC para una billetera propiedad del cliente autenticado.

**Endpoint:** `POST /api/v2/wallets/balance`

**Headers:**
```
x-api-key: TU_API_KEY
Content-Type: application/json
```

**Request Body:**
```json
{
  "address": "0x1234567890abcdef1234567890abcdef12345678"
}
```

**Respuesta Exitosa (200):**
```json
{
  "success": true,
  "wallet": {
    "address": "0x1234567890abcdef1234567890abcdef12345678",
    "label": "user-deposit-42",
    "status": "active"
  },
  "balances": {
    "BNB": "0.0042",
    "USDT": "150.50",
    "USDC": "75.00"
  }
}
```

**Errores Comunes:**
- **400 Bad Request:** Parámetros faltantes o inválidos
- **401 Unauthorized:** API key inválida o faltante
- **403 Forbidden:** Cliente desactivado
- **404 Not Found:** Billetera no encontrada o no pertenece al cliente
- **500 Internal Server Error:** Error en el servidor

---

### 3. Obtener Historial de Transacciones

Devuelve el historial de transacciones paginado para una billetera propiedad del cliente autenticado. Soporta filtrado por estado.

**Endpoint:** `POST /api/v2/wallets/transactions`

**Headers:**
```
x-api-key: TU_API_KEY
Content-Type: application/json
```

**Request Body:**
```json
{
  "address": "0x1234567890abcdef1234567890abcdef12345678",
  "limit": 20,
  "offset": 0,
  "status": "confirmed"
}
```

**Parámetros:**
- `address`: Dirección de la billetera (obligatorio)
- `limit`: Máximo resultados por página (1-100, predeterminado: 50)
- `offset`: Número de registros a saltar (predeterminado: 0)
- `status`: Filtrar por estado de transacción (opcional)

**Respuesta Exitosa (200):**
```json
{
  "success": true,
  "wallet": {
    "address": "0x1234567890abcdef1234567890abcdef12345678",
    "label": "user-deposit-42"
  },
  "total": 42,
  "limit": 20,
  "offset": 0,
  "transactions": [
    {
      "tx_hash": "0xabc123...",
      "log_index": 0,
      "block_number": 0,
      "from_address": "string",
      "to_address": "string",
      "asset": "USDT",
      "amount": "100.00",
      "confirmations": 0,
      "status": "detected",
      "detected_at": "2026-02-26T01:05:44.688Z",
      "created_at": "2026-02-26T01:05:44.688Z"
    }
  ]
}
```

**Errores Comunes:**
- **400 Bad Request:** Parámetros faltantes o inválidos
- **401 Unauthorized:** API key inválida o faltante
- **403 Forbidden:** Cliente desactivado
- **404 Not Found:** Billetera no encontrada o no pertenece al cliente
- **500 Internal Server Error:** Error en el servidor

---

## Endpoints Adicionales (Explorados)

### 4. Calcular Costo de Energía

Calcula el costo de energía antes de comprar.

**Endpoint:** `POST /api/v2/energy/calculate`

**Request Body:**
```json
{
  "blockchain": "TRON",
  "energy_amount": 65000,
  "duration": 1
}
```

---

### 5. Comprar Energía

Compra energía para una dirección TRON.

**Endpoint:** `POST /api/v2/energy/buy`

**Request Body:**
```json
{
  "blockchain": "TRON",
  "address": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
  "energy_amount": 65000,
  "duration": 1
}
```

---

### 6. Activar Dirección

Activa una dirección en una blockchain.

**Endpoint:** `POST /api/v2/address/activate`

**Request Body:**
```json
{
  "blockchain": "TRON",
  "address": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
}
```

---

### 7. Obtener Servicios

Obtiene la lista de servicios disponibles y precios.

**Endpoint:** `POST /api/v2/services`

**Request Body:**
```json
{}
```

---

### 8. Tasas y Estimaciones

Obtiene estimaciones de tasas de cambio.

**Endpoint:** `POST /api/v2/rates`

---

### 9. Crear Pago

Crea una orden de pago.

**Endpoint:** `POST /api/v2/payment/create`

**Request Body:**
```json
{
  "blockchain": "TRON",
  "amount": 10,
  "currency": "USDT"
}
```

---

### 10. Generar QR de Pago

Genera un código QR para pagos.

**Endpoint:** `POST /api/v2/payment/qrcode`

**Request Body:**
```json
{
  "blockchain": "TRON"
}
```

---

## Códigos de Respuesta

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `success` | boolean | Indica si la operación fue exitosa |
| `wallet` | object | Información de la billetera |
| `balances` | object | Saldos de los tokens |
| `transactions` | array | Lista de transacciones |

---

## Ejemplo Completo en Python

```python
import requests
import json

API_KEY = "TU_API_KEY"
BASE_URL = "https://trondealer.com/api/v2"

headers = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

# Asignar billetera con etiqueta
response = requests.post(
    f"{BASE_URL}/wallets/assign",
    headers=headers,
    json={"label": "user-deposit-42"}
)
print("Asignar Billetera:", json.dumps(response.json(), indent=2))

# Obtener balance
wallet_address = "0x1234567890abcdef1234567890abcdef12345678"
response = requests.post(
    f"{BASE_URL}/wallets/balance",
    headers=headers,
    json={"address": wallet_address}
)
print("\nSaldo de Billetera:", json.dumps(response.json(), indent=2))

# Obtener transacciones con parámetros
response = requests.post(
    f"{BASE_URL}/wallets/transactions",
    headers=headers,
    json={
        "address": wallet_address,
        "limit": 20,
        "offset": 0,
        "status": "confirmed"
    }
)
print("\nHistorial de Transacciones:", json.dumps(response.json(), indent=2))
```

---

## Billeteras Soportadas

- **BSC** (Binance Smart Chain) - asignable mediante `/wallets/assign`
- **TRON** - mediante endpoints de energía
- Soporte para más de 15 blockchains

---

## Notas

- La API usa autenticación por API Key en header `x-api-key`
- No requiere firma SHA256 (a diferencia de TronZap)
- Todos los endpoints son POST
- Los timestamps están en formato ISO 8601
