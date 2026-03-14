from pydantic import BaseModel, Field, validator
import re


class OTPRequest(BaseModel):
    """
    Schema para solicitar código OTP.

    El identifier puede ser:
    - Username de Telegram (con @ al inicio)
    - Telegram ID (número)
    """
    identifier: str = Field(..., min_length=1, max_length=50)

    @validator("identifier")
    def validate_identifier(cls, v):
        v = v.strip()

        if v.startswith("@"):
            # Username: 5-32 caracteres, solo letras, números, guiones bajos
            if not re.match(r"^[a-zA-Z0-9_]{5,32}$", v[1:]):
                raise ValueError(
                    "Username inválido. Debe tener 5-32 caracteres "
                    "y solo letras, números y guiones bajos"
                )
        else:
            # Debe ser telegram_id (número)
            if not v.isdigit():
                raise ValueError("Debe ser un username (@usuario) o telegram_id válido")
            if not (1 <= int(v) <= 9223372036854775807):
                raise ValueError("telegram_id fuera de rango válido")

        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "identifier": "@juanperez"
            }
        }
    }


class OTPResponse(BaseModel):
    """
    Schema de respuesta para solicitud OTP.
    """
    message: str
    expires_in_seconds: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Código enviado a tu chat de Telegram",
                "expires_in_seconds": 300
            }
        }
    }


class OTPVerify(BaseModel):
    """
    Schema para verificar código OTP.
    """
    identifier: str = Field(..., min_length=1, max_length=50)
    otp: str = Field(..., min_length=6, max_length=6)

    @validator("identifier")
    def validate_identifier(cls, v):
        v = v.strip()
        if v.startswith("@"):
            if not re.match(r"^[a-zA-Z0-9_]{5,32}$", v[1:]):
                raise ValueError("Username inválido")
        else:
            if not v.isdigit():
                raise ValueError("Debe ser username o telegram_id")
        return v

    @validator("otp")
    def validate_otp(cls, v):
        if not v.isdigit():
            raise ValueError("El código OTP debe ser numérico")
        if len(v) != 6:
            raise ValueError("El código OTP debe tener 6 dígitos")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "identifier": "@juanperez",
                "otp": "123456"
            }
        }
    }


class TokenResponse(BaseModel):
    """
    Schema de respuesta con token JWT.
    """
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 86400,
                "user": {
                    "telegram_id": "123456789",
                    "username": "juanperez",
                    "full_name": "Juan Pérez"
                }
            }
        }
    }


class RefreshTokenResponse(BaseModel):
    """
    Schema de respuesta para refresh de token.
    """
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 86400
            }
        }
    }


class LogoutResponse(BaseModel):
    """
    Schema de respuesta para logout.
    """
    message: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Sesión cerrada"
            }
        }
    }


class UserProfileResponse(BaseModel):
    """
    Schema de respuesta con perfil de usuario autenticado.

    Se usa en el endpoint GET /auth/me para devolver
    información del usuario autenticado.
    """
    telegram_id: int
    username: str | None
    full_name: str | None
    status: str
    has_pending_debt: bool = False
    consumption_mode_enabled: bool = False

    model_config = {
        "json_schema_extra": {
            "example": {
                "telegram_id": 123456789,
                "username": "juanperez",
                "full_name": "Juan Pérez",
                "status": "active",
                "has_pending_debt": False,
                "consumption_mode_enabled": False
            }
        }
    }
