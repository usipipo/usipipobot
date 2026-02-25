import asyncio
import logging
from typing import Optional

import aiohttp

from utils.logger import logger


class DuckDNSService:
    DUCKDNS_UPDATE_URL = "https://www.duckdns.org/update"

    def __init__(self, domain: str, token: str) -> None:
        self.domain = domain
        self.token = token
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def update_ip(self) -> bool:
        session = await self._get_session()
        params = {"domains": self.domain, "token": self.token, "ip": ""}
        try:
            async with session.get(self.DUCKDNS_UPDATE_URL, params=params) as response:
                result = await response.text()
                if result == "OK":
                    logger.info(f"✅ DuckDNS IP actualizada: {self.domain}.duckdns.org")
                    return True
                else:
                    logger.error(f"❌ DuckDNS error: {result}")
                    return False
        except Exception as e:
            logger.error(f"❌ Error actualizando DuckDNS: {e}")
            return False

    def get_public_url(self) -> str:
        return f"https://{self.domain}.duckdns.org"

    @staticmethod
    def get_cron_script_content(domain: str, token: str) -> str:
        return f"""#!/bin/bash
echo url="https://www.duckdns.org/update?domains={domain}&token={token}&ip=" | curl -k -o ~/duckdns/duck.log -K -
"""

    @staticmethod
    def setup_instructions(domain: str, token: str) -> str:
        return f"""
Instrucciones para configurar DuckDNS:

1. Crear directorio:
   mkdir -p ~/duckdns

2. Crear script de actualizacion:
   cat > ~/duckdns/duck.sh << 'SCRIPT'
{DuckDNSService.get_cron_script_content(domain, token)}SCRIPT

3. Hacer ejecutable:
   chmod 700 ~/duckdns/duck.sh

4. Configurar cron (cada 5 minutos):
   (crontab -l 2>/dev/null; echo "*/5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1") | crontab -

5. Probar:
   ~/duckdns/duck.sh
   cat ~/duckdns/duck.log

Debe mostrar: OK
"""
