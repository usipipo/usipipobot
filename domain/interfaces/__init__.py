from domain.interfaces.idata_package_repository import IDataPackageRepository
from domain.interfaces.ikey_repository import IKeyRepository
from domain.interfaces.iuser_repository import IUserRepository
from domain.interfaces.iachievement_repository import IAchievementRepository
from domain.interfaces.itransaction_repository import ITransactionRepository
from domain.interfaces.iachievement_service import IAchievementService
from domain.interfaces.iadmin_service import IAdminService
from domain.interfaces.iai_support_service import IAiSupportService
from domain.interfaces.igame_service import IGameService
from domain.interfaces.ireferral_service import IReferralService
from domain.interfaces.ivpn_service import IVpnService

__all__ = [
    "IDataPackageRepository",
    "IKeyRepository",
    "IUserRepository",
    "IAchievementRepository",
    "ITransactionRepository",
    "IAchievementService",
    "IAdminService",
    "IAiSupportService",
    "IGameService",
    "IReferralService",
    "IVpnService",
]
