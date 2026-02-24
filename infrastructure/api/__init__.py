from infrastructure.api.webhooks import tron_dealer_router
from infrastructure.api.server import create_app

app = create_app()

__all__ = ["tron_dealer_router", "app", "create_app"]
