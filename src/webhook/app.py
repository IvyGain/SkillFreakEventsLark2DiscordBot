"""
Webhook server for receiving Lark notifications
"""

import asyncio
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn

from src.config.settings import settings
from src.utils.logger import get_logger
from src.discord.bot import EventsBot
from src.lark.client import LarkClient
from src.services.event_automation import event_automation_service

logger = get_logger(__name__)

class WebhookApp:
    """Webhook application for handling Lark notifications"""
    
    def __init__(self):
        self.app = FastAPI(title="Lark to Discord Webhook", version="1.0.0")
        self.bot: EventsBot = None
        self.lark_client: LarkClient = None
        self._setup_routes()
    
    def set_bot(self, bot: EventsBot):
        """Set the Discord bot instance"""
        self.bot = bot
    
    def set_lark_client(self, lark_client: LarkClient):
        """Set the Lark client instance"""
        self.lark_client = lark_client
        # Initialize event automation service
        if self.bot and self.lark_client:
            event_automation_service.set_clients(self.lark_client, self.bot.client)
    
    def _setup_routes(self):
        """Setup webhook routes"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {"status": "healthy", "message": "Webhook server is running"}
        
        @self.app.post("/webhook/lark/event")
        async def lark_event_webhook(request: Request, background_tasks: BackgroundTasks):
            """Handle Lark event webhook notifications"""
            try:
                # Get request body
                body = await request.json()
                logger.info(f"Received Lark webhook: {body}")
                
                # Verify webhook (if needed)
                if not self._verify_webhook(body):
                    raise HTTPException(status_code=401, detail="Unauthorized")
                
                # Process webhook in background
                background_tasks.add_task(self._process_lark_webhook, body)
                
                return JSONResponse(
                    status_code=200,
                    content={"message": "Webhook received successfully"}
                )
                
            except Exception as e:
                logger.error(f"Error processing Lark webhook: {str(e)}")
                raise HTTPException(status_code=500, detail="Internal server error")
        
        @self.app.post("/webhook/lark/peatix")
        async def lark_peatix_webhook(request: Request, background_tasks: BackgroundTasks):
            """Handle Lark Peatix status change webhook notifications"""
            try:
                # Get request body
                body = await request.json()
                logger.info(f"Received Lark Peatix webhook: {body}")
                
                # Verify webhook (if needed)
                if not self._verify_webhook(body):
                    raise HTTPException(status_code=401, detail="Unauthorized")
                
                # Process Peatix webhook in background
                background_tasks.add_task(self._process_peatix_webhook, body)
                
                return JSONResponse(
                    status_code=200,
                    content={"message": "Peatix webhook received successfully"}
                )
                
            except Exception as e:
                logger.error(f"Error processing Lark Peatix webhook: {str(e)}")
                raise HTTPException(status_code=500, detail="Internal server error")
    
    def _verify_webhook(self, body: Dict[str, Any]) -> bool:
        """Verify webhook authenticity (implement as needed)"""
        # TODO: Implement webhook verification if Lark provides signature verification
        return True
    
    async def _process_lark_webhook(self, body: Dict[str, Any]):
        """Process general Lark webhook notifications"""
        try:
            logger.info("Processing Lark webhook notification")
            
            # Extract event information from webhook body
            event_type = body.get("type")
            
            if event_type == "record_updated":
                # Handle record update notifications
                await self._handle_record_update(body)
            elif event_type == "record_created":
                # Handle record creation notifications
                await self._handle_record_creation(body)
            else:
                logger.warning(f"Unknown webhook event type: {event_type}")
                
        except Exception as e:
            logger.error(f"Error processing Lark webhook: {str(e)}")
    
    async def _process_peatix_webhook(self, body: Dict[str, Any]):
        """Process Peatix-specific webhook notifications"""
        try:
            logger.info("Processing Lark Peatix webhook notification")
            
            # Extract Peatix status information
            record_id = body.get("record_id")
            peatix_status = body.get("peatix_status")
            
            if not record_id:
                logger.warning("No record_id in Peatix webhook")
                return
            
            # Check if Peatix is published
            if peatix_status == "公開済み":
                logger.info(f"Peatix published for record {record_id}, creating Discord event")
                
                if self.bot and self.lark_client:
                    # Get the specific event record
                    event_record = await self._get_event_record(record_id)
                    if event_record and event_record.is_peatix_published():
                        # Create Discord event
                        await self.bot.create_discord_event(event_record)
                        logger.info(f"Discord event created for record {record_id}")
                    else:
                        logger.warning(f"Event record {record_id} not found or not published")
                else:
                    logger.error("Bot or Lark client not initialized")
            else:
                logger.info(f"Peatix not published for record {record_id}")
                
        except Exception as e:
            logger.error(f"Error processing Peatix webhook: {str(e)}")
    
    async def _handle_record_update(self, body: Dict[str, Any]):
        """Handle record update notifications"""
        try:
            logger.info("Handling record update notification")
            
            # Process with event automation service
            result = await event_automation_service.process_event_webhook(body)
            logger.info(f"Record update processing result: {result}")
                
        except Exception as e:
            logger.error(f"Error handling record update: {str(e)}")
    
    async def _handle_record_creation(self, body: Dict[str, Any]):
        """Handle record creation notifications"""
        try:
            logger.info("Handling record creation notification")
            
            # Process with event automation service
            result = await event_automation_service.process_event_webhook(body)
            logger.info(f"Record creation processing result: {result}")
                
        except Exception as e:
            logger.error(f"Error handling record creation: {str(e)}")
    
    async def _get_event_record(self, record_id: str):
        """Get event record by ID"""
        try:
            if not self.lark_client:
                logger.error("Lark client not initialized")
                return None
            
            # Get all events and find the specific record
            events = await self.lark_client.get_all_events()
            for event in events:
                if event.record_id == record_id:
                    return event
            
            logger.warning(f"Event record {record_id} not found")
            return None
            
        except Exception as e:
            logger.error(f"Error getting event record {record_id}: {str(e)}")
            return None

# Global webhook app instance
webhook_app = WebhookApp()

def get_webhook_app() -> FastAPI:
    """Get the FastAPI webhook application"""
    return webhook_app.app

async def run_webhook_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the webhook server"""
    config = uvicorn.Config(
        app=webhook_app.app,
        host=host,
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()