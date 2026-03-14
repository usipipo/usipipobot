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
