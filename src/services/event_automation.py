"""
Event automation service for handling Lark webhook triggers
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import discord
from discord.ext import commands

from src.config.settings import settings
from src.utils.logger import get_logger
from src.lark.client import LarkClient

logger = get_logger(__name__)

class EventAutomationService:
    """Service for automating Discord event creation and announcements"""
    
    def __init__(self):
        self.lark_client: Optional[LarkClient] = None
        self.discord_client: Optional[discord.Client] = None
    
    def set_clients(self, lark_client: LarkClient, discord_client: discord.Client):
        """Set the Lark and Discord client instances"""
        self.lark_client = lark_client
        self.discord_client = discord_client
    
    async def process_event_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process Lark webhook and trigger Discord event creation/announcement
        
        Args:
            webhook_data: Webhook payload from Lark
            
        Returns:
            Dict containing processing results
        """
        try:
            logger.info(f"Processing event webhook: {webhook_data}")
            
            # Extract record information
            record_id = self._extract_record_id(webhook_data)
            if not record_id:
                raise ValueError("No record ID found in webhook data")
            
            # Get full event data from Lark
            event_data = await self._get_event_data(record_id)
            if not event_data:
                raise ValueError(f"Could not retrieve event data for record {record_id}")
            
            # Check if this is a new event that needs processing
            if not self._should_process_event(event_data):
                logger.info(f"Event {record_id} does not need processing")
                return {"status": "skipped", "reason": "Event does not meet processing criteria"}
            
            # Create Discord event and announcements
            result = await self._create_discord_event_and_announcement(event_data)
            
            logger.info(f"Successfully processed event {record_id}")
            return {
                "status": "success",
                "record_id": record_id,
                "discord_event": result.get("discord_event"),
                "announcements": result.get("announcements"),
                "processed_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing event webhook: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "processed_at": datetime.now(timezone.utc).isoformat()
            }
    
    def _extract_record_id(self, webhook_data: Dict[str, Any]) -> Optional[str]:
        """Extract record ID from webhook data"""
        try:
            # Lark webhook structure varies, check common paths
            if "record" in webhook_data:
                return webhook_data["record"].get("record_id")
            elif "data" in webhook_data and "record_id" in webhook_data["data"]:
                return webhook_data["data"]["record_id"]
            elif "record_id" in webhook_data:
                return webhook_data["record_id"]
            return None
        except Exception as e:
            logger.error(f"Error extracting record ID: {str(e)}")
            return None
    
    async def _get_event_data(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Get full event data from Lark table"""
        try:
            if not self.lark_client:
                raise ValueError("Lark client not initialized")
            
            # Use existing Lark client to get record data
            record_data = await self.lark_client.get_record(record_id)
            return record_data
            
        except Exception as e:
            logger.error(f"Error getting event data for {record_id}: {str(e)}")
            return None
    
    def _should_process_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Determine if event should be processed for Discord automation
        
        Args:
            event_data: Event data from Lark
            
        Returns:
            bool: True if event should be processed
        """
        try:
            # Check if event has required fields
            required_fields = ["title", "instructor", "opening_month"]
            for field in required_fields:
                if field not in event_data or not event_data[field]:
                    logger.info(f"Event missing required field: {field}")
                    return False
            
            # Check if event is in the future (or within processing window)
            opening_month = event_data.get("opening_month")
            if opening_month:
                # Add logic to check if event is upcoming
                # For now, process all events with opening_month
                pass
            
            # Check if Discord event already exists
            # You could add a field to track this in Lark or check Discord
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking if event should be processed: {str(e)}")
            return False
    
    async def _create_discord_event_and_announcement(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create Discord event and post announcements
        
        Args:
            event_data: Event data from Lark
            
        Returns:
            Dict containing creation results
        """
        try:
            if not self.discord_client:
                raise ValueError("Discord client not initialized")
            
            # Extract event details
            title = event_data.get("title", "Unknown Event")
            instructor = event_data.get("instructor", "Unknown Instructor")
            
            # Get thumbnail image URL
            thumbnail_url = None
            fields = event_data.get("fields", {})
            
            # Extract thumbnail from サムネイル field
            thumbnail_field = fields.get("サムネイル")
            if thumbnail_field and isinstance(thumbnail_field, list) and len(thumbnail_field) > 0:
                thumbnail_item = thumbnail_field[0]
                if isinstance(thumbnail_item, dict):
                    thumbnail_url = thumbnail_item.get("url") or thumbnail_item.get("tmp_url")
            
            # Get links from fields
            youtube_link = None
            peatix_link = None
            
            for field_name, field_value in fields.items():
                if "YouTube" in field_name and field_value:
                    youtube_link = field_value
                elif "Peatix" in field_name and field_value:
                    peatix_link = field_value
            
            # Create start and end times (adjust as needed)
            from datetime import datetime, timedelta
            start_time = datetime.now(timezone.utc) + timedelta(days=7)  # Example: 1 week from now
            end_time = start_time + timedelta(hours=1, minutes=30)
            
            # Get guild and channels
            guild_id = int(settings.DISCORD_GUILD_ID)
            guild = self.discord_client.get_guild(guild_id)
            if not guild:
                raise ValueError(f"Guild {guild_id} not found")
            
            # Create Discord scheduled event
            discord_event = await guild.create_scheduled_event(
                name=title,
                description=f"""
🎯 **講師**: {instructor}

📺 **YouTube Live**: {youtube_link or 'TBD'}
🎫 **申込み**: {peatix_link or 'TBD'}

このイベントでは、{title}について詳しく学びます。
ぜひご参加ください！

#SkillFreak #プログラミング #自動化
                """.strip(),
                start_time=start_time,
                end_time=end_time,
                location=youtube_link or "YouTube Live",
                entity_type=discord.EntityType.external
            )
            
            # Set thumbnail image for Discord event if available
            if thumbnail_url:
                try:
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        async with session.get(thumbnail_url) as response:
                            if response.status == 200:
                                image_data = await response.read()
                                await discord_event.edit(image=image_data)
                                logger.info(f"Set thumbnail image for Discord event: {title}")
                            else:
                                logger.warning(f"Failed to fetch thumbnail image: HTTP {response.status}")
                except Exception as e:
                    logger.error(f"Failed to set Discord event thumbnail: {str(e)}")
            
            # Create announcement embed with thumbnail
            embed = discord.Embed(
                title=f"🎉 新しいイベントが追加されました！",
                description=f"**{title}**",
                color=0x3498db,
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(
                name="👨‍🏫 講師",
                value=instructor,
                inline=True
            )
            
            embed.add_field(
                name="📅 日時",
                value=start_time.strftime('%Y年%m月%d日 %H:%M JST'),
                inline=True
            )
            
            embed.add_field(
                name="📺 配信",
                value=youtube_link or 'YouTube Live (URL後日公開)',
                inline=False
            )
            
            embed.add_field(
                name="🔗 Discord イベント",
                value=f"[イベントページ]({discord_event.url})",
                inline=True
            )
            
            embed.add_field(
                name="🎫 申込み",
                value=peatix_link or 'Peatix (URL後日公開)',
                inline=True
            )
            
            # Set thumbnail image for embed
            if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)
            
            embed.set_footer(text="皆さんのご参加をお待ちしています！ 🚀")
            
            # Create announcement message
            announcement_text = f"""
皆さんのご参加をお待ちしています！ 🚀

#SkillFreak #イベント #プログラミング
            """.strip()
            
            # Post to main channel
            main_channel_id = int(settings.DISCORD_NOTIFICATION_CHANNEL_ID)
            main_channel = guild.get_channel(main_channel_id)
            
            main_message = None
            if main_channel:
                main_message = await main_channel.send(content=announcement_text, embed=embed)
            
            return {
                "discord_event": {
                    "event_id": discord_event.id,
                    "event_name": discord_event.name,
                    "event_url": discord_event.url,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "location": discord_event.location
                },
                "announcements": {
                    "main_channel": {
                        "message_id": main_message.id if main_message else None,
                        "channel_id": main_channel_id,
                        "channel_name": main_channel.name if main_channel else None
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating Discord event and announcement: {str(e)}")
            raise

# Global automation service instance
event_automation_service = EventAutomationService()