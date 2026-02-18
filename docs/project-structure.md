# Estructura del Proyecto UsiPipoBot

## Arquitectura

Este proyecto implementa **Clean Architecture** con las siguientes capas:

### 1. Domain Layer (`domain/`)
Entidades y reglas de negocio puras. No depende de ninguna otra capa.
- `entities/`: Objetos de dominio (User, Task, VPNKey, etc.)
- `interfaces/`: Contratos para repositorios y servicios

### 2. Application Layer (`application/`)
Casos de uso y lógica de aplicación.
- `services/`: Implementación de casos de uso
- `ports/`: Puertos de entrada/salida

### 3. Infrastructure Layer (`infrastructure/`)
Implementaciones técnicas y adaptadores.
- `persistence/supabase/`: Repositorios usando Supabase
- `api_clients/`: Clientes para APIs externas (Groq, WireGuard, Outline)
- `jobs/`: Jobs en background

### 4. Presentation Layer (`telegram_bot/`)
Interfaz con el usuario vía Telegram.
- `features/`: Módulos por funcionalidad
- `handlers/`: Manejadores de comandos y callbacks

## Estructura de Directorios

```
usipipobot/
├── api/                    # API REST endpoints
├── application/
│   ├── services/          # Servicios de aplicación
│   └── ports/            # Puertos
├── config.py             # Configuración centralizada
├── core/                 # Core/startup
├── docs/                 # Documentación
├── domain/
│   ├── entities/        # Entidades de dominio
│   └── interfaces/      # Interfaces (puertos)
├── infrastructure/
│   ├── api_clients/    # Clientes API externos
│   ├── jobs/          # Jobs programados
│   └── persistence/   # Persistencia
│       └── supabase/  # Implementación Supabase
├── main.py            # Entry point
├── migrations/        # Alembic migrations
├── requirements.txt   # Dependencias
├── telegram_bot/
│   ├── features/     # Features modulares
│   │   ├── announcer/
│   │   ├── operations/
│   │   ├── task_management/
│   │   ├── user_management/
│   │   └── vip/
│   └── handlers/    # Inicializador de handlers
├── templates/        # Plantillas de mensajes
└── utils/           # Utilidades compartidas
```

## Convenciones

- Cada feature en `telegram_bot/features/` tiene:
  - `handlers_*.py`: Manejadores
  - `keyboards_*.py`: Teclados inline
  - `messages_*.py`: Mensajes y textos
  - `__init__.py`: Inicialización

- Repositorios siguen el patrón Repository:
  - Interfaz en `domain/interfaces/`
  - Implementación en `infrastructure/persistence/`
