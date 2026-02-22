from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from application.services.data_package_service import DataPackageService
from application.services.referral_service import ReferralService
from application.services.vpn_service import VpnService
from domain.interfaces.itransaction_repository import ITransactionRepository
from utils.logger import logger


@dataclass
class UserProfileSummary:
    user_id: int
    username: Optional[str]
    full_name: Optional[str]
    status: str
    role: str
    created_at: datetime
    max_keys: int
    keys_count: int
    keys_used: int
    total_used_gb: float
    total_limit_gb: float
    remaining_gb: float
    free_data_remaining_gb: float
    active_packages: int
    referral_code: str
    total_referrals: int
    referral_credits: int
    referred_by: Optional[int]


class UserProfileService:
    def __init__(
        self,
        transaction_repo: ITransactionRepository,
        data_package_service: DataPackageService,
        referral_service: ReferralService,
        vpn_service: VpnService,
    ):
        self.transaction_repo = transaction_repo
        self.data_package_service = data_package_service
        self.referral_service = referral_service
        self.vpn_service = vpn_service

    async def get_user_profile_summary(
        self, user_id: int, current_user_id: int
    ) -> Optional[UserProfileSummary]:
        try:
            vpn_status = await self.vpn_service.get_user_status(user_id, current_user_id)
            user = vpn_status.get("user")
            if not user:
                logger.warning(f"User not found for profile summary: {user_id}")
                return None

            data_summary = await self.data_package_service.get_user_data_summary(
                user_id, current_user_id
            )

            referral_stats = await self.referral_service.get_referral_stats(
                user_id, current_user_id
            )

            keys = vpn_status.get("keys", [])
            keys_used = sum(1 for k in keys if getattr(k, "used_bytes", 0) > 0)

            summary = UserProfileSummary(
                user_id=user.telegram_id,
                username=user.username,
                full_name=user.full_name,
                status=user.status.value,
                role=user.role.value,
                created_at=user.created_at,
                max_keys=user.max_keys,
                keys_count=vpn_status.get("keys_count", 0),
                keys_used=keys_used,
                total_used_gb=vpn_status.get("total_used_gb", 0.0),
                total_limit_gb=vpn_status.get("total_limit_gb", 0.0),
                remaining_gb=vpn_status.get("remaining_gb", 0.0),
                free_data_remaining_gb=data_summary.get("free_plan", {}).get(
                    "remaining_gb", 0.0
                ),
                active_packages=data_summary.get("active_packages", 0),
                referral_code=referral_stats.referral_code,
                total_referrals=referral_stats.total_referrals,
                referral_credits=referral_stats.referral_credits,
                referred_by=referral_stats.referred_by,
            )

            logger.info(f"📋 Profile summary generated for user {user_id}")
            return summary

        except Exception as e:
            logger.error(f"Error generating profile summary for user {user_id}: {e}")
            return None

    async def get_user_transactions(
        self, user_id: int, limit: int = 10
    ) -> List[dict]:
        try:
            transactions = await self.transaction_repo.get_user_transactions(user_id, limit)
            logger.info(f"📋 Retrieved {len(transactions)} transactions for user {user_id}")
            return transactions
        except Exception as e:
            logger.error(f"Error retrieving transactions for user {user_id}: {e}")
            return []
