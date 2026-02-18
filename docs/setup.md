# Setup Inicial - UsiPipoBot

## Prerrequisitos

- Python 3.9+
- Git
- Acceso a Supabase
- Cuenta de Telegram Bot

## Instalación

### 1. Clonar repositorio

```bash
git clone https://github.com/usipipo/usipipobot.git
cd usipipobot
```

### 2. Crear y activar entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp example.env .env
# Editar .env con tus configuraciones
```

### 5. Verificar estructura

El proyecto debe tener la siguiente estructura verificada:
- ✅ Rama `develop` activa
- ✅ Directorios organizados
- ✅ Sin archivos temporales

## Workflow de Desarrollo

### Ramas

- `main`: Producción estable
- `develop`: Desarrollo activo

### Flujo de trabajo

1. Crear feature branch desde develop:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/nueva-funcionalidad
   ```

2. Desarrollar y commitear cambios

3. Push y crear PR a develop:
   ```bash
   git push -u origin feature/nueva-funcionalidad
   ```

4. Merge a develop vía PR

5. Para releases, merge develop → main

## Estructura del Proyecto

Ver [project-structure.md](./project-structure.md) para detalles completos.

## Verificación Post-Setup

```bash
# Verificar rama
git branch --show-current  # Debe mostrar: develop

# Verificar no hay cambios pendientes
git status

# Verificar estructura
ls -la
```
