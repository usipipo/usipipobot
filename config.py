"""
Configuración central de la aplicación uSipipo VPN Manager.
Gestiona variables de entorno con validación estricta y valores seguros por defecto.

Author: uSipipo Team
Version: 3.0.0
Last Updated: 2026-02-21
"""

from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración centralizada con validación automática.
    Todas las variables se cargan desde .env con valores por defecto seguros.
    """

    # =========================================================================
    # APLICACIÓN BASE
    # =========================================================================
    PROJECT_NAME: str = Field(
        default="uSipipo VPN Manager", description="Nombre del proyecto"
    )

    APP_ENV: str = Field(
        default="development",
        description="Entorno de ejecución: development | production | staging",
    )

    DEFAULT_LANG: str = Field(
        default="es", description="Idioma por defecto de la aplicación"
    )

    # =========================================================================
    # SEGURIDAD Y API
    # =========================================================================
    SECRET_KEY: str = Field(
        ...,
        min_length=32,
        description="Clave secreta para JWT y encriptación (generada con openssl rand -hex 32)",
    )

    ALGORITHM: str = Field(default="HS256", description="Algoritmo de firma JWT")

    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        ge=5,
        le=1440,
        description="Tiempo de expiración del token en minutos",
    )

    API_HOST: str = Field(default="0.0.0.0", description="Host donde escucha la API")

    API_PORT: int = Field(
        default=8000, ge=1024, le=65535, description="Puerto de la API"
    )

    CORS_ORIGINS: List[str] = Field(
        default=["*"],
        description="Orígenes permitidos para CORS",
    )

    API_RATE_LIMIT: int = Field(
        default=60, ge=10, description="Límite de peticiones por minuto a la API"
    )

    # =========================================================================
    # TELEGRAM BOT
    # =========================================================================
    TELEGRAM_TOKEN: str = Field(
        ...,
        min_length=30,
        description="Token del bot de Telegram obtenido de @BotFather",
    )

    AUTHORIZED_USERS: List[int] = Field(
        default_factory=list,
        description="Lista de IDs de usuarios autorizados",
    )

    ADMIN_ID: int = Field(
        ..., description="ID de Telegram del administrador principal"
    )

    ADMIN_EMAIL: Optional[str] = Field(
        default=None, description="Email del administrador (opcional)"
    )

    TELEGRAM_RATE_LIMIT: int = Field(
        default=30,
        ge=1,
        description="Límite de peticiones por minuto por usuario en Telegram",
    )

    BOT_USERNAME: str = Field(
        default="usipipo_bot",
        description="Nombre de usuario del bot de Telegram (sin @)",
    )

    TELEGRAM_WEBHOOK_URL: Optional[str] = Field(
        default=None,
        description="URL del webhook de Telegram (opcional)",
    )

    # =========================================================================
    # BASE DE DATOS
    # =========================================================================
    DATABASE_URL: str = Field(
        ...,
        description="URL de conexión PostgreSQL (postgresql+asyncpg://user:pass@host:5432/db)",
    )

    DB_POOL_SIZE: int = Field(
        default=10,
        ge=5,
        le=50,
        description="Tamaño del pool de conexiones",
    )

    DB_TIMEOUT: int = Field(
        default=30, ge=10, le=120, description="Timeout de conexión en segundos"
    )

    # =========================================================================
    # INFORMACIÓN DE RED DEL SERVIDOR
    # =========================================================================
    SERVER_IP: str = Field(..., description="IP pública principal del VPS")

    SERVER_IPV4: str = Field(..., description="Dirección IPv4 pública")

    SERVER_IPV6: Optional[str] = Field(
        default=None, description="Dirección IPv6 pública (opcional)"
    )

    # =========================================================================
    # WIREGUARD
    # =========================================================================
    WG_INTERFACE: str = Field(
        default="wg0", description="Nombre de la interfaz WireGuard"
    )

    WG_SERVER_PORT: int = Field(
        default=51820, ge=1024, le=65535, description="Puerto UDP de WireGuard"
    )

    WG_SERVER_PUBKEY: Optional[str] = Field(
        default=None, description="Clave pública del servidor WireGuard"
    )

    WG_SERVER_PRIVKEY: Optional[str] = Field(
        default=None, description="Clave privada del servidor WireGuard (CONFIDENCIAL)"
    )

    WG_PATH: str = Field(
        default="/etc/wireguard", description="Ruta de configuraciones de WireGuard"
    )

    WG_ENDPOINT: Optional[str] = Field(
        default=None,
        description="Endpoint público de WireGuard (autoconstruido si no existe)",
    )

    WG_CLIENT_DNS_1: str = Field(
        default="1.1.1.1", description="DNS primario para clientes WireGuard"
    )

    # =========================================================================
    # OUTLINE VPN
    # =========================================================================
    OUTLINE_API_URL: Optional[str] = Field(
        default=None, description="URL completa de la API de Outline"
    )

    # =========================================================================
    # LÍMITES Y CUOTAS
    # =========================================================================
    VPN_KEY_EXPIRE_DAYS: int = Field(
        default=30, ge=1, le=365, description="Días de validez de llaves VPN"
    )

    MAX_KEYS_PER_USER: int = Field(
        default=5, ge=1, le=50, description="Máximo de llaves permitidas por usuario"
    )

    # =========================================================================
    # SISTEMA DE PLANES
    # =========================================================================
    FREE_PLAN_MAX_KEYS: int = Field(
        default=2, ge=1, description="Máximo de llaves para el plan gratuito"
    )

    FREE_PLAN_DATA_LIMIT_GB: int = Field(
        default=10,
        ge=1,
        description="Límite de datos por clave en GB para el plan gratuito",
    )

    REFERRAL_COMMISSION_PERCENT: int = Field(
        default=10,
        ge=0,
        le=100,
        description="Porcentaje de comisión por referidos (0-100)",
    )

    KEY_CLEANUP_DAYS: int = Field(
        default=90, ge=30, description="Días de inactividad para limpiar una clave"
    )

    BILLING_CYCLE_DAYS: int = Field(
        default=30, ge=1, description="Días del ciclo de facturación"
    )

    # =========================================================================
    # LOGGING Y MONITOREO
    # =========================================================================
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Nivel de logging: DEBUG | INFO | WARNING | ERROR | CRITICAL",
    )

    LOG_FILE_PATH: str = Field(
        default="./logs/vpn_manager.log", description="Ruta del archivo de logs"
    )

    ENABLE_METRICS: bool = Field(
        default=False,
        description="Habilitar recolección de métricas",
    )

    SENTRY_DSN: Optional[str] = Field(
        default=None, description="DSN de Sentry para tracking de errores"
    )

    # =========================================================================
    # RUTAS Y DIRECTORIOS
    # =========================================================================
    TEMP_PATH: str = Field(default="./temp", description="Directorio temporal")

    QR_CODE_PATH: str = Field(
        default="./static/qr_codes", description="Directorio para códigos QR"
    )

    CLIENT_CONFIGS_PATH: str = Field(
        default="./static/configs",
        description="Directorio para configuraciones de clientes",
    )

    # =========================================================================
    # CONFIGURACIÓN DE PYDANTIC
    # =========================================================================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
        validate_assignment=True,
    )

    # =========================================================================
    # VALIDADORES
    # =========================================================================

    @field_validator("AUTHORIZED_USERS", mode="before")
    @classmethod
    def parse_authorized_users(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            v = v.strip("[]")
            try:
                return [int(x.strip()) for x in v.split(",") if x.strip()]
            except ValueError:
                return []
        return v if isinstance(v, list) else []

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            v = v.strip()
            v = v.strip("[]").replace('"', "").replace("'", "")
            if not v:
                return ["*"]
            return [x.strip() for x in v.split(",") if x.strip()]
        return v if isinstance(v, list) else ["*"]

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in valid_levels:
            return "INFO"
        return v

    @model_validator(mode="after")
    def validate_environment(self):
        if not self.WG_ENDPOINT and self.SERVER_IP and self.WG_SERVER_PORT:
            self.WG_ENDPOINT = f"{self.SERVER_IP}:{self.WG_SERVER_PORT}"

        if self.is_production and "*" in self.CORS_ORIGINS:
            pass

        if self.ADMIN_ID not in self.AUTHORIZED_USERS:
            self.AUTHORIZED_USERS.append(self.ADMIN_ID)

        for path_attr in ["TEMP_PATH", "QR_CODE_PATH", "CLIENT_CONFIGS_PATH"]:
            path_value = getattr(self, path_attr)
            Path(path_value).mkdir(parents=True, exist_ok=True)

        log_dir = Path(self.LOG_FILE_PATH).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        return self

    # =========================================================================
    # PROPIEDADES COMPUTADAS
    # =========================================================================

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV.lower() == "development"

    @property
    def database_config(self) -> dict:
        return {
            "url": self.DATABASE_URL,
            "pool_size": self.DB_POOL_SIZE,
            "pool_timeout": self.DB_TIMEOUT,
            "pool_pre_ping": True,
            "echo": self.is_development,
        }

    @property
    def wireguard_enabled(self) -> bool:
        return bool(
            self.WG_SERVER_PUBKEY and self.WG_SERVER_PRIVKEY and self.WG_ENDPOINT
        )

    @property
    def outline_enabled(self) -> bool:
        return bool(self.OUTLINE_API_URL)

    def get_vpn_protocols(self) -> List[str]:
        protocols = []
        if self.wireguard_enabled:
            protocols.append("wireguard")
        if self.outline_enabled:
            protocols.append("outline")
        return protocols

    def model_dump_safe(self) -> dict:
        data = self.model_dump()
        sensitive_keys = [
            "SECRET_KEY",
            "TELEGRAM_TOKEN",
            "WG_SERVER_PRIVKEY",
            "DATABASE_URL",
            "OUTLINE_API_URL",
            "SENTRY_DSN",
        ]
        for key in sensitive_keys:
            if key in data:
                data[key] = "***HIDDEN***"
        return data


def get_settings() -> Settings:
    return settings


try:
    settings = Settings()

    from utils.logger import logger

    try:
        logger.configure_from_settings(settings)
    except Exception:
        pass

    logger.info(f"Configuración cargada correctamente")
    logger.info(f"Proyecto: {settings.PROJECT_NAME}")
    logger.info(f"Entorno: {settings.APP_ENV}")
    logger.info(f"API: {settings.API_HOST}:{settings.API_PORT}")
    logger.info(f"Protocolos VPN: {', '.join(settings.get_vpn_protocols())}")

except Exception as e:
    from utils.logger import logger

    logger.critical(f"Error crítico de configuración: {str(e)}")
    exit(1)
