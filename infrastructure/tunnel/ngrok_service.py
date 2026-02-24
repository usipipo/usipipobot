import time
from typing import Any, List, Optional

from pyngrok import ngrok
from pyngrok.exception import PyngrokNgrokError
from pyngrok.ngrok import NgrokTunnel

from utils.logger import logger


class NgrokService:
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    def __init__(self, auth_token: Optional[str] = None, subdomain: Optional[str] = None) -> None:
        self.auth_token: Optional[str] = auth_token
        self.subdomain: Optional[str] = subdomain
        self.tunnel: Optional[NgrokTunnel] = None
        self.public_url: Optional[str] = None

    @staticmethod
    def kill_all_tunnels() -> None:
        try:
            ngrok.kill()
            logger.info("💀 Killed all existing ngrok tunnels")
            time.sleep(1)
        except Exception as e:
            logger.debug(f"No existing ngrok tunnels to kill: {e}")

    def start(self, port: int = 8000, kill_existing: bool = True) -> str:
        if kill_existing:
            self.kill_all_tunnels()

        if self.auth_token:
            ngrok.set_auth_token(self.auth_token)
            logger.info("🔑 Ngrok auth token configured")

        config = {
            "addr": port,
            "proto": "http",
        }

        if self.subdomain:
            config["subdomain"] = self.subdomain
            logger.info(f"🌐 Using subdomain: {self.subdomain}")

        for attempt in range(self.MAX_RETRIES):
            try:
                self.tunnel = ngrok.connect(**config)
                public_url = self.tunnel.public_url
                if public_url is None:
                    raise RuntimeError("Failed to get public URL from ngrok tunnel")
                self.public_url = public_url

                logger.info(f"🚀 Ngrok tunnel started: {self.public_url}")
                logger.info(f"📡 Webhook URL: {self.public_url}/api/v1/webhooks/tron-dealer")

                return self.public_url
            except PyngrokNgrokError as e:
                if "already online" in str(e) or "ERR_NGROK_334" in str(e):
                    logger.warning(f"⚠️ Tunnel already online, killing and retrying (attempt {attempt + 1}/{self.MAX_RETRIES})")
                    self.kill_all_tunnels()
                    if attempt < self.MAX_RETRIES - 1:
                        time.sleep(self.RETRY_DELAY)
                        continue
                raise
            except Exception as e:
                logger.error(f"❌ Unexpected error starting ngrok tunnel: {e}")
                raise

        raise RuntimeError("Failed to start ngrok tunnel after max retries")

    def stop(self) -> None:
        if self.tunnel:
            public_url = self.tunnel.public_url
            if public_url is not None:
                ngrok.disconnect(public_url)
            logger.info("🔌 Ngrok tunnel stopped")

    def get_webhook_url(self) -> str:
        if not self.public_url:
            raise RuntimeError("Tunnel not started")
        return f"{self.public_url}/api/v1/webhooks/tron-dealer"

    @staticmethod
    def get_tunnels() -> List[Any]:
        return ngrok.get_tunnels()

    @staticmethod
    def kill_all() -> None:
        ngrok.kill()
        logger.info("💀 All ngrok tunnels killed")
