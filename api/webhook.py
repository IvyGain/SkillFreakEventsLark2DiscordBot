"""
Vercel Serverless Function for Lark Webhook
"""

import json
import os
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
import discord
import aiohttp

# Environment variables
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_GUILD_ID = int(os.getenv('DISCORD_GUILD_ID', '0'))
DISCORD_NOTIFICATION_CHANNEL_ID = int(os.getenv('DISCORD_NOTIFICATION_CHANNEL_ID', '0'))
LARK_APP_ID = os.getenv('LARK_APP_ID')
LARK_APP_SECRET = os.getenv('LARK_APP_SECRET')
LARK_TABLE_ID = os.getenv('LARK_TABLE_ID')

async def get_lark_access_token():
    """Get Lark access token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {
        "app_id": LARK_APP_ID,
        "app_secret": LARK_APP_SECRET
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            result = await response.json()
            return result.get("app_access_token")

async def get_lark_record(record_id: str, access_token: str):
    """Get record from Lark table"""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{LARK_TABLE_ID}/tables/tblxxxxxxxxxxx/records/{record_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            result = await response.json()
            return result.get("data", {}).get("record", {})

async def create_discord_event_and_announcement(event_data: Dict[str, Any]):
    """Create Discord event and post announcement"""
    
    # Discord Intents (minimal for API calls)
    intents = discord.Intents.default()
    intents.guilds = True
    intents.guild_scheduled_events = True
    
    # Create Discord client
    client = discord.Client(intents=intents)
    
    try:
        # Login to Discord
        await client.login(DISCORD_BOT_TOKEN)
        
        # Get guild
        guild = client.get_guild(DISCORD_GUILD_ID)
        if not guild:
            # If not in cache, fetch it
            guild = await client.fetch_guild(DISCORD_GUILD_ID)
        
        # Extract event details
        fields = event_data.get("fields", {})
        title = fields.get("title", "Unknown Event")
        instructor = fields.get("instructor", "Unknown Instructor")
        
        # Get links
        youtube_link = None
        peatix_link = None
        
        for field_name, field_value in fields.items():
            if "YouTube" in field_name and field_value:
                youtube_link = field_value
            elif "Peatix" in field_name and field_value:
                peatix_link = field_value
        
        # Create start and end times
        start_time = datetime.now(timezone.utc) + timedelta(days=7)
        end_time = start_time + timedelta(hours=1, minutes=30)
        
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
        
        # Create announcement
        announcement_text = f"""
🎉 **新しいイベントが追加されました！**

**{title}**
👨‍🏫 講師: {instructor}
📅 日時: {start_time.strftime('%Y年%m月%d日 %H:%M')} JST
📺 配信: {youtube_link or 'YouTube Live (URL後日公開)'}

🔗 **Discord イベント**: {discord_event.url}
🎫 **申込み**: {peatix_link or 'Peatix (URL後日公開)'}

皆さんのご参加をお待ちしています！ 🚀

#SkillFreak #イベント #プログラミング
        """.strip()
        
        # Post to channel
        channel = guild.get_channel(DISCORD_NOTIFICATION_CHANNEL_ID)
        if not channel:
            channel = await guild.fetch_channel(DISCORD_NOTIFICATION_CHANNEL_ID)
        
        message = await channel.send(announcement_text)
        
        return {
            "success": True,
            "discord_event": {
                "event_id": discord_event.id,
                "event_name": discord_event.name,
                "event_url": discord_event.url,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            },
            "announcement": {
                "message_id": message.id,
                "channel_id": channel.id
            }
        }
        
    finally:
        await client.close()

async def handler(request):
    """Vercel serverless function handler"""
    
    if request.method == 'GET':
        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'healthy', 'message': 'Webhook endpoint is running'})
        }
    
    if request.method != 'POST':
        return {
            'statusCode': 405,
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    try:
        # Parse request body
        body = json.loads(request.body)
        
        # Extract record ID
        record_id = None
        if "record" in body:
            record_id = body["record"].get("record_id")
        elif "data" in body and "record_id" in body["data"]:
            record_id = body["data"]["record_id"]
        elif "record_id" in body:
            record_id = body["record_id"]
        
        if not record_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No record ID found'})
            }
        
        # Get Lark access token
        access_token = await get_lark_access_token()
        if not access_token:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Failed to get Lark access token'})
            }
        
        # Get event data from Lark
        event_data = await get_lark_record(record_id, access_token)
        if not event_data:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Event data not found'})
            }
        
        # Create Discord event and announcement
        result = await create_discord_event_and_announcement(event_data)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'record_id': record_id,
                'result': result,
                'processed_at': datetime.now(timezone.utc).isoformat()
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'error': str(e),
                'processed_at': datetime.now(timezone.utc).isoformat()
            })
        }

# Vercel entry point
def handler_sync(request):
    """Synchronous wrapper for Vercel"""
    return asyncio.run(handler(request))