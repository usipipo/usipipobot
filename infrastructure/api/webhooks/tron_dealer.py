import json
from datetime import datetime, timezone
from fastapi import APIRouter, Request, HTTPException, Header, Depends
from pydantic import BaseModel, Field
from typing import Optional
import uuid

from application.services.webhook_security_service import WebhookSecurityService
from application.services.crypto_payment_service import CryptoPaymentService
from utils.logger import logger


router = APIRouter(tags=["webhooks"])


class TronDealerWebhookPayload(BaseModel):
    wallet_address: str = Field(..., min_length=42, max_length=42)
    amount: float = Field(..., gt=0)
    tx_hash: str = Field(..., min_length=66, max_length=66)
    token_symbol: str = Field(default="USDT")
    timestamp: Optional[str] = None
    nonce: Optional[str] = None


_security_service_instance: Optional[WebhookSecurityService] = None
_payment_service_instance: Optional[CryptoPaymentService] = None


def set_services(security_service: WebhookSecurityService, payment_service: CryptoPaymentService):
    global _security_service_instance, _payment_service_instance
    _security_service_instance = security_service
    _payment_service_instance = payment_service


async def get_security_service() -> WebhookSecurityService:
    if _security_service_instance is None:
        raise RuntimeError("Security service not initialized")
    return _security_service_instance


async def get_payment_service() -> CryptoPaymentService:
    if _payment_service_instance is None:
        raise RuntimeError("Payment service not initialized")
    return _payment_service_instance


@router.post("/tron-dealer")
async def handle_tron_dealer_webhook(
    request: Request,
    payload: TronDealerWebhookPayload,
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
    x_timestamp: Optional[str] = Header(None, alias="X-Timestamp"),
    x_nonce: Optional[str] = Header(None, alias="X-Nonce"),
    security: WebhookSecurityService = Depends(get_security_service),
    payment: CryptoPaymentService = Depends(get_payment_service)
):
    request_id = str(uuid.uuid4())[:8]
    client_ip = security.extract_client_ip(dict(request.headers)) or "unknown"

    logger.info(f"[{request_id}] Webhook received from IP: {client_ip}")

    raw_body = await request.body()

    if x_signature:
        if not security.verify_hmac_signature(raw_body, x_signature, x_timestamp):
            logger.warning(f"[{request_id}] Invalid HMAC signature from IP: {client_ip}")
            raise HTTPException(status_code=401, detail="Invalid signature")

    if x_timestamp:
        valid, error = security.validate_timestamp(x_timestamp)
        if not valid:
            logger.warning(f"[{request_id}] Timestamp validation failed: {error}")
            raise HTTPException(status_code=400, detail=error)

    nonce = x_nonce or payload.nonce or str(uuid.uuid4())
    valid, error = await security.check_and_register_nonce(nonce)
    if not valid:
        logger.warning(f"[{request_id}] Nonce validation failed: {error}")
        raise HTTPException(status_code=400, detail=error)

    is_suspicious, reason = security.is_suspicious_request(
        payload.model_dump(),
        dict(request.headers)
    )
    if is_suspicious:
        logger.warning(f"[{request_id}] Suspicious request: {reason}")
        raise HTTPException(status_code=400, detail="Invalid request")

    logger.info(
        f"[{request_id}] Processing payment: {payload.amount} {payload.token_symbol} "
        f"to wallet {payload.wallet_address}"
    )

    try:
        transaction = await payment.process_webhook_payment(
            wallet_address=payload.wallet_address,
            amount=payload.amount,
            tx_hash=payload.tx_hash,
            token_symbol=payload.token_symbol,
            raw_payload=payload.model_dump()
        )

        if transaction:
            logger.info(
                f"[{request_id}] Transaction processed: {transaction.id} "
                f"status={transaction.status}"
            )
            return {
                "status": "success",
                "transaction_id": str(transaction.id),
                "request_id": request_id
            }
        else:
            logger.error(f"[{request_id}] Failed to process transaction")
            return {
                "status": "error",
                "message": "Transaction processing failed",
                "request_id": request_id
            }

    except Exception as e:
        logger.error(f"[{request_id}] Error processing webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get("/tron-dealer/health")
async def webhook_health():
    return {
        "status": "healthy",
        "service": "tron-dealer-webhook",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
