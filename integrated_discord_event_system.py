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
    channel_id = int(os.getenv('DISCORD_NOTIFICATION_CHANNEL_ID'))
    kokuchi_channel_id = int(os.getenv('DISCORD_KOKUCHI_CHANNEL_ID', os.getenv('DISCORD_NOTIFICATION_CHANNEL_ID')))
    
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
    # message_contentは特権インテントなので無効化
    
    # Discordクライアントを初期化
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        print(f"✅ Bot logged in as {client.user}")
        
        try:
            # ギルドとチャンネルを取得
            guild = client.get_guild(guild_id)
            channel = client.get_channel(channel_id)
            kokuchi_channel = client.get_channel(kokuchi_channel_id)
            
            if not guild:
                print(f"❌ Guild with ID {guild_id} not found")
                return
            if not channel:
                print(f"❌ Channel with ID {channel_id} not found")
                return
            
            print(f"✅ Guild found: {guild.name}")
            print(f"✅ Main channel found: {channel.name}")
            if kokuchi_channel:
                print(f"✅ Kokuchi channel found: {kokuchi_channel.name}")
            
            # イベント詳細を抽出
            title = event_data.get('title', 'Unknown Event')
            instructor_data = event_data.get('instructor', [])
            instructor = instructor_data[0].get('text', 'Unknown Instructor') if instructor_data else 'Unknown Instructor'
            
            # リンクを抽出
            fields = event_data.get('fields', {})
            youtube_link = 'オンライン配信'
            peatix_link = 'https://skillfreak.peatix.com/'
            thumbnail_url = None
            
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
                elif 'サムネイル' in key or 'thumbnail' in key.lower():
                    if isinstance(value, list) and value:
                        thumbnail_url = value[0].get('link')
                    elif isinstance(value, dict):
                        thumbnail_url = value.get('link')
            
            # 開始時間と終了時間を設定
            start_time = datetime(2025, 10, 3, 21, 30, 0, tzinfo=timezone.utc)
            end_time = datetime(2025, 10, 3, 23, 0, 0, tzinfo=timezone.utc)
            
            # 過去の日付の場合は1週間後に調整
            now = datetime.now(timezone.utc)
            if start_time < now:
                days_to_add = 7
                start_time = start_time + timedelta(days=days_to_add)
                end_time = end_time + timedelta(days=days_to_add)
                print(f"⏰ Event time adjusted to future: {start_time}")
            
            print(f"📝 Event title: {title}")
            print(f"👨‍🏫 Instructor: {instructor}")
            print(f"🔗 YouTube link: {youtube_link}")
            print(f"🎫 Peatix link: {peatix_link}")
            
            # === STEP 1: Discordスケジュールイベントを作成 ===
            event_description = f"""🎯 **{title}**

👨‍🏫 **講師:** {instructor}

📅 **開催日時:**
開始: {start_time.strftime('%Y年%m月%d日 %H:%M UTC')}
終了: {end_time.strftime('%Y年%m月%d日 %H:%M UTC')}

🔗 **配信リンク:**
{youtube_link}

🎫 **申し込み:**
{peatix_link}

📝 **イベント詳細:**
Manusを活用した業務自動化の実践的な手法を学べるセミナーです。他ツールとの連携方法も詳しく解説します。

🆔 **Record ID:** {event_data['record_id']}
"""
            
            scheduled_event = await guild.create_scheduled_event(
                name=title,
                description=event_description,
                start_time=start_time,
                end_time=end_time,
                location=youtube_link,
                entity_type=discord.EntityType.external,
                privacy_level=discord.PrivacyLevel.guild_only
            )
            
            print(f"✅ Discord scheduled event created!")
            print(f"📝 Event ID: {scheduled_event.id}")
            print(f"🔗 Event URL: {scheduled_event.url}")
            
            # === STEP 2: 詳細な告知メッセージを作成 ===
            event_date = "2025年10月3日（金）"
            event_time = "21:30 - 23:00"
            
            announcement_text = f"""🎉 **新しいイベントのお知らせ** 🎉

**{title}**

📅 **日時**: {event_date} {event_time}
🏢 **会場**: オンライン配信
💰 **料金**: 無料
👥 **定員**: 制限なし
🎫 **申込**: {peatix_link}

**📝 イベント概要**
Manusを活用した業務自動化の実践的な手法を学べるセミナーです。他ツールとの連携方法も詳しく解説します。

【内容】
・Manusの基本機能と活用方法
・他ツールとの連携実践
・業務自動化のベストプラクティス
・実際の導入事例紹介
・Q&Aセッション

【対象者】
・業務効率化に興味がある方
・Manusを活用したい方
・自動化ツールの連携を学びたい方
・実践的なスキルを身につけたい方

【講師】
{instructor} - 業務自動化のエキスパート、多数の導入実績を持つ

**🔗 Discordイベント**: {scheduled_event.url}

**🏷️ タグ**
#Manus #業務自動化 #ツール連携 #効率化 #実践

皆様のご参加をお待ちしております！ 🚀"""

            # Embedを作成
            embed = discord.Embed(
                title=f"🎯 {title}",
                description=f"**講師**: {instructor}\n**日時**: {event_date} {event_time}",
                color=0x00ff00,
                timestamp=datetime.now(timezone.utc)
            )
            
            if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)
            
            embed.add_field(name="🏢 会場", value="オンライン配信", inline=True)
            embed.add_field(name="💰 料金", value="無料", inline=True)
            embed.add_field(name="👥 定員", value="制限なし", inline=True)
            embed.add_field(name="🔗 配信URL", value=f"[YouTube Live]({youtube_link})", inline=False)
            embed.add_field(name="🎫 申込み", value=f"[Peatixで申込]({peatix_link})", inline=False)
            embed.add_field(name="📅 Discordイベント", value=f"[イベントページ]({scheduled_event.url})", inline=False)
            
            embed.set_footer(text=f"Record ID: {event_data.get('record_id', 'N/A')}")
            
            # === STEP 3: メインチャンネルに投稿 ===
            main_message = await channel.send(content=announcement_text, embed=embed)
            print(f"✅ Announcement posted to main channel: {main_message.id}")
            
            # === STEP 4: イベントコクチチャンネルにも投稿 ===
            kokuchi_message = None
            if kokuchi_channel and kokuchi_channel.id != channel.id:
                # イベントコクチ用の簡潔なメッセージ
                kokuchi_text = f"""📢 **イベント告知** 📢

**{title}**

📅 **{event_date} {event_time}**
👨‍🏫 **講師**: {instructor}

🔗 **Discordイベント**: {scheduled_event.url}
🎫 **申込**: {peatix_link}

詳細は上記のDiscordイベントページをご確認ください！"""

                kokuchi_embed = discord.Embed(
                    title=f"📅 {title}",
                    description=f"講師: {instructor}",
                    color=0xff6b35,
                    url=scheduled_event.url
                )
                
                if thumbnail_url:
                    kokuchi_embed.set_thumbnail(url=thumbnail_url)
                
                kokuchi_embed.add_field(name="日時", value=f"{event_date} {event_time}", inline=False)
                kokuchi_embed.add_field(name="Discordイベント", value=f"[参加表明はこちら]({scheduled_event.url})", inline=False)
                
                kokuchi_message = await kokuchi_channel.send(content=kokuchi_text, embed=kokuchi_embed)
                print(f"✅ Event posted to kokuchi channel: {kokuchi_message.id}")
            
            # === STEP 5: 結果を保存 ===
            result_info = {
                'discord_event': {
                    'event_id': scheduled_event.id,
                    'event_name': scheduled_event.name,
                    'event_url': scheduled_event.url,
                    'start_time': scheduled_event.start_time.isoformat(),
                    'end_time': scheduled_event.end_time.isoformat(),
                    'location': scheduled_event.location
                },
                'announcements': {
                    'main_channel': {
                        'message_id': main_message.id,
                        'channel_id': channel.id,
                        'channel_name': channel.name
                    },
                    'kokuchi_channel': {
                        'message_id': kokuchi_message.id if kokuchi_message else None,
                        'channel_id': kokuchi_channel.id if kokuchi_channel else None,
                        'channel_name': kokuchi_channel.name if kokuchi_channel else None
                    } if kokuchi_channel else None
                },
                'event_details': {
                    'title': title,
                    'instructor': instructor,
                    'event_date': event_date,
                    'event_time': event_time,
                    'youtube_link': youtube_link,
                    'peatix_link': peatix_link,
                    'thumbnail_url': thumbnail_url
                },
                'metadata': {
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'source_record_id': event_data.get('record_id'),
                    'source': 'integrated_manus_oct3_2025',
                    'note': 'Integrated system: Discord event creation + dual channel announcements'
                }
            }
            
            with open('integrated_discord_system_result.json', 'w', encoding='utf-8') as f:
                json.dump(result_info, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Complete system result saved to integrated_discord_system_result.json")
            print(f"🎉 Integration complete! Event created and announced in both channels.")
            
        except Exception as e:
            print(f"❌ Error in integrated system: {e}")
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