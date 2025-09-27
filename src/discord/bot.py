"""
Discord Bot メイン機能
イベント通知とアーカイブ機能を提供
"""

import discord
from discord.ext import commands
import logging
from typing import List, Optional
from datetime import datetime
import aiohttp

from ..config.settings import get_settings
from ..lark.client import LarkClient, LarkAPIError
from ..lark.models import LarkEventRecord
from .formatters import DiscordFormatter

logger = logging.getLogger(__name__)


class EventsBot(commands.Bot):
    """イベント通知Bot"""
    
    def __init__(self):
        # Bot設定
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        self.settings = get_settings()
        self.lark_client = None
    
    async def setup_hook(self):
        """Bot起動時の初期化処理"""
        logger.info("Setting up Events Bot...")
        
        # Larkクライアントの初期化
        self.lark_client = LarkClient()
        
        # コマンドの登録
        await self.add_cog(EventCommands(self))
        
        logger.info("Events Bot setup completed")
    
    async def on_ready(self):
        """Bot準備完了時の処理"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # ステータス設定
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="Larkのイベント情報"
        )
        await self.change_presence(activity=activity)
    
    async def on_error(self, event, *args, **kwargs):
        """エラーハンドリング"""
        logger.error(f"An error occurred in event {event}", exc_info=True)
    
    async def close(self):
        """Bot終了時のクリーンアップ"""
        if self.lark_client:
            await self.lark_client.close()
        await super().close()
    
    async def send_today_events_notification(self) -> bool:
        """本日のイベント通知を送信"""
        try:
            # 通知チャンネルを取得
            channel = self.get_channel(self.settings.discord_notification_channel_id)
            if not channel:
                logger.error(f"Notification channel {self.settings.discord_notification_channel_id} not found")
                return False
            
            # Larkから今日のイベントを取得
            async with LarkClient() as lark_client:
                today_events = await lark_client.get_today_events()
            
            # Embedを作成して送信
            embed = DiscordFormatter.create_today_events_embed(today_events)
            await channel.send(embed=embed)
            
            logger.info(f"Sent today's events notification: {len(today_events)} events")
            return True
            
        except LarkAPIError as e:
            logger.error(f"Lark API error in notification: {e.message}")
            
            # エラー通知を送信
            if channel:
                error_embed = DiscordFormatter.create_error_embed(
                    f"Larkからイベント情報を取得できませんでした: {e.message}",
                    "イベント取得エラー"
                )
                await channel.send(embed=error_embed)
            
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error in notification: {str(e)}")
            return False
    
    async def create_archive_threads(self, days_back: int = 1) -> int:
        """アーカイブスレッドを作成"""
        try:
            # フォーラムチャンネルを取得
            forum_channel = self.get_channel(self.settings.discord_archive_forum_id)
            if not forum_channel or not isinstance(forum_channel, discord.ForumChannel):
                logger.error(f"Archive forum {self.settings.discord_archive_forum_id} not found or not a forum")
                return 0
            
            # Larkから過去のイベントを取得
            async with LarkClient() as lark_client:
                past_events = await lark_client.get_past_events(days_back=days_back)
            
            archived_count = 0
            
            for event in past_events:
                try:
                    # スレッド名を生成
                    thread_name = DiscordFormatter.format_thread_name(event)
                    
                    # 既存のスレッドをチェック（重複防止）
                    existing_thread = discord.utils.get(forum_channel.threads, name=thread_name)
                    if existing_thread:
                        logger.info(f"Thread already exists: {thread_name}")
                        continue
                    
                    # アーカイブEmbedを作成
                    embed = DiscordFormatter.create_event_archive_embed(event)
                    
                    # フォーラムスレッドを作成
                    thread = await forum_channel.create_thread(
                        name=thread_name,
                        content=f"イベント「{event.get_title()}」のアーカイブです。",
                        embed=embed
                    )
                    
                    logger.info(f"Created archive thread: {thread_name}")
                    archived_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to create thread for event {event.get_title()}: {str(e)}")
                    continue
            
            # アーカイブ完了通知
            if archived_count > 0:
                notification_channel = self.get_channel(self.settings.discord_notification_channel_id)
                if notification_channel:
                    summary_embed = DiscordFormatter.create_archive_summary_embed(
                        archived_count, 
                        datetime.now().strftime("%Y年%m月%d日")
                    )
                    await notification_channel.send(embed=summary_embed)
            
            logger.info(f"Archive process completed: {archived_count} threads created")
            return archived_count
            
        except LarkAPIError as e:
            logger.error(f"Lark API error in archive: {e.message}")
            return 0
            
        except Exception as e:
            logger.error(f"Unexpected error in archive: {str(e)}")
            return 0
    
    async def create_recently_ended_archive_threads(self, hours_back: int = 24) -> int:
        """最近終了したイベントのアーカイブスレッドを作成"""
        try:
            # フォーラムチャンネルを取得
            forum_channel = self.get_channel(self.settings.discord_archive_forum_id)
            if not forum_channel or not isinstance(forum_channel, discord.ForumChannel):
                logger.error(f"Archive forum {self.settings.discord_archive_forum_id} not found or not a forum")
                return 0
            
            # Larkから最近終了したイベントを取得
            async with LarkClient() as lark_client:
                recently_ended_events = await lark_client.get_recently_ended_events(hours_back=hours_back)
            
            archived_count = 0
            
            for event in recently_ended_events:
                try:
                    # スレッド名を生成
                    thread_name = DiscordFormatter.format_thread_name(event)
                    
                    # 既存のスレッドをチェック（重複防止）
                    existing_thread = discord.utils.get(forum_channel.threads, name=thread_name)
                    if existing_thread:
                        logger.info(f"Thread already exists: {thread_name}")
                        continue
                    
                    # アーカイブEmbedを作成
                    embed = DiscordFormatter.create_event_archive_embed(event)
                    
                    # フォーラムスレッドを作成
                    thread = await forum_channel.create_thread(
                        name=thread_name,
                        content=f"イベント「{event.get_title()}」のアーカイブです。",
                        embed=embed
                    )
                    
                    logger.info(f"Created archive thread for recently ended event: {thread_name}")
                    archived_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to create thread for recently ended event {event.get_title()}: {str(e)}")
                    continue
            
            # アーカイブ完了通知（終了したイベントがある場合のみ）
            if archived_count > 0:
                notification_channel = self.get_channel(self.settings.discord_notification_channel_id)
                if notification_channel:
                    summary_embed = DiscordFormatter.create_archive_summary_embed(
                        archived_count, 
                        f"過去{hours_back}時間"
                    )
                    await notification_channel.send(embed=summary_embed)
            
            logger.info(f"Recently ended events archive process completed: {archived_count} threads created")
            return archived_count
            
        except LarkAPIError as e:
            logger.error(f"Lark API error in recently ended archive: {e.message}")
            return 0
            
        except Exception as e:
            logger.error(f"Unexpected error in recently ended archive: {str(e)}")
            return 0
    
    async def create_discord_event(self, lark_event: LarkEventRecord) -> Optional[discord.ScheduledEvent]:
        """LarkイベントからDiscordイベントを作成"""
        try:
            # ギルドを取得
            guild = self.get_guild(self.settings.discord_guild_id)
            if not guild:
                logger.error(f"Guild {self.settings.discord_guild_id} not found")
                return None
            
            # イベント情報を準備
            event_title = lark_event.get_title()
            description = self._create_discord_event_description(lark_event)
            
            # 開始時間と終了時間を設定
            start_time = lark_event.event_start_datetime
            end_time = lark_event.event_end_datetime
            
            if not start_time:
                logger.error(f"Event {event_title} has no start time")
                return None
            
            # 場所の設定（オンラインかオフラインか）
            location = lark_event.location or "オンライン"
            entity_type = discord.EntityType.external if lark_event.seminar_url else discord.EntityType.voice
            
            # Discordイベントを作成
            discord_event = await guild.create_scheduled_event(
                name=event_title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                entity_type=entity_type,
                location=location if entity_type == discord.EntityType.external else None,
                privacy_level=discord.PrivacyLevel.guild_only
            )
            
            # サムネイル画像を設定（可能な場合）
            if lark_event.thumbnail_url:
                await self._set_event_image(discord_event, lark_event.thumbnail_url)
            
            logger.info(f"Created Discord event: {event_title} (ID: {discord_event.id})")
            return discord_event
            
        except Exception as e:
            logger.error(f"Failed to create Discord event for {lark_event.get_title()}: {str(e)}")
            return None
    
    def _create_discord_event_description(self, lark_event: LarkEventRecord) -> str:
        """Discordイベント用の説明文を作成"""
        description_parts = []
        
        if lark_event.description:
            description_parts.append(lark_event.description)
        
        if lark_event.speakers:
            description_parts.append(f"🎤 登壇者: {lark_event.speakers}")
        
        if lark_event.seminar_url:
            description_parts.append(f"🔗 参加URL: {lark_event.seminar_url}")
        
        if lark_event.participants:
            description_parts.append(f"👥 参加者数: {lark_event.participants}名")
        
        return "\n\n".join(description_parts)
    
    async def _set_event_image(self, discord_event: discord.ScheduledEvent, image_url: str):
        """Discordイベントにサムネイル画像を設定"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        await discord_event.edit(image=image_data)
                        logger.info(f"Set thumbnail image for event {discord_event.name}")
                    else:
                        logger.warning(f"Failed to fetch image from {image_url}: HTTP {response.status}")
        except Exception as e:
            logger.error(f"Failed to set event image: {str(e)}")
    
    async def check_and_create_events_for_published_peatix(self) -> int:
        """Peatix公開済みイベントをチェックしてDiscordイベントを作成"""
        try:
            created_count = 0
            
            # Larkから全イベントを取得
            async with LarkClient() as lark_client:
                all_events = await lark_client.get_all_events()
            
            for event in all_events:
                # Peatixが公開済みかつ未来のイベントのみ処理
                if event.is_peatix_published() and event.is_upcoming():
                    # 既存のDiscordイベントをチェック（重複作成を防ぐ）
                    if not await self._discord_event_exists(event):
                        discord_event = await self.create_discord_event(event)
                        if discord_event:
                            created_count += 1
            
            logger.info(f"Created {created_count} Discord events for published Peatix events")
            return created_count
            
        except LarkAPIError as e:
            logger.error(f"Lark API error in Peatix check: {e.message}")
            return 0
            
        except Exception as e:
            logger.error(f"Unexpected error in Peatix check: {str(e)}")
            return 0
    
    async def _discord_event_exists(self, lark_event: LarkEventRecord) -> bool:
        """指定されたLarkイベントに対応するDiscordイベントが既に存在するかチェック"""
        try:
            guild = self.get_guild(self.settings.discord_guild_id)
            if not guild:
                return False
            
            # ギルドの予定されたイベントを取得
            events = guild.scheduled_events
            event_title = lark_event.get_title()
            
            # タイトルと開始時間で重複チェック
            for discord_event in events:
                if (discord_event.name == event_title and 
                    discord_event.start_time and lark_event.event_start_datetime and
                    abs((discord_event.start_time - lark_event.event_start_datetime).total_seconds()) < 3600):  # 1時間以内の差は同じイベントとみなす
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking Discord event existence: {str(e)}")
            return False


class EventCommands(commands.Cog):
    """イベント関連のコマンド"""
    
    def __init__(self, bot: EventsBot):
        self.bot = bot
    
    @commands.command(name='today')
    async def today_events(self, ctx):
        """本日のイベントを表示"""
        try:
            async with ctx.typing():
                async with LarkClient() as lark_client:
                    today_events = await lark_client.get_today_events()
                
                embed = DiscordFormatter.create_today_events_embed(today_events)
                await ctx.send(embed=embed)
                
        except LarkAPIError as e:
            error_embed = DiscordFormatter.create_error_embed(
                f"Larkからイベント情報を取得できませんでした: {e.message}"
            )
            await ctx.send(embed=error_embed)
            
        except Exception as e:
            logger.error(f"Error in today command: {str(e)}")
            error_embed = DiscordFormatter.create_error_embed(
                "予期しないエラーが発生しました。"
            )
            await ctx.send(embed=error_embed)
    
    @commands.command(name='archive')
    @commands.has_permissions(manage_channels=True)
    async def manual_archive(self, ctx, days: int = 1):
        """手動でアーカイブを実行"""
        if days < 1 or days > 30:
            await ctx.send("日数は1〜30の範囲で指定してください。")
            return
        
        try:
            async with ctx.typing():
                archived_count = await self.bot.create_archive_threads(days_back=days)
            
            if archived_count > 0:
                embed = DiscordFormatter.create_success_embed(
                    f"過去{days}日間のイベント {archived_count}件をアーカイブしました。",
                    "アーカイブ完了"
                )
            else:
                embed = DiscordFormatter.create_info_embed(
                    f"過去{days}日間にアーカイブ対象のイベントはありませんでした。",
                    "アーカイブ結果"
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in archive command: {str(e)}")
            error_embed = DiscordFormatter.create_error_embed(
                "アーカイブ処理中にエラーが発生しました。"
            )
            await ctx.send(embed=error_embed)
    
    @commands.command(name='status')
    async def bot_status(self, ctx):
        """Bot の状態を表示"""
        try:
            # Lark接続テスト
            async with LarkClient() as lark_client:
                await lark_client._get_access_token()
                lark_status = "✅ 接続OK"
        except Exception:
            lark_status = "❌ 接続エラー"
        
        embed = discord.Embed(
            title="🤖 Bot ステータス",
            color=DiscordFormatter.COLORS['info'],
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Lark API", value=lark_status, inline=True)
        embed.add_field(name="Discord", value="✅ 接続OK", inline=True)
        embed.add_field(name="サーバー数", value=f"{len(self.bot.guilds)}個", inline=True)
        
        embed.set_footer(text="Lark Events Bot")
        await ctx.send(embed=embed)
    
    @commands.command(name='help')
    async def help_command(self, ctx):
        """ヘルプを表示"""
        embed = discord.Embed(
            title="📚 Lark Events Bot ヘルプ",
            description="Larkのイベント情報をDiscordに通知するBotです。",
            color=DiscordFormatter.COLORS['info']
        )
        
        embed.add_field(
            name="!today",
            value="本日のイベント一覧を表示",
            inline=False
        )
        
        embed.add_field(
            name="!archive [日数]",
            value="過去のイベントを手動でアーカイブ（管理者のみ）",
            inline=False
        )
        
        embed.add_field(
            name="!status",
            value="Botの接続状態を確認",
            inline=False
        )
        
        embed.add_field(
            name="自動機能",
            value="• 毎日定時に本日のイベントを通知\n• 毎日定時に過去のイベントをアーカイブ",
            inline=False
        )
        
        embed.set_footer(text="Lark Events Bot")
        await ctx.send(embed=embed)
    
    @manual_archive.error
    async def archive_error(self, ctx, error):
        """アーカイブコマンドのエラーハンドリング"""
        if isinstance(error, commands.MissingPermissions):
            embed = DiscordFormatter.create_error_embed(
                "このコマンドを実行するには「チャンネル管理」権限が必要です。"
            )
            await ctx.send(embed=embed)


# Bot インスタンスの作成と実行
def create_bot() -> EventsBot:
    """Bot インスタンスを作成"""
    return EventsBot()


async def run_bot():
    """Bot を実行"""
    bot = create_bot()
    
    try:
        await bot.start(bot.settings.discord_bot_token)
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")
        raise
    finally:
        await bot.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_bot())