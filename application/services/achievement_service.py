from typing import List, Optional

from utils.logger import logger


class AchievementService:
    def __init__(self, user_repo=None, achievement_repo=None):
        self.user_repo = user_repo
        self.achievement_repo = achievement_repo

    async def get_user_achievements(self, user_id: int) -> List:
        return []

    async def check_achievements(self, user_id: int) -> List:
        return []
