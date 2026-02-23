# Technology Stack

Documento técnico que describe el stack tecnológico, arquitectura y componentes del sistema uSipipo Bot.

---

## 1. Stack Tecnológico Principal

### 1.1 Lenguaje y Framework Base
| Componente | Versión | Propósito |
|------------|---------|-----------|
| Python | 3.9+ | Lenguaje principal |
| python-telegram-bot | 21.x | Framework para Bot de Telegram |
| FastAPI | 0.115+ | Framework API REST |

### 1.2 Base de Datos
| Componente | Versión | Propósito |
|------------|---------|-----------|
| PostgreSQL | 14+ | Base de datos relacional |
| SQLAlchemy | 2.0+ | ORM para Python |
| Alembic | 1.13+ | Migraciones de base de datos |
| Supabase | Cloud | Hosting de PostgreSQL |

### 1.3 Infraestructura VPN
| Componente | Versión | Propósito |
|------------|---------|-----------|
| WireGuard | Latest | Protocolo VPN de alto rendimiento |
| Outline Server | Latest | Shadowsocks VPN server |
| Outline SDK | Python | API para gestión Outline |

### 1.4 Librerías Principales
| Librería | Versión | Propósito |
|----------|---------|-----------|
| Pydantic | 2.x | Validación de datos y settings |
| Punq | 0.7+ | Inyección de dependencias |
| Loguru | 0.7+ | Logging estructurado |
| aiohttp | 3.9+ | Cliente HTTP async |
| asyncpg | 0.29+ | Driver PostgreSQL async |

---

## 2. Arquitectura del Sistema

### 2.1 Clean Architecture / Arquitectura Hexagonal

El sistema sigue Clean Architecture con 4 capas principales:

1. **Capa de Interfaz**: Handlers de Telegram, API REST, Panel Admin
2. **Capa de Aplicación**: Servicios de aplicación y Puertos
3. **Capa de Dominio**: Entidades y Value Objects
4. **Capa de Infraestructura**: Repositorios, Servicios VPN, Adaptadores externos

### 2.2 Estructura de Directorios

```
project-root/
├── domain/                    # Capa de Dominio
│   ├── entities/             # User, Key, Server, Payment
│   └── interfaces/           # Repositorios
├── application/              # Capa de Aplicación
│   ├── ports/               # Interfaces de entrada
│   └── services/            # UserService, VPNService, PaymentService
├── infrastructure/           # Capa de Infraestructura
│   ├── persistence/         # Repositorios SQLAlchemy
│   ├── vpn/                 # WireGuard, Outline implementaciones
│   └── external/            # Telegram, Supabase clientes
├── telegram_bot/            # Interfaz Telegram
│   ├── handlers/
│   └── features/
├── api/                    # API REST
├── core/                   # Configuración
├── migrations/             # Alembic
└── docs/                   # Documentación
```

---

## 3. Componentes Detallados

### 3.1 Domain Layer - Entidades

**User**
- telegram_id: int
- username: Optional[str]
- full_name: Optional[str]
- status: UserStatus (ACTIVE, SUSPENDED, BLOCKED)
- role: UserRole (USER, ADMIN)
- max_keys: int (default: 2)
- referral_code: Optional[str]
- referred_by: Optional[int]
- referral_credits: int
- free_data_limit_bytes: int (10GB default)
- free_data_used_bytes: int

**Key**
- id: UUID
- user_id: UUID
- server_id: UUID
- protocol: WIREGUARD | OUTLINE
- config_data: str
- expires_at: datetime
- is_active: bool

**Server**
- id: UUID
- name: str
- location: str
- protocol: ProtocolType
- host: str
- port: int
- max_keys: int
- current_keys: int

### 3.2 Application Layer - Servicios

**VPNService**
- create_key(user_id, protocol, server_id) -> Key
- delete_key(key_id) -> bool
- list_user_keys(user_id) -> List[Key]
- renew_key(key_id, days) -> Key

**PaymentService**
- create_invoice(user_id, package_id) -> Invoice
- process_payment(payment_data) -> bool
- purchase_key_slots(user_id, slots) -> bool

**UserService**
- register_user(telegram_data) -> User
- get_user(telegram_id) -> User
- update_user(user_id, data)
- register_referral(new_user_id, referral_code) -> dict

**ReferralService**
- register_referral(new_user_id, referral_code) -> dict
- get_referral_stats(user_id) -> dict
- redeem_credits_for_data(user_id, credits) -> dict
- redeem_credits_for_slot(user_id) -> dict

### 3.3 Infrastructure Layer

**Repositorios**
- SQLAlchemyUserRepository
- SQLAlchemyKeyRepository
- SQLAlchemyPaymentRepository

**Servicios VPN**
- WireGuardService: SSH + wg commands
- OutlineService: Outline Management API

**Adaptadores**
- TelegramPayments: Webhook handler
- SupabaseClient: PostgreSQL connection

---

## 4. Flujo de Datos

### 4.1 Creación de Clave VPN
1. User → Telegram Bot → KeyHandler
2. KeyHandler → VPNService.create_key()
3. VPNService → KeyRepository (BD)
4. VPNService → WireGuardService/OutlineService
5. Servidor VPN → Genera config
6. VPNService → KeyRepository.save()
7. KeyHandler → User (config + QR)

### 4.2 Proceso de Pago
1. User → Comprar GB → PaymentHandler
2. PaymentHandler → PaymentService.create_invoice()
3. PaymentService → Telegram Payments API
4. Telegram → User (checkout)
5. User → Completa pago → Telegram
6. Telegram → Webhook → PaymentHandler
7. PaymentHandler → PaymentService.process_payment()
8. PaymentService → UserRepository.update_balance()
9. PaymentService → User (confirmación)

---

## 5. Configuración

### 5.1 Variables de Entorno Esenciales

```bash
# Telegram
TELEGRAM_TOKEN=bot_token_here
ADMIN_ID=123456789

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=xxx

# VPN Servers
WG_SERVER_IP=xxx.xxx.xxx.xxx
WG_SERVER_PORT=51820
OUTLINE_API_URL=https://xxx:xxx@host:port/xxx
OUTLINE_API_PORT=8080
OUTLINE_KEYS_PORT=443

# Application
SECRET_KEY=your-secret-key
ENVIRONMENT=production|development
LOG_LEVEL=INFO
```

### 5.2 Configuración Pydantic

```python
from pydantic_settings import BaseSettings
from pydantic import SecretStr, PostgresDsn

class Settings(BaseSettings):
    telegram_token: SecretStr
    admin_id: int
    database_url: PostgresDsn
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

---

## 6. Seguridad

### 6.1 Medidas Implementadas

| Aspecto | Implementación |
|---------|----------------|
| Autenticación | JWT tokens para API |
| Autorización | Decoradores role-based |
| Input Validation | Pydantic validators |
| SQL Injection | SQLAlchemy ORM (parameterized) |
| Logging | Loguru con sanitización |
| Secrets | python-dotenv + SecretStr |

### 6.2 Mejores Prácticas

- Nunca loggear tokens o datos sensibles
- Validar todos los inputs de usuario
- Rate limiting en handlers
- Escapar mensajes Markdown/HTML
- Usar HTTPS para todas las comunicaciones

---

## 7. Testing

### 7.1 Estrategia

| Tipo | Herramienta | Cobertura |
|------|-------------|-----------|
| Unit Tests | pytest | Services, Domain |
| Integration | pytest-asyncio | Repositories |
| E2E | Manual/API | Telegram Handlers |

### 7.2 Estructura de Tests

```
tests/
├── unit/
│   ├── domain/test_user.py
│   └── application/test_vpn_service.py
├── integration/
│   └── infrastructure/test_repositories.py
├── fixtures/conftest.py
└── mocks/telegram_mock.py
```

---

## 8. Despliegue

### 8.1 Requisitos del Servidor

- Ubuntu 20.04+ / Debian 11+
- 2 vCPU, 4GB RAM (recomendado)
- Docker & Docker Compose
- WireGuard instalado
- Python 3.9+

### 8.2 Proceso de Despliegue

```bash
# 1. Clonar repositorio
git clone https://github.com/usipipo/usipipobot.git
cd usipipobot

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables
cp example.env .env
nano .env  # Editar configuración

# 4. Ejecutar migraciones
alembic upgrade head

# 5. Iniciar bot
python main.py
```

### 8.3 Systemd Service

```ini
[Unit]
Description=uSipipo Telegram Bot
After=network.target

[Service]
Type=simple
User=usipipo
WorkingDirectory=/opt/usipipobot
Environment=PYTHONPATH=/opt/usipipobot
ExecStart=/opt/usipipobot/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

---

## 9. Dependencias

### 9.1 requirements.txt

```
# Telegram Bot
python-telegram-bot[job-queue]==21.10

# Database (PostgreSQL + SQLAlchemy Async)
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
alembic==1.14.0
psycopg2-binary==2.9.10

# Configuration & Validation
pydantic==2.10.3
pydantic-settings==2.6.1
python-dotenv==1.0.1
PyYAML==6.0.3

# HTTP Client
httpx==0.27.2
aiohttp==3.13.3

# Security & Authentication
PyJWT==2.10.1
cryptography==46.0.5

# Utilities
punq==0.7.0
loguru==0.7.3
qrcode[pil]==8.1
pillow==12.1.1
cachetools==6.2.4
python-dateutil==2.8.2
pytz==2025.2

# Testing
pytest==8.3.4
pytest-asyncio==1.3.0

# Optional / Development
rich==14.2.0
StrEnum==0.4.15
tenacity==9.1.2
```

---

*Documento versión 2.0 - Fecha: 2026-02-22*
