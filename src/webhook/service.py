"""
Webhook service for managing webhook server lifecycle
"""

import asyncio
import logging
from typing import Optional
import uvicorn

from src.config.settings import settings
from src.utils.logger import get_logger
from src.webhook.app import webhook_app, WebhookApp
from src.discord.bot import EventsBot
from src.lark.client import LarkClient

logger = get_logger(__name__)

class WebhookService:
    """Service for managing webhook server"""
    
    def __init__(self):
        self.server: Optional[uvicorn.Server] = None
        self.server_task: Optional[asyncio.Task] = None
        self.webhook_app: WebhookApp = webhook_app
        self.is_running = False
    
    async def start(self, bot: EventsBot, lark_client: LarkClient, host: str = "0.0.0.0", port: int = 8000):
        """Start the webhook server"""
        try:
            if self.is_running:
                logger.warning("Webhook server is already running")
                return
            
            # Set bot and lark client instances
            self.webhook_app.set_bot(bot)
            self.webhook_app.set_lark_client(lark_client)
            
            # Create server configuration
            config = uvicorn.Config(
                app=self.webhook_app.app,
                host=host,
                port=port,
                log_level="info",
                access_log=True
            )
            
            self.server = uvicorn.Server(config)
            
            # Start server in background task
            self.server_task = asyncio.create_task(self.server.serve())
            self.is_running = True
            
            logger.info(f"Webhook server started on {host}:{port}")
            
        except Exception as e:
            logger.error(f"Failed to start webhook server: {str(e)}")
            raise
    
    async def stop(self):
        """Stop the webhook server"""
        try:
            if not self.is_running:
                logger.warning("Webhook server is not running")
                return
            
            if self.server:
                self.server.should_exit = True
            
            if self.server_task:
                self.server_task.cancel()
                try:
                    await self.server_task
                except asyncio.CancelledError:
                    pass
            
            self.is_running = False
            logger.info("Webhook server stopped")
            
        except Exception as e:
            logger.error(f"Error stopping webhook server: {str(e)}")
    
    def get_webhook_urls(self, host: str = "localhost", port: int = 8000) -> dict:
        """Get webhook URLs for configuration"""
        base_url = f"http://{host}:{port}"
        return {
            "health_check": f"{base_url}/health",
            "lark_event_webhook": f"{base_url}/webhook/lark/event",
            "lark_peatix_webhook": f"{base_url}/webhook/lark/peatix"
        }

# Global webhook service instance
webhook_service = WebhookService()