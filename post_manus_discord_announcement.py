#!/usr/bin/env python3
"""
2025年10月3日のモーリーさんのManusセミナーのDiscord告知を投稿するスクリプト
"""

import os
import sys
import json
import asyncio
import discord
from datetime import datetime, timezone
from dotenv import load_dotenv

async def main():
    # 環境変数を読み込み
    load_dotenv()
    
    # Discord設定
    bot_token = os.getenv('DISCORD_BOT_TOKEN')
    guild_id = int(os.getenv('DISCORD_GUILD_ID'))
    notification_channel_id = int(os.getenv('DISCORD_NOTIFICATION_CHANNEL_ID'))
    
    # イベントデータを読み込み
    with open('morrie_oct_2025_event_1.json', 'r', encoding='utf-8') as f:
        event_data = json.load(f)
    
    # Discord Intentsを設定（特権インテントを無効化）
    intents = discord.Intents.default()
    intents.message_content = False
    intents.members = False
    intents.presences = False
    
    # Discordクライアントを初期化
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        try:
            print(f'✅ Discord Bot logged in as {client.user}')
            
            # ギルドとチャンネルを取得
            guild = client.get_guild(guild_id)
            if not guild:
                print(f"❌ Guild not found: {guild_id}")
                return
            
            channel = guild.get_channel(notification_channel_id)
            if not channel:
                print(f"❌ Channel not found: {notification_channel_id}")
                return
            
            print(f"📢 Posting to channel: {channel.name}")
            
            # イベント情報を抽出
            fields = event_data['fields']
            title = fields.get('イベントタイトル', 'タイトル不明')
            instructor = 'モーリー'
            
            # 日時情報を抽出
            start_timestamp = fields.get('イベント開始日時', 0)
            end_timestamp = fields.get('イベント終了日時', 0)
            
            # タイムスタンプをdatetimeに変換（ミリ秒なので1000で割る）
            start_time = datetime.fromtimestamp(start_timestamp / 1000, tz=timezone.utc)
            end_time = datetime.fromtimestamp(end_timestamp / 1000, tz=timezone.utc)
            
            # 日本時間での表示用
            start_time_jst = start_time.strftime('%Y年%m月%d日 %H:%M')
            end_time_jst = end_time.strftime('%H:%M')
            
            # リンク情報
            youtube_link = fields.get('セミナーURL', {}).get('link', '')
            peatix_link = fields.get('本番Peatixページ', {}).get('link', '')
            thumbnail_url = fields.get('サムネイル', [{}])[0].get('url', '') if fields.get('サムネイル') else ''
            
            # Embedを作成
            embed = discord.Embed(
                title=f"🎯 {title}",
                description=f"**講師:** {instructor}\\n\\n**開催日時:**\\n{start_time_jst} - {end_time_jst} (JST)\\n\\n**配信リンク:**\\n{youtube_link}\\n\\n**申し込み:**\\n{peatix_link}",
                color=0x00ff00,
                timestamp=datetime.now(timezone.utc)
            )
            
            # サムネイル画像を設定
            if thumbnail_url:
                embed.set_image(url=thumbnail_url)
            
            embed.set_footer(text="SkillFreak Events | Larkから自動投稿")
            
            # メッセージを投稿
            message = await channel.send(embed=embed)
            
            print(f"✅ Discord announcement posted successfully!")
            print(f"📝 Message ID: {message.id}")
            print(f"🔗 Message URL: {message.jump_url}")
            
            # 投稿情報を保存
            post_info = {
                'message_id': message.id,
                'channel_id': channel.id,
                'guild_id': guild.id,
                'event_title': title,
                'instructor': instructor,
                'start_time': start_time_jst,
                'end_time': end_time_jst,
                'thumbnail_url': thumbnail_url,
                'youtube_link': youtube_link,
                'peatix_link': peatix_link,
                'posted_at': datetime.now().isoformat(),
                'source_record_id': event_data['record_id'],
                'source': 'manus_oct3_2025'
            }
            
            with open('discord_manus_oct3_announcement_post.json', 'w', encoding='utf-8') as f:
                json.dump(post_info, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Post information saved to discord_manus_oct3_announcement_post.json")
            
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