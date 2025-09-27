#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import asyncio
import discord
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

async def main():
    # 環境変数から設定を取得
    bot_token = os.getenv('DISCORD_BOT_TOKEN')
    guild_id = int(os.getenv('DISCORD_GUILD_ID'))
    
    if not bot_token:
        print("❌ DISCORD_BOT_TOKEN not found in environment variables")
        return
    
    # イベントデータを読み込み
    try:
        with open('morrie_oct_2025_event_1.json', 'r', encoding='utf-8') as f:
            event_data = json.load(f)
        print("✅ Event data loaded successfully")
    except FileNotFoundError:
        print("❌ Event data file not found: morrie_oct_2025_event_1.json")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing event data: {e}")
        return
    
    # Discord Intentsを設定
    intents = discord.Intents.default()
    intents.guilds = True
    intents.guild_scheduled_events = True
    
    # Discordクライアントを初期化
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        print(f"✅ Bot logged in as {client.user}")
        
        try:
            # ギルドを取得
            guild = client.get_guild(guild_id)
            if not guild:
                print(f"❌ Guild with ID {guild_id} not found")
                return
            
            print(f"✅ Guild found: {guild.name}")
            
            # イベント詳細を抽出
            title = event_data.get('title', 'Unknown Event')
            instructor_data = event_data.get('instructor', [])
            instructor = instructor_data[0].get('text', 'Unknown Instructor') if instructor_data else 'Unknown Instructor'
            
            # リンクを抽出（fieldsから）
            fields = event_data.get('fields', {})
            youtube_link = 'No YouTube link'
            peatix_link = 'No Peatix link'
            
            # YouTube_セミナーフィールドを探す
            for key, value in fields.items():
                if 'YouTube' in key or 'セミナー' in key:
                    if isinstance(value, list) and value:
                        youtube_link = value[0].get('link', youtube_link)
                    elif isinstance(value, dict):
                        youtube_link = value.get('link', youtube_link)
                elif 'Peatix' in key and 'メイン' in key:
                    if isinstance(value, list) and value:
                        peatix_link = value[0].get('link', peatix_link)
                    elif isinstance(value, dict):
                        peatix_link = value.get('link', peatix_link)
            
            print(f"📝 Event title: {title}")
            print(f"👨‍🏫 Instructor: {instructor}")
            print(f"🔗 YouTube link: {youtube_link}")
            print(f"🎫 Peatix link: {peatix_link}")
            
            # 開始時間と終了時間を設定（2025年10月3日 21:30-23:00 UTC）
            start_time = datetime(2025, 10, 3, 21, 30, 0, tzinfo=timezone.utc)
            end_time = datetime(2025, 10, 3, 23, 0, 0, tzinfo=timezone.utc)
            
            # 過去の日付の場合は1週間後に調整
            now = datetime.now(timezone.utc)
            if start_time < now:
                days_to_add = 7
                start_time = start_time + timedelta(days=days_to_add)
                end_time = end_time + timedelta(days=days_to_add)
                print(f"⏰ Event time adjusted to future: {start_time}")
            
            # イベント説明を作成
            description = f"""🎯 **{title}**

👨‍🏫 **講師:** {instructor}

📅 **開催日時:**
開始: {start_time.strftime('%Y年%m月%d日 %H:%M UTC')}
終了: {end_time.strftime('%Y年%m月%d日 %H:%M UTC')}

🔗 **配信リンク:**
{youtube_link}

🎫 **申し込み:**
{peatix_link}

📝 **イベント詳細:**
Larkから取得した実際のイベントデータを使用して作成されました。

🆔 **Record ID:** {event_data['record_id']}
"""
            
            # Discordスケジュールイベントを作成
            scheduled_event = await guild.create_scheduled_event(
                name=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                location=youtube_link,
                entity_type=discord.EntityType.external,
                privacy_level=discord.PrivacyLevel.guild_only
            )
            
            print(f"✅ Discord scheduled event created successfully!")
            print(f"📝 Event ID: {scheduled_event.id}")
            print(f"🔗 Event URL: {scheduled_event.url}")
            print(f"📅 Start time: {scheduled_event.start_time}")
            print(f"📅 End time: {scheduled_event.end_time}")
            print(f"📍 Location: {scheduled_event.location}")
            
            # イベント情報を保存
            event_info = {
                'event_id': scheduled_event.id,
                'event_name': scheduled_event.name,
                'event_url': scheduled_event.url,
                'guild_id': guild.id,
                'guild_name': guild.name,
                'start_time': scheduled_event.start_time.isoformat(),
                'end_time': scheduled_event.end_time.isoformat(),
                'location': scheduled_event.location,
                'description': description,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'source_record_id': event_data['record_id'],
                'source': 'manus_oct3_2025',
                'instructor': instructor,
                'youtube_link': youtube_link,
                'peatix_link': peatix_link,
                'note': 'Real Lark data used for Manus seminar event creation with timezone awareness'
            }
            
            with open('discord_manus_oct3_event_created.json', 'w', encoding='utf-8') as f:
                json.dump(event_info, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Event information saved to discord_manus_oct3_event_created.json")
            
        except Exception as e:
            print(f"❌ Error creating scheduled event: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await client.close()
    
    # Botを起動
    try:
        await client.start(bot_token)
    except Exception as e:
        print(f"❌ Failed to start Discord bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())