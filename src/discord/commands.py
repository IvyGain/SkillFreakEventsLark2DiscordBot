"""
Discord コマンド機能
追加のコマンドやスラッシュコマンドを定義
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional
from datetime import datetime, timedelta

from ..lark.client import LarkClient, LarkAPIError
from .formatters import DiscordFormatter

logger = logging.getLogger(__name__)


class SlashCommands(commands.Cog):
    """スラッシュコマンド"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="events", description="イベント情報を表示")
    @app_commands.describe(
        period="表示期間",
        days="日数（過去または未来）"
    )
    @app_commands.choices(period=[
        app_commands.Choice(name="今日", value="today"),
        app_commands.Choice(name="明日", value="tomorrow"),
        app_commands.Choice(name="今週", value="week"),
        app_commands.Choice(name="過去", value="past"),
        app_commands.Choice(name="未来", value="future")
    ])
    async def events_slash(self, interaction: discord.Interaction, 
                          period: str = "today", 
                          days: Optional[int] = None):
        """イベント情報をスラッシュコマンドで表示"""
        await interaction.response.defer()
        
        try:
            async with LarkClient() as lark_client:
                if period == "today":
                    events = await lark_client.get_today_events()
                    embed = DiscordFormatter.create_today_events_embed(events)
                    
                elif period == "tomorrow":
                    # 明日のイベント取得ロジック（実装が必要）
                    embed = DiscordFormatter.create_info_embed(
                        "明日のイベント表示機能は開発中です。"
                    )
                    
                elif period == "week":
                    # 今週のイベント取得ロジック（実装が必要）
                    embed = DiscordFormatter.create_info_embed(
                        "今週のイベント表示機能は開発中です。"
                    )
                    
                elif period == "past":
                    days = days or 7
                    events = await lark_client.get_past_events(days_back=days)
                    
                    if not events:
                        embed = DiscordFormatter.create_info_embed(
                            f"過去{days}日間にイベントはありませんでした。"
                        )
                    else:
                        embed = discord.Embed(
                            title=f"📅 過去{days}日間のイベント",
                            description=f"**{len(events)}件** のイベントが見つかりました。",
                            color=DiscordFormatter.COLORS['info'],
                            timestamp=datetime.now()
                        )
                        
                        for event in events[:10]:  # 最大10件まで表示
                            embed.add_field(
                                name=f"{event.get_status_emoji()} {event.event_name}",
                                value=f"📅 {event.get_formatted_date()}\n🕐 {event.get_formatted_time()}",
                                inline=True
                            )
                        
                        if len(events) > 10:
                            embed.add_field(
                                name="その他",
                                value=f"他に{len(events) - 10}件のイベントがあります。",
                                inline=False
                            )
                
                else:
                    embed = DiscordFormatter.create_error_embed(
                        "無効な期間が指定されました。"
                    )
            
            await interaction.followup.send(embed=embed)
            
        except LarkAPIError as e:
            error_embed = DiscordFormatter.create_error_embed(
                f"Larkからイベント情報を取得できませんでした: {e.message}"
            )
            await interaction.followup.send(embed=error_embed)
            
        except Exception as e:
            logger.error(f"Error in events slash command: {str(e)}")
            error_embed = DiscordFormatter.create_error_embed(
                "予期しないエラーが発生しました。"
            )
            await interaction.followup.send(embed=error_embed)
    
    @app_commands.command(name="archive-manual", description="手動でアーカイブを実行")
    @app_commands.describe(days="アーカイブする過去の日数（1-30）")
    @app_commands.default_permissions(manage_channels=True)
    async def archive_manual_slash(self, interaction: discord.Interaction, days: int = 1):
        """手動アーカイブのスラッシュコマンド"""
        if days < 1 or days > 30:
            embed = DiscordFormatter.create_error_embed(
                "日数は1〜30の範囲で指定してください。"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
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
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in archive slash command: {str(e)}")
            error_embed = DiscordFormatter.create_error_embed(
                "アーカイブ処理中にエラーが発生しました。"
            )
            await interaction.followup.send(embed=error_embed)
    
    @app_commands.command(name="bot-info", description="Botの情報を表示")
    async def bot_info_slash(self, interaction: discord.Interaction):
        """Bot情報のスラッシュコマンド"""
        await interaction.response.defer()
        
        try:
            # Lark接続テスト
            async with LarkClient() as lark_client:
                await lark_client._get_access_token()
                lark_status = "✅ 接続OK"
        except Exception:
            lark_status = "❌ 接続エラー"
        
        embed = discord.Embed(
            title="🤖 Lark Events Bot",
            description="LarkのイベントテーブルとDiscordを連携するBotです。",
            color=DiscordFormatter.COLORS['primary'],
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Lark API", value=lark_status, inline=True)
        embed.add_field(name="Discord", value="✅ 接続OK", inline=True)
        embed.add_field(name="サーバー数", value=f"{len(self.bot.guilds)}個", inline=True)
        
        embed.add_field(
            name="主な機能",
            value="• 本日のイベント自動通知\n• イベントアーカイブ\n• 手動コマンド実行",
            inline=False
        )
        
        embed.add_field(
            name="利用可能コマンド",
            value="• `/events` - イベント表示\n• `/archive-manual` - 手動アーカイブ\n• `/bot-info` - Bot情報",
            inline=False
        )
        
        embed.set_footer(text="Lark Events Bot | 開発者: あなたの名前")
        await interaction.followup.send(embed=embed)


class AdminCommands(commands.Cog):
    """管理者専用コマンド"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='reload')
    @commands.has_permissions(administrator=True)
    async def reload_cog(self, ctx, cog_name: str = None):
        """Cogをリロード"""
        if not cog_name:
            await ctx.send("リロードするCog名を指定してください。")
            return
        
        try:
            await self.bot.reload_extension(f"src.discord.{cog_name}")
            embed = DiscordFormatter.create_success_embed(
                f"Cog `{cog_name}` をリロードしました。"
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Failed to reload cog {cog_name}: {str(e)}")
            embed = DiscordFormatter.create_error_embed(
                f"Cog `{cog_name}` のリロードに失敗しました: {str(e)}"
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='sync')
    @commands.has_permissions(administrator=True)
    async def sync_commands(self, ctx):
        """スラッシュコマンドを同期"""
        try:
            synced = await self.bot.tree.sync()
            embed = DiscordFormatter.create_success_embed(
                f"{len(synced)}個のスラッシュコマンドを同期しました。"
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Failed to sync commands: {str(e)}")
            embed = DiscordFormatter.create_error_embed(
                f"コマンド同期に失敗しました: {str(e)}"
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='test-notification')
    @commands.has_permissions(administrator=True)
    async def test_notification(self, ctx):
        """通知機能をテスト"""
        try:
            success = await self.bot.send_today_events_notification()
            
            if success:
                embed = DiscordFormatter.create_success_embed(
                    "テスト通知を送信しました。"
                )
            else:
                embed = DiscordFormatter.create_error_embed(
                    "テスト通知の送信に失敗しました。"
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Test notification failed: {str(e)}")
            embed = DiscordFormatter.create_error_embed(
                f"テスト通知でエラーが発生しました: {str(e)}"
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='logs')
    @commands.has_permissions(administrator=True)
    async def show_logs(self, ctx, lines: int = 20):
        """最新のログを表示"""
        if lines > 50:
            lines = 50
        
        try:
            # ログファイルから最新の行を読み取り
            # 実際の実装では適切なログファイルパスを指定
            embed = DiscordFormatter.create_info_embed(
                "ログ表示機能は開発中です。",
                "ログ情報"
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Failed to show logs: {str(e)}")
            embed = DiscordFormatter.create_error_embed(
                "ログの取得に失敗しました。"
            )
            await ctx.send(embed=embed)
    
    @reload_cog.error
    @sync_commands.error
    @test_notification.error
    @show_logs.error
    async def admin_command_error(self, ctx, error):
        """管理者コマンドのエラーハンドリング"""
        if isinstance(error, commands.MissingPermissions):
            embed = DiscordFormatter.create_error_embed(
                "このコマンドを実行するには管理者権限が必要です。"
            )
            await ctx.send(embed=embed)


# Cogの登録用関数
async def setup_commands(bot):
    """コマンドCogをBotに追加"""
    await bot.add_cog(SlashCommands(bot))
    await bot.add_cog(AdminCommands(bot))