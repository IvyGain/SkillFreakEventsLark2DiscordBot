#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import asyncio
import discord
from datetime import datetime, timezone
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

async def main():
    # 環境変数から設定を取得
    bot_token = os.getenv('DISCORD_BOT_TOKEN')
    guild_id = int(os.getenv('DISCORD_GUILD_ID'))
    channel_id = int(os.getenv('DISCORD_CHANNEL_ID'))
    kokuchi_channel_id = int(os.getenv('DISCORD_KOKUCHI_CHANNEL_ID', channel_id))  # イベントコクチチャンネル
    
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
    intents.message_content = True
    
    # Discordクライアントを初期化
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        print(f"✅ Bot logged in as {client.user}")
        
        try:
            # チャンネルを取得
            channel = client.get_channel(channel_id)
            kokuchi_channel = client.get_channel(kokuchi_channel_id)
            
            if not channel:
                print(f"❌ Channel with ID {channel_id} not found")
                return
            
            print(f"✅ Channel found: {channel.name}")
            if kokuchi_channel:
                print(f"✅ Kokuchi channel found: {kokuchi_channel.name}")
            
            # イベント詳細を抽出
            title = event_data.get('title', 'Unknown Event')
            instructor_data = event_data.get('instructor', [])
            instructor = instructor_data[0].get('text', 'Unknown Instructor') if instructor_data else 'Unknown Instructor'
            
            # 開催月情報を取得
            opening_month_data = event_data.get('opening_month', [])
            opening_month = opening_month_data[0].get('text', '2025-10') if opening_month_data else '2025-10'
            
            # リンクを抽出（fieldsから）
            fields = event_data.get('fields', {})
            youtube_link = 'オンライン配信'
            peatix_link = 'https://skillfreak.peatix.com/'
            streamyard_link = ''
            
            # 各種リンクを探す
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
                elif 'StreamYard' in key:
                    if isinstance(value, list) and value:
                        streamyard_link = value[0].get('link', '')
                    elif isinstance(value, dict):
                        streamyard_link = value.get('link', '')
            
            # 日時情報を設定
            event_date = "2025年10月3日（金）"
            event_time = "21:30 - 23:00"
            
            print(f"📝 Event title: {title}")
            print(f"👨‍🏫 Instructor: {instructor}")
            print(f"📅 Date: {event_date} {event_time}")
            print(f"🔗 YouTube link: {youtube_link}")
            print(f"🎫 Peatix link: {peatix_link}")
            
            # 詳細な告知メッセージを作成
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
            
            # サムネイル画像を設定（もしあれば）
            thumbnail_url = None
            for key, value in fields.items():
                if 'サムネイル' in key or 'thumbnail' in key.lower():
                    if isinstance(value, list) and value:
                        thumbnail_url = value[0].get('link')
                    elif isinstance(value, dict):
                        thumbnail_url = value.get('link')
                    break
            
            if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)
            
            embed.add_field(name="🏢 会場", value="オンライン配信", inline=True)
            embed.add_field(name="💰 料金", value="無料", inline=True)
            embed.add_field(name="👥 定員", value="制限なし", inline=True)
            embed.add_field(name="🔗 配信URL", value=f"[YouTube Live]({youtube_link})", inline=False)
            embed.add_field(name="🎫 申込み", value=f"[Peatixで申込]({peatix_link})", inline=False)
            
            embed.set_footer(text=f"Record ID: {event_data.get('record_id', 'N/A')}")
            
            # メインチャンネルに投稿
            message = await channel.send(content=announcement_text, embed=embed)
            print(f"✅ Announcement posted to main channel: {message.id}")
            
            # イベントコクチチャンネルにも投稿（もし設定されていれば）
            kokuchi_message = None
            if kokuchi_channel and kokuchi_channel.id != channel.id:
                kokuchi_message = await kokuchi_channel.send(content=announcement_text, embed=embed)
                print(f"✅ Announcement posted to kokuchi channel: {kokuchi_message.id}")
            
            # 投稿情報を保存
            post_info = {
                'main_channel': {
                    'message_id': message.id,
                    'channel_id': channel.id,
                    'channel_name': channel.name
                },
                'kokuchi_channel': {
                    'message_id': kokuchi_message.id if kokuchi_message else None,
                    'channel_id': kokuchi_channel.id if kokuchi_channel else None,
                    'channel_name': kokuchi_channel.name if kokuchi_channel else None
                } if kokuchi_channel else None,
                'event_title': title,
                'instructor': instructor,
                'event_date': event_date,
                'event_time': event_time,
                'youtube_link': youtube_link,
                'peatix_link': peatix_link,
                'thumbnail_url': thumbnail_url,
                'posted_at': datetime.now(timezone.utc).isoformat(),
                'source_record_id': event_data.get('record_id'),
                'source': 'improved_manus_oct3_2025',
                'note': 'Improved detailed announcement with proper formatting and dual channel posting'
            }
            
            with open('improved_discord_announcement_post.json', 'w', encoding='utf-8') as f:
                json.dump(post_info, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Post information saved to improved_discord_announcement_post.json")
            
        except Exception as e:
            print(f"❌ Error posting announcement: {e}")
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