"""
Ghost Key Cleanup Job - Automated cleanup of inactive VPN keys.

This module provides a scheduled job that identifies and disables
VPN keys that have been inactive for a configurable period.

Author: uSipipo Team
"""

from datetime import datetime
from typing import Any, Dict, Optional

from application.services.common.container import get_service
from application.services.vpn_infrastructure_service import VpnInfrastructureService
from config import settings
from utils.logger import logger


class GhostKeyCleanupJob:
    """
    Job for cleaning up ghost (inactive) VPN keys.

    Runs on a configurable schedule to identify keys that haven't been
    used for a specified number of days and disables them.
    """

    def __init__(
        self,
        vpn_service: Optional[VpnInfrastructureService] = None,
        key_repository: Optional[Any] = None,
        user_repository: Optional[Any] = None,
    ):
        """
        Initialize the ghost key cleanup job.

        Args:
            vpn_service: Service for VPN infrastructure operations.
            key_repository: Repository for key operations (optional).
            user_repository: Repository for user operations (optional).
        """
        self.vpn_service = vpn_service
        self.key_repository = key_repository
        self.user_repository = user_repository

    async def run(self) -> Dict[str, Any]:
        """
        Execute the ghost key cleanup.

        Identifies inactive keys and disables them. Logs results and
        notifies admin if any ghost keys were found.

        Returns:
            Dict with cleanup results including:
            - success: bool indicating if cleanup completed
            - total_checked: number of keys checked
            - ghosts_found: number of ghost keys identified
            - disabled_count: number of keys disabled
            - errors: list of any errors encountered
        """
        start_time = datetime.utcnow()
        logger.info(
            f"🧹 Starting ghost key cleanup job (inactive > {settings.GHOST_KEY_DETECTION_DAYS} days)"
        )

        try:
            if not self.vpn_service:
                self.vpn_service = get_service(VpnInfrastructureService)

            result = await self.vpn_service.cleanup_ghost_keys(
                days_inactive=settings.GHOST_KEY_DETECTION_DAYS
            )

            elapsed = (datetime.utcnow() - start_time).total_seconds()

            if result.get("ghosts_found", 0) > 0:
                logger.info(
                    f"👻 Ghost keys found: {result['ghosts_found']} "
                    f"disabled: {result['disabled_count']}"
                )
                await self._notify_admin(result)
            else:
                logger.info("✅ No ghost keys found")

            logger.info(f"✅ Ghost key cleanup completed in {elapsed:.2f}s")

            return {
                "success": True,
                "timestamp": start_time.isoformat(),
                "elapsed_seconds": elapsed,
                **result,
            }

        except Exception as e:
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"❌ Error during ghost key cleanup: {e}")

            return {
                "success": False,
                "timestamp": start_time.isoformat(),
                "elapsed_seconds": elapsed,
                "error": str(e),
                "total_checked": 0,
                "ghosts_found": 0,
                "disabled_count": 0,
                "errors": [str(e)],
            }

    def should_run_now(self) -> bool:
        """
        Check if the cleanup should run based on current day and hour.

        Returns:
            True if current day/hour matches settings and cleanup is enabled.
        """
        if not settings.GHOST_KEY_AUTO_CLEANUP_ENABLED:
            logger.debug("Ghost key cleanup is disabled")
            return False

        now = datetime.utcnow()
        current_day = now.strftime("%A").lower()
        current_hour = now.hour

        configured_day = settings.GHOST_KEY_CLEANUP_DAY.lower()
        configured_hour = settings.GHOST_KEY_CLEANUP_HOUR

        day_match = current_day == configured_day
        hour_match = current_hour == configured_hour

        logger.debug(
            f"Ghost key cleanup check: day={current_day}({day_match}), "
            f"hour={current_hour}({hour_match})"
        )

        return day_match and hour_match

    async def _notify_admin(self, result: Dict[str, Any]) -> None:
        """
        Notify admin about cleanup results.

        Args:
            result: The cleanup result dictionary.
        """
        try:
            ghosts_found = result.get("ghosts_found", 0)
            disabled_count = result.get("disabled_count", 0)
            errors = result.get("errors", [])

            logger.info(
                f"📢 Admin notification: Ghost key cleanup completed - "
                f"found={ghosts_found}, disabled={disabled_count}, errors={len(errors)}"
            )

            # Actual notification implementation can be added later
            # For now, we just log the notification

        except Exception as e:
            logger.warning(f"⚠️ Failed to send admin notification: {e}")


# Global instance for singleton pattern
_cleanup_job_instance: Optional[GhostKeyCleanupJob] = None


def get_cleanup_job(
    vpn_service: Optional[VpnInfrastructureService] = None,
    key_repository: Optional[Any] = None,
    user_repository: Optional[Any] = None,
) -> GhostKeyCleanupJob:
    """
    Get or create the global GhostKeyCleanupJob instance.

    Args:
        vpn_service: Optional VPN service instance.
        key_repository: Optional key repository instance.
        user_repository: Optional user repository instance.

    Returns:
        GhostKeyCleanupJob singleton instance.
    """
    global _cleanup_job_instance
    if _cleanup_job_instance is None:
        _cleanup_job_instance = GhostKeyCleanupJob(
            vpn_service=vpn_service,
            key_repository=key_repository,
            user_repository=user_repository,
        )
    return _cleanup_job_instance


async def run_ghost_key_cleanup() -> Dict[str, Any]:
    """
    Entry point for scheduled execution.

    Checks if cleanup should run and executes if conditions are met.
    Safe to call multiple times (idempotent via should_run_now check).

    Returns:
        Dict with cleanup results or status message.
    """
    job = get_cleanup_job()

    if not job.should_run_now():
        logger.debug("Ghost key cleanup skipped - not scheduled time")
        return {"success": True, "skipped": True, "reason": "not_scheduled_time"}

    return await job.run()
