"""
Servicio de gestión de usuarios administrativos para el bot uSipipo.

Author: uSipipo Team
Version: 1.0.0
"""

from typing import Dict, List, Optional

from domain.entities.admin import AdminOperationResult, AdminUserInfo
from domain.entities.user import UserRole, UserStatus
from domain.interfaces.iadmin_service import IAdminUserService
from utils.logger import logger


class AdminUserService(IAdminUserService):
    """Servicio dedicado a la gestión de usuarios desde el panel admin."""

    def __init__(
        self,
        user_repository,
        key_repository,
        payment_repository,
    ):
        self.user_repository = user_repository
        self.key_repository = key_repository
        self.payment_repository = payment_repository

    async def get_all_users(self, current_user_id: int) -> List[Dict]:
        """Obtener lista de todos los usuarios registrados."""
        try:
            users = await self.user_repository.get_all_users(current_user_id)

            user_list = []
            for user in users:
                user_keys = await self.key_repository.get_by_user(user.telegram_id, current_user_id)
                active_keys = [k for k in user_keys if k.is_active]

                balance = await self.payment_repository.get_balance(user.telegram_id)

                name_parts = (user.full_name or "").split(" ", 1)
                first_name = name_parts[0] if name_parts and name_parts[0] else "Unknown"
                last_name = name_parts[1] if len(name_parts) > 1 else None

                user_info = AdminUserInfo(
                    user_id=user.telegram_id,
                    username=user.username,
                    first_name=first_name,
                    last_name=last_name,
                    total_keys=len(user_keys),
                    active_keys=len(active_keys),
                    stars_balance=balance.stars if balance else 0,
                    total_deposited=getattr(user, "referral_credits", 0) or 0,
                    referral_credits=getattr(user, "referral_credits", 0) or 0,
                    registration_date=user.created_at,
                    last_activity=getattr(user, "last_activity", None),
                )
                user_list.append(user_info.__dict__)

            return user_list

        except Exception as e:
            logger.error(f"Error obteniendo todos los usuarios: {e}")
            return []

    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Obtener información detallada de un usuario."""
        try:
            user = await self.user_repository.get_by_id(user_id, user_id)
            if not user:
                return None

            user_keys = await self.key_repository.get_user_keys(user_id)
            active_keys = [k for k in user_keys if k.is_active]

            return {
                "user_id": user.telegram_id,
                "username": user.username,
                "full_name": user.full_name,
                "status": user.status.value,
                "role": user.role.value,
                "total_keys": len(user_keys),
                "active_keys": len(active_keys),
                "balance_stars": 0,
                "total_deposited": getattr(user, "referral_credits", 0) or 0,
                "referral_credits": user.referral_credits,
                "created_at": user.created_at,
            }
        except Exception as e:
            logger.error(f"Error obteniendo usuario {user_id}: {e}")
            return None

    async def update_user_status(self, user_id: int, status: str) -> AdminOperationResult:
        """Actualizar estado del usuario (ACTIVE, SUSPENDED, BLOCKED)."""
        try:
            user = await self.user_repository.get_by_id(user_id, user_id)
            if not user:
                return AdminOperationResult(
                    success=False,
                    operation="update_user_status",
                    target_id=str(user_id),
                    message="Usuario no encontrado",
                )

            valid_statuses = [s.value for s in UserStatus]
            if status not in valid_statuses:
                return AdminOperationResult(
                    success=False,
                    operation="update_user_status",
                    target_id=str(user_id),
                    message=f"Estado inválido. Válidos: {valid_statuses}",
                )

            user.status = UserStatus(status)
            await self.user_repository.update_user(user)

            logger.info(f"Usuario {user_id} actualizado a estado: {status}")
            return AdminOperationResult(
                success=True,
                operation="update_user_status",
                target_id=str(user_id),
                message=f"Usuario actualizado a estado: {status}",
                details={"new_status": status},
            )
        except Exception as e:
            logger.error(f"Error actualizando estado de usuario {user_id}: {e}")
            return AdminOperationResult(
                success=False,
                operation="update_user_status",
                target_id=str(user_id),
                message=f"Error: {str(e)}",
            )

    async def assign_role_to_user(
        self, user_id: int, role: str, duration_days: Optional[int] = None
    ) -> AdminOperationResult:
        """Asignar rol a un usuario."""
        try:
            user = await self.user_repository.get_by_id(user_id, user_id)
            if not user:
                return AdminOperationResult(
                    success=False,
                    operation="assign_role",
                    target_id=str(user_id),
                    message="Usuario no encontrado",
                )

            valid_roles = [r.value for r in UserRole]
            if role not in valid_roles:
                return AdminOperationResult(
                    success=False,
                    operation="assign_role",
                    target_id=str(user_id),
                    message=f"Rol inválido. Válidos: {valid_roles}",
                )

            user.role = UserRole(role)
            await self.user_repository.update_user(user)

            message = f'Rol "{role}" asignado a usuario {user_id}'
            logger.info(message)
            return AdminOperationResult(
                success=True,
                operation="assign_role",
                target_id=str(user_id),
                message=message,
                details={"role": role},
            )
        except Exception as e:
            logger.error(f"Error asignando rol a usuario {user_id}: {e}")
            return AdminOperationResult(
                success=False,
                operation="assign_role",
                target_id=str(user_id),
                message=f"Error: {str(e)}",
            )

    async def block_user(self, user_id: int) -> AdminOperationResult:
        """Bloquear un usuario."""
        return await self.update_user_status(user_id, UserStatus.BLOCKED.value)

    async def unblock_user(self, user_id: int) -> AdminOperationResult:
        """Desbloquear un usuario."""
        return await self.update_user_status(user_id, UserStatus.ACTIVE.value)

    async def delete_user(self, user_id: int, **kwargs) -> AdminOperationResult:
        """Eliminar un usuario y sus claves asociadas."""
        key_service = kwargs.get("key_service")
        try:
            user = await self.user_repository.get_by_id(user_id, user_id)
            if not user:
                return AdminOperationResult(
                    success=False,
                    operation="delete_user",
                    target_id=str(user_id),
                    message="Usuario no encontrado",
                )

            user_keys = await self.key_repository.get_user_keys(user_id)

            if key_service is None:
                return AdminOperationResult(
                    success=False,
                    operation="delete_user",
                    target_id=str(user_id),
                    message="Key service no proporcionado",
                )

            from typing import Any

            key_svc: Any = key_service

            deleted_keys_count = 0
            for key in user_keys:
                try:
                    result = await key_svc.delete_user_key_complete(key.key_id)
                    if result["success"]:
                        deleted_keys_count += 1
                except Exception as e:
                    logger.error(f"Error eliminando clave {key.key_id}: {e}")

            await self.user_repository.delete_user(user_id)

            message = f"Usuario {user_id} eliminado junto con {deleted_keys_count} claves"
            logger.info(message)
            return AdminOperationResult(
                success=True,
                operation="delete_user",
                target_id=str(user_id),
                message=message,
                details={"deleted_keys": deleted_keys_count},
            )
        except Exception as e:
            logger.error(f"Error eliminando usuario {user_id}: {e}")
            return AdminOperationResult(
                success=False,
                operation="delete_user",
                target_id=str(user_id),
                message=f"Error: {str(e)}",
            )

    async def get_users_paginated(
        self, page: int = 1, per_page: int = 10, current_user_id: int | None = None
    ) -> Dict:
        """Obtener usuarios paginados."""
        try:
            if current_user_id is None:
                current_user_id = 1
            all_users = await self.user_repository.get_all_users(current_user_id)
            total_users = len(all_users)

            offset = (page - 1) * per_page
            paginated_users = all_users[offset : offset + per_page]

            user_list = []
            for user in paginated_users:
                user_keys = await self.key_repository.get_user_keys(user.telegram_id)
                active_keys = [k for k in user_keys if k.is_active]

                user_list.append(
                    {
                        "user_id": user.telegram_id,
                        "username": user.username,
                        "full_name": user.full_name,
                        "status": user.status.value,
                        "role": user.role.value,
                        "total_keys": len(user_keys),
                        "active_keys": len(active_keys),
                        "balance_stars": getattr(user, "referral_credits", 0) or 0,
                        "created_at": user.created_at.isoformat(),
                    }
                )

            total_pages = (total_users + per_page - 1) // per_page

            return {
                "users": user_list,
                "total_users": total_users,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
            }
        except Exception as e:
            logger.error(f"Error obteniendo usuarios paginados: {e}")
            return {
                "users": [],
                "total_users": 0,
                "page": page,
                "per_page": per_page,
                "total_pages": 0,
            }
