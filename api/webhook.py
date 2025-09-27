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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

async def download_thumbnail_image(url: str, access_token: str) -> bytes:
    """Download thumbnail image from URL and return as bytes"""
    try:
        print(f"Attempting to download thumbnail from: {url}")
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                print(f"Response status: {response.status}")
                if response.status == 200:
                    content = await response.read()
                    print(f"Downloaded {len(content)} bytes")
                    return content
                else:
                    print(f"Failed to download: HTTP {response.status}")
                    response_text = await response.text()
                    print(f"Response body: {response_text}")
    except Exception as e:
        print(f"Failed to download thumbnail: {e}")
        import traceback
        traceback.print_exc()
    return None

async def create_discord_event_and_announcement(event_data: Dict[str, Any]):
    """Discord scheduled event and announcement creation"""
    
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
        title = "Unknown Event"
        instructor = "Unknown Instructor"
        
        # Get links, thumbnail, datetime, and content from real Lark data
        youtube_link = None
        peatix_link = None
        thumbnail_url = None
        event_start_timestamp = None
        event_end_timestamp = None
        event_overview = None
        benefits_available = False
        
        for field_name, field_value in fields.items():
            if "イベントタイトル" in field_name and field_value:
                title = field_value
            elif field_name == "登壇者" and field_value:
                if isinstance(field_value, list):
                    # Handle list of dictionaries with 'text' field
                    instructor_names = []
                    for item in field_value:
                        if isinstance(item, dict) and 'text' in item:
                            instructor_names.append(item['text'])
                        elif isinstance(item, str):
                            instructor_names.append(item)
                        else:
                            instructor_names.append(str(item))
                    instructor = ", ".join(instructor_names)
                else:
                    instructor = str(field_value)
            elif "Peatix確認" in field_name and field_value:
                # Extract instructor name from Peatix confirmation field
                if isinstance(field_value, list) and len(field_value) > 0:
                    peatix_user = field_value[0]
                    if isinstance(peatix_user, dict):
                        instructor = peatix_user.get("name", peatix_user.get("en_name", "Unknown Instructor"))
                    else:
                        instructor = str(peatix_user)
                elif isinstance(field_value, dict) and "users" in field_value:
                    # Handle case where field_value has 'users' key
                    users = field_value["users"]
                    if isinstance(users, list) and len(users) > 0:
                        user = users[0]
                        if isinstance(user, dict):
                            instructor = user.get("name", user.get("enName", "Unknown Instructor"))
                        else:
                            instructor = str(user)
            elif "セミナーURL" in field_name and field_value:
                if isinstance(field_value, dict) and "link" in field_value:
                    youtube_link = field_value["link"]
                else:
                    youtube_link = field_value
            elif "本番Peatixページ" in field_name and field_value:
                if isinstance(field_value, dict) and "link" in field_value:
                    peatix_link = field_value["link"]
                else:
                    peatix_link = field_value
            elif "サムネイル" in field_name and field_value:
                if isinstance(field_value, list) and len(field_value) > 0:
                    thumbnail_url = field_value[0].get("url")
            elif "イベント開始日時" in field_name and field_value:
                event_start_timestamp = field_value
            elif "イベント終了日時" in field_name and field_value:
                event_end_timestamp = field_value
            elif "イベント概要" in field_name and field_value:
                event_overview = field_value
            elif "特典配布" in field_name and field_value:
                benefits_available = bool(field_value)
        
        # Download thumbnail image
        thumbnail_bytes = None
        if thumbnail_url:
            # Get Lark access token for downloading thumbnail
            access_token = await get_lark_access_token()
            if access_token:
                thumbnail_bytes = await download_thumbnail_image(thumbnail_url, access_token)
            else:
                print("Failed to get Lark access token for thumbnail download")
        
        # Parse event datetime from real Lark data
        event_start_time = None
        event_end_time = None
        
        # Convert Unix timestamps directly to datetime objects
        if event_start_timestamp:
            try:
                # Convert Lark timestamp (Unix milliseconds) to datetime
                if isinstance(event_start_timestamp, (int, float)):
                    event_start_time = datetime.fromtimestamp(event_start_timestamp / 1000, tz=timezone.utc)
                else:
                    print(f"Unexpected event_start_timestamp format: {event_start_timestamp}")
            except Exception as e:
                print(f"Error parsing event start timestamp: {e}")
        
        if event_end_timestamp:
            try:
                # Convert Lark timestamp (Unix milliseconds) to datetime
                if isinstance(event_end_timestamp, (int, float)):
                    event_end_time = datetime.fromtimestamp(event_end_timestamp / 1000, tz=timezone.utc)
                else:
                    print(f"Unexpected event_end_timestamp format: {event_end_timestamp}")
            except Exception as e:
                print(f"Error parsing event end timestamp: {e}")
        
        # Fallback to default times if parsing failed
        if not event_start_time or not event_end_time:
            print("Using fallback datetime values")
            now = datetime.now(timezone.utc)
            event_start_time = now + timedelta(days=7)  # 1 week from now
            event_end_time = event_start_time + timedelta(hours=2)
        
        # Convert to JST (Japan Standard Time)
        jst = timezone(timedelta(hours=9))
        event_start_jst = event_start_time.astimezone(jst)
        event_end_jst = event_end_time.astimezone(jst)
        
        # Japanese weekday mapping
        weekdays_jp = {
            'Mon': '月', 'Tue': '火', 'Wed': '水', 'Thu': '木', 
            'Fri': '金', 'Sat': '土', 'Sun': '日'
        }
        weekday_jp = weekdays_jp.get(event_start_jst.strftime('%a'), event_start_jst.strftime('%a'))
        
        # Create enhanced event description with Lark data
        event_description = f"""🎯 **{title}**

👨‍🏫 **講師**: {instructor}

📅 **開催日時**:
{event_start_jst.strftime('%Y年%m月%d日')}({weekday_jp}) {event_start_jst.strftime('%H:%M')}~{event_end_jst.strftime('%H:%M')}

🔗 **配信リンク**:
{youtube_link or 'YouTube Live (URL後日公開)'}

🎫 **申し込み**:
{peatix_link or 'Peatix (URL後日公開)'}

📝 **イベント詳細**:
{event_overview or '実践的な内容で学べるセミナーです。業務効率化や自動化に興味がある方におすすめです。'}

#SkillFreak #プログラミング #自動化 #業務効率化"""
        
        # Create Discord scheduled event
        event_params = {
            "name": title,
            "description": event_description,
            "start_time": event_start_time,
            "end_time": event_end_time,
            "location": youtube_link or "YouTube Live",
            "entity_type": discord.EntityType.external,
            "privacy_level": discord.PrivacyLevel.guild_only
        }
        
        discord_event = await guild.create_scheduled_event(**event_params)
        
        # Set cover image if available
        if thumbnail_bytes:
            try:
                # For external events, we need to provide location and end_time when editing
                await discord_event.edit(
                    image=thumbnail_bytes,
                    location=youtube_link or "YouTube Live",
                    end_time=event_end_time
                )
                print("Successfully set cover image for Discord event")
            except Exception as e:
                print(f"Failed to set cover image: {e}")
                # Try alternative parameter names for different discord.py versions
                try:
                    await discord_event.edit(
                        cover=thumbnail_bytes,
                        location=youtube_link or "YouTube Live", 
                        end_time=event_end_time
                    )
                    print("Successfully set cover image using 'cover' parameter")
                except Exception as e2:
                    print(f"Failed with both 'image' and 'cover' parameters: {e2}")
        
        # Create enhanced announcement with Lark data
        benefits_section = ""
        if benefits_available:
            benefits_section = "\n\n🎁 **特典あり**\n参加者限定の特典をご用意しています！"
        
        # Convert to JST for announcement
        jst_timezone = timezone(timedelta(hours=9))
        jst_start_time = event_start_time.astimezone(jst_timezone)
        jst_end_time = event_end_time.astimezone(jst_timezone)
        
        # Japanese weekday mapping
        weekdays_jp = {
            0: '月', 1: '火', 2: '水', 3: '木', 4: '金', 5: '土', 6: '日'
        }
        weekday_jp = weekdays_jp[jst_start_time.weekday()]
        
        announcement_text = f"""🎉 **新しいイベントのお知らせ** 🎉

**{title}**

📅 **日時**: {jst_start_time.strftime('%Y年%m月%d日')}({weekday_jp}) {jst_start_time.strftime('%H:%M')}~{jst_end_time.strftime('%H:%M')}
🏢 **会場**: オンライン配信
💰 **料金**: 無料
👥 **定員**: 制限なし
👨‍🏫 **講師**: {instructor}

📝 **イベント概要**
{event_overview or '実践的な内容で学べるセミナーです。業務効率化や自動化に興味がある方におすすめです。'}{benefits_section}

🔗 **YouTube Live**: {youtube_link or 'URL後日公開'}
🎫 **申し込み**: {peatix_link or 'URL後日公開'}
📅 **Discordイベント**: {discord_event.url}

🏷️ **タグ**
#SkillFreak #プログラミング #自動化 #業務効率化 #実践

皆様のご参加をお待ちしております！ 🚀"""
        

        
        # Post to channel
        channel = guild.get_channel(DISCORD_NOTIFICATION_CHANNEL_ID)
        if not channel:
            channel = await guild.fetch_channel(DISCORD_NOTIFICATION_CHANNEL_ID)
        
        # Send simple text message without embed
        message = await channel.send(content=announcement_text)
        
        return {
            "success": True,
            "discord_event": {
                "id": discord_event.id,
                "name": discord_event.name,
                "url": discord_event.url,
                "start_time": discord_event.start_time.isoformat() if discord_event.start_time else None,
                "end_time": discord_event.end_time.isoformat() if discord_event.end_time else None,
                "description": discord_event.description,
                "has_cover": thumbnail_bytes is not None
            },
            "announcement": {
                "message_id": message.id,
                "channel_id": channel.id,
                "has_thumbnail": thumbnail_url is not None
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