import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)


class WalletStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


@dataclass
class BscWallet:
    id: str
    address: str
    label: Optional[str] = None
    status: WalletStatus = WalletStatus.ACTIVE
    created_at: Optional[str] = None


@dataclass
class WalletBalance:
    address: str
    label: Optional[str] = None
    status: WalletStatus = WalletStatus.ACTIVE
    bnb: float = 0.0
    usdt: float = 0.0
    usdc: float = 0.0


class TransactionStatus(str, Enum):
    DETECTED = "detected"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    PENDING = "pending"


@dataclass
class WalletTransaction:
    tx_hash: str
    log_index: int
    block_number: int
    from_address: str
    to_address: str
    asset: str
    amount: float
    confirmations: int
    status: TransactionStatus
    detected_at: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class TransactionResponse:
    total: int
    limit: int
    offset: int
    transactions: List[WalletTransaction]


@dataclass
class PaymentOrder:
    order_id: str
    blockchain: str
    amount: float
    currency: str
    status: str
    created_at: Optional[str] = None


@dataclass
class PaymentQRCode:
    qr_code: str
    expires_at: Optional[str] = None


class TronDealerApiError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"TronDealer API error {status_code}: {message}")


class TronDealerClient:
    """
    API client for TronDealer v2 BSC wallet management.
    """

    BASE_URL = "https://trondealer.com/api/v2"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.TRON_DEALER_API_KEY
        self._client = httpx.AsyncClient()

    async def __aenter__(self):
        if self._client is None:
            self._client = httpx.AsyncClient()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def close(self):
        """Close the HTTP client connection."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def headers(self):
        return {"x-api-key": self.api_key, "Content-Type": "application/json"}

    async def _make_request(
        self, endpoint: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make a POST request to TronDealer API
        """
        if not self.api_key:
            raise TronDealerApiError(401, "API key not configured")

        url = f"{self.BASE_URL}/{endpoint}"

        try:
            logger.debug(f"Making TronDealer API request to {url}")

            # Ensure client is initialized
            if self._client is None:
                self._client = httpx.AsyncClient()

            response = await self._client.post(url, headers=self.headers, json=data)

            logger.debug(f"TronDealer API response status: {response.status_code}")

            try:
                response_data = await response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse TronDealer API response: {e}")
                raise TronDealerApiError(500, "Invalid response format")

            if response.status_code == 401:
                raise TronDealerApiError(
                    401, response_data.get("error", "Unauthorized")
                )
            elif response.status_code == 403:
                raise TronDealerApiError(403, response_data.get("error", "Forbidden"))
            elif response.status_code == 404:
                raise TronDealerApiError(404, response_data.get("error", "Not found"))
            elif response.status_code != 200 and response.status_code != 201:
                raise TronDealerApiError(
                    response.status_code, response_data.get("error", "Unknown error")
                )

            if not response_data.get("success"):
                raise TronDealerApiError(
                    response.status_code, response_data.get("error", "Request failed")
                )

            return response_data

        except TronDealerApiError:
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"TronDealer API HTTP error: {e}")
            raise TronDealerApiError(e.response.status_code, str(e))
        except httpx.RequestError as e:
            logger.error(f"TronDealer API request error: {e}")
            raise TronDealerApiError(503, f"Service unavailable: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error calling TronDealer API: {e}")
            raise TronDealerApiError(500, f"Unexpected error: {str(e)}")

    async def assign_wallet(self, label: Optional[str] = None) -> BscWallet:
        """
        Assign a new BSC wallet to the authenticated client.

        Args:
            label: Optional label for the wallet

        Returns:
            BscWallet: Newly created wallet
        """
        data = {}
        if label:
            data["label"] = label

        response_data = await self._make_request("wallets/assign", data)

        wallet_data = response_data.get("wallet")
        if not wallet_data:
            raise TronDealerApiError(
                500, "Invalid response format: missing wallet data"
            )

        return BscWallet(
            id=wallet_data["id"],
            address=wallet_data["address"],
            label=wallet_data.get("label"),
            status=WalletStatus(wallet_data["status"]),
            created_at=wallet_data.get("created_at"),
        )

    async def get_balance(self, address: str) -> WalletBalance:
        """
        Get live BNB, USDT, and USDC balances for a specific wallet.

        Args:
            address: BSC wallet address

        Returns:
            WalletBalance: Wallet with balances
        """
        response_data = await self._make_request(
            "wallets/balance", {"address": address}
        )

        wallet_data = response_data.get("wallet")
        balances_data = response_data.get("balances")

        if not wallet_data:
            raise TronDealerApiError(
                500, "Invalid response format: missing wallet data"
            )
        if not balances_data:
            raise TronDealerApiError(
                500, "Invalid response format: missing balances data"
            )

        return WalletBalance(
            address=wallet_data["address"],
            label=wallet_data.get("label"),
            status=WalletStatus(wallet_data["status"]),
            bnb=float(balances_data.get("BNB", 0)),
            usdt=float(balances_data.get("USDT", 0)),
            usdc=float(balances_data.get("USDC", 0)),
        )

    async def get_transactions(
        self,
        address: str,
        limit: int = 50,
        offset: int = 0,
        status: Optional[TransactionStatus] = None,
    ) -> TransactionResponse:
        """
        Get paginated transaction history for a specific wallet.

        Args:
            address: BSC wallet address
            limit: Number of transactions per page (1-100)
            offset: Number of records to skip
            status: Optional transaction status filter

        Returns:
            TransactionResponse: Paginated transactions
        """
        data = {
            "address": address,
            "limit": min(max(1, limit), 100),
            "offset": max(0, offset),
        }

        if status:
            data["status"] = status.value

        response_data = await self._make_request("wallets/transactions", data)

        transactions = []
        for tx_data in response_data.get("transactions", []):
            transactions.append(
                WalletTransaction(
                    tx_hash=tx_data["tx_hash"],
                    log_index=tx_data["log_index"],
                    block_number=tx_data["block_number"],
                    from_address=tx_data["from_address"],
                    to_address=tx_data["to_address"],
                    asset=tx_data["asset"],
                    amount=float(tx_data["amount"]),
                    confirmations=tx_data["confirmations"],
                    status=TransactionStatus(tx_data["status"]),
                    detected_at=tx_data.get("detected_at"),
                    created_at=tx_data.get("created_at"),
                )
            )

        return TransactionResponse(
            total=response_data.get("total", 0),
            limit=response_data.get("limit", 50),
            offset=response_data.get("offset", 0),
            transactions=transactions,
        )

    async def create_payment(
        self, blockchain: str, amount: float, currency: str = "USDT"
    ) -> PaymentOrder:
        """
        Create a payment order via TronDealer API.

        Args:
            blockchain: Blockchain network (e.g., "BSC", "TRON")
            amount: Amount to pay
            currency: Currency symbol (default: USDT)

        Returns:
            PaymentOrder: Created payment order
        """
        data = {"blockchain": blockchain, "amount": amount, "currency": currency}

        response_data = await self._make_request("payment/create", data)

        payment_data = response_data.get("payment")
        if not payment_data:
            raise TronDealerApiError(
                500, "Invalid response format: missing payment data"
            )

        return PaymentOrder(
            order_id=payment_data.get("order_id", ""),
            blockchain=payment_data.get("blockchain", blockchain),
            amount=float(payment_data.get("amount", amount)),
            currency=payment_data.get("currency", currency),
            status=payment_data.get("status", "pending"),
            created_at=payment_data.get("created_at"),
        )

    async def generate_qrcode(self, blockchain: str) -> PaymentQRCode:
        """
        Generate a QR code for payment.

        Args:
            blockchain: Blockchain network (e.g., "BSC", "TRON")

        Returns:
            PaymentQRCode: QR code data
        """
        data = {"blockchain": blockchain}

        response_data = await self._make_request("payment/qrcode", data)

        qr_data = response_data.get("qr_code")
        if not qr_data:
            raise TronDealerApiError(
                500, "Invalid response format: missing qr_code data"
            )

        return PaymentQRCode(
            qr_code=qr_data.get("code", ""), expires_at=qr_data.get("expires_at")
        )
