import hashlib
import hmac
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from domain.entities.crypto_transaction import WebhookToken
from domain.interfaces.icrypto_transaction_repository import IWebhookTokenRepository
from utils.logger import logger


class WebhookSecurityService:
    MAX_TIMESTAMP_DRIFT_SECONDS = 300
    NONCE_EXPIRY_HOURS = 24

    def __init__(self, webhook_secret: str, token_repo: IWebhookTokenRepository):
        self.webhook_secret = webhook_secret
        self.token_repo = token_repo

    def verify_hmac_signature(
        self, payload: bytes, signature: str, timestamp: Optional[str] = None
    ) -> bool:
        if not signature:
            logger.warning("Missing HMAC signature")
            return False

        message = payload
        if timestamp:
            message = f"{timestamp}.".encode() + payload

        expected_signature = hmac.new(
            self.webhook_secret.encode(), message, hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            logger.warning("Invalid HMAC signature")
            return False

        return True

    def validate_timestamp(self, timestamp_str: str) -> Tuple[bool, Optional[str]]:
        try:
            timestamp = int(timestamp_str)
            current_time = int(time.time())
            drift = abs(current_time - timestamp)

            if drift > self.MAX_TIMESTAMP_DRIFT_SECONDS:
                logger.warning(f"Timestamp drift too large: {drift}s")
                return False, f"Timestamp expired (drift: {drift}s)"

            return True, None
        except ValueError:
            return False, "Invalid timestamp format"

    async def check_and_register_nonce(self, nonce: str) -> Tuple[bool, Optional[str]]:
        nonce_hash = hashlib.sha256(nonce.encode()).hexdigest()

        existing = await self.token_repo.get_by_hash(nonce_hash)
        if existing and not existing.is_expired:
            logger.warning("Replay attack detected: nonce already used")
            return False, "Nonce already used (potential replay attack)"

        token = WebhookToken(
            token_hash=nonce_hash,
            purpose="replay_protection",
            expires_at=datetime.now(timezone.utc)
            + timedelta(hours=self.NONCE_EXPIRY_HOURS),
            extra_data={"nonce": nonce},
        )

        await self.token_repo.save(token)
        return True, None

    async def cleanup_expired_nonces(self) -> int:
        count = await self.token_repo.cleanup_expired()
        if count > 0:
            logger.info(f"Cleaned up {count} expired nonces")
        return count

    def extract_client_ip(self, request_headers: dict) -> Optional[str]:
        x_forwarded_for = request_headers.get("x-forwarded-for")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

        x_real_ip = request_headers.get("x-real-ip")
        if x_real_ip:
            return x_real_ip

        return None

    def is_suspicious_request(
        self, payload: dict, headers: dict
    ) -> Tuple[bool, Optional[str]]:
        if not payload:
            return True, "Empty payload"

        required_fields = ["wallet_address", "amount", "tx_hash"]
        for field in required_fields:
            if field not in payload:
                return True, f"Missing required field: {field}"

        if payload.get("amount", 0) <= 0:
            return True, "Invalid amount"

        wallet = payload.get("wallet_address", "")
        if not wallet.startswith("0x") or len(wallet) != 42:
            return True, "Invalid wallet address format"

        return False, None
