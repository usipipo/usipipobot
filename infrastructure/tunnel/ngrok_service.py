from typing import Optional
from pyngrok import ngrok
from utils.logger import logger


class NgrokService:
    def __init__(self, auth_token: Optional[str] = None, subdomain: Optional[str] = None):
        self.auth_token = auth_token
        self.subdomain = subdomain
        self.tunnel = None
        self.public_url = None

    def start(self, port: int = 8000) -> str:
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

        self.tunnel = ngrok.connect(**config)
        self.public_url = self.tunnel.public_url

        logger.info(f"🚀 Ngrok tunnel started: {self.public_url}")
        logger.info(f"📡 Webhook URL: {self.public_url}/api/v1/webhooks/tron-dealer")

        return self.public_url

    def stop(self):
        if self.tunnel:
            ngrok.disconnect(self.tunnel.public_url)
            logger.info("🔌 Ngrok tunnel stopped")

    def get_webhook_url(self) -> str:
        if not self.public_url:
            raise RuntimeError("Tunnel not started")
        return f"{self.public_url}/api/v1/webhooks/tron-dealer"

    @staticmethod
    def get_tunnels() -> list:
        return ngrok.get_tunnels()

    @staticmethod
    def kill_all():
        ngrok.kill()
        logger.info("💀 All ngrok tunnels killed")
