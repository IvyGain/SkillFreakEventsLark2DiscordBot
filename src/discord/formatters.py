"""
Discord メッセージフォーマッター
Larkのイベントデータを Discord の Embed 形式に変換
"""

import discord
from datetime import datetime
from typing import List, Optional
from ..lark.models import LarkEventRecord


class DiscordFormatter:
    """Discord メッセージフォーマッター"""
    
    # カラーコード
    COLORS = {
        'primary': 0x3498db,      # 青
        'success': 0x2ecc71,     # 緑
        'warning': 0xf39c12,     # オレンジ
        'danger': 0xe74c3c,      # 赤
        'info': 0x9b59b6,        # 紫
        'secondary': 0x95a5a6    # グレー
    }
    
    # ステータス別カラー
    STATUS_COLORS = {
        '開催予定': COLORS['primary'],
        '開催中': COLORS['warning'],
        '終了': COLORS['success'],
        '中止': COLORS['danger'],
        '延期': COLORS['secondary']
    }
    
    @classmethod
    def create_today_events_embed(cls, events: List[LarkEventRecord]) -> discord.Embed:
        """本日のイベント告知用Embedを作成"""
        if not events:
            embed = discord.Embed(
                title="📅 本日のイベント情報",
                description="本日開催予定のイベントはありません。",
                color=cls.COLORS['info'],
                timestamp=datetime.now()
            )
            embed.set_footer(text="Lark Events Bot")
            return embed
        
        embed = discord.Embed(
            title="🎉 本日のイベント情報",
            description=f"本日は **{len(events)}件** のイベントが開催予定です！",
            color=cls.COLORS['primary'],
            timestamp=datetime.now()
        )
        
        for i, event in enumerate(events, 1):
            # イベント名（新しいフィールドを優先）
            event_title = event.get_title()
            
            # 時間情報（新しいフィールドを使用）
            if event.event_start_datetime and event.event_end_datetime:
                start_time = event.event_start_datetime.strftime("%H:%M")
                end_time = event.event_end_datetime.strftime("%H:%M")
                time_info = f"{start_time} - {end_time}"
            elif event.event_start_datetime:
                start_time = event.event_start_datetime.strftime("%H:%M")
                time_info = f"{start_time}〜"
            else:
                time_info = event.get_formatted_time()
            
            # 場所情報
            location = event.location or "場所未設定"
            
            # 参加者数
            participants = f"{event.participants}名" if event.participants else "未定"
            
            # ステータス絵文字
            status_emoji = event.get_status_emoji()
            
            # フィールド値を構築
            field_value = f"{status_emoji} **{event_title}**\n"
            field_value += f"🕐 **時間**: {time_info}\n"
            field_value += f"📍 **場所**: {location}\n"
            field_value += f"👥 **参加者**: {participants}\n"
            
            # 登壇者情報
            if event.speakers:
                field_value += f"🎤 **登壇者**: {event.speakers}\n"
            
            # セミナーURL
            if event.seminar_url:
                field_value += f"🔗 **セミナーURL**: [参加はこちら]({event.seminar_url})"
            
            if event.description:
                # 説明が長い場合は省略
                description = event.description
                if len(description) > 100:
                    description = description[:97] + "..."
                field_value += f"\n📝 **説明**: {description}"
            
            embed.add_field(
                name=f"イベント {i}",
                value=field_value,
                inline=False
            )
        
        # サムネイル画像を設定（最初のイベントのサムネイルを使用）
        if events and events[0].thumbnail_url:
            embed.set_thumbnail(url=events[0].thumbnail_url)
        
        embed.set_footer(text="Lark Events Bot | 素敵な一日をお過ごしください！")
        return embed
    
    @classmethod
    def create_event_archive_embed(cls, event: LarkEventRecord) -> discord.Embed:
        """イベントアーカイブ用Embedを作成"""
        event_title = event.get_title()
        
        # ステータスに応じたカラー
        color = cls.STATUS_COLORS.get(event.status, cls.COLORS['secondary'])
        
        embed = discord.Embed(
            title=f"📋 {event_title}",
            description="イベントアーカイブ",
            color=color,
            timestamp=datetime.now()
        )
        
        # 基本情報
        if event.event_start_datetime:
            date_str = event.event_start_datetime.strftime("%Y年%m月%d日")
        else:
            date_str = event.get_formatted_date()
            
        if event.event_start_datetime and event.event_end_datetime:
            start_time = event.event_start_datetime.strftime("%H:%M")
            end_time = event.event_end_datetime.strftime("%H:%M")
            time_str = f"{start_time} - {end_time}"
        else:
            time_str = event.get_formatted_time()
        
        basic_info = f"📅 **開催日**: {date_str}\n"
        basic_info += f"🕐 **時間**: {time_str}\n"
        basic_info += f"📍 **場所**: {event.location or '場所未設定'}\n"
        basic_info += f"👥 **参加者数**: {event.participants or '未定'}名\n"
        basic_info += f"📊 **ステータス**: {event.get_status_emoji()} {event.status or '未設定'}"
        
        # 登壇者情報
        if event.speakers:
            basic_info += f"\n🎤 **登壇者**: {event.speakers}"
        
        # セミナーURL
        if event.seminar_url:
            basic_info += f"\n🔗 **セミナーURL**: [録画・資料はこちら]({event.seminar_url})"
        
        embed.add_field(
            name="基本情報",
            value=basic_info,
            inline=False
        )
        
        # 詳細説明
        if event.description:
            embed.add_field(
                name="詳細",
                value=event.description,
                inline=False
            )
        
        # メタ情報
        if event.created_time or event.modified_time:
            meta_info = ""
            if event.created_time:
                meta_info += f"作成日時: {event.created_time.strftime('%Y-%m-%d %H:%M')}\n"
            if event.modified_time:
                meta_info += f"更新日時: {event.modified_time.strftime('%Y-%m-%d %H:%M')}"
            
            embed.add_field(
                name="メタ情報",
                value=meta_info,
                inline=True
            )
        
        # サムネイル画像を設定
        if event.thumbnail_url:
            embed.set_thumbnail(url=event.thumbnail_url)
        
        embed.set_footer(text="Lark Events Bot | アーカイブ")
        return embed

    @classmethod
    def create_error_embed(cls, error_message: str, title: str = "エラーが発生しました") -> discord.Embed:
        """エラー用Embedを作成"""
        embed = discord.Embed(
            title=f"❌ {title}",
            description=error_message,
            color=cls.COLORS['danger'],
            timestamp=datetime.now()
        )
        embed.set_footer(text="Lark Events Bot")
        return embed
    
    @classmethod
    def create_success_embed(cls, message: str, title: str = "成功") -> discord.Embed:
        """成功用Embedを作成"""
        embed = discord.Embed(
            title=f"✅ {title}",
            description=message,
            color=cls.COLORS['success'],
            timestamp=datetime.now()
        )
        embed.set_footer(text="Lark Events Bot")
        return embed
    
    @classmethod
    def create_info_embed(cls, message: str, title: str = "情報") -> discord.Embed:
        """情報用Embedを作成"""
        embed = discord.Embed(
            title=f"ℹ️ {title}",
            description=message,
            color=cls.COLORS['info'],
            timestamp=datetime.now()
        )
        embed.set_footer(text="Lark Events Bot")
        return embed
    
    @classmethod
    def create_archive_summary_embed(cls, archived_count: int, date: str) -> discord.Embed:
        """アーカイブ完了サマリー用Embedを作成"""
        if archived_count == 0:
            description = f"{date} のアーカイブ対象イベントはありませんでした。"
            color = cls.COLORS['info']
        else:
            description = f"{date} の **{archived_count}件** のイベントをアーカイブしました。"
            color = cls.COLORS['success']
        
        embed = discord.Embed(
            title="📁 アーカイブ完了",
            description=description,
            color=color,
            timestamp=datetime.now()
        )
        embed.set_footer(text="Lark Events Bot")
        return embed
    
    @classmethod
    def format_thread_name(cls, event: LarkEventRecord) -> str:
        """フォーラムスレッド名をフォーマット"""
        event_name = event.event_name or "イベント"
        date_str = event.get_formatted_date() if event.event_date else "日付未設定"
        
        # スレッド名の長さ制限（Discordの制限: 100文字）
        thread_name = f"{event_name} - {date_str}"
        if len(thread_name) > 97:
            # イベント名を短縮
            max_event_name_length = 97 - len(f" - {date_str}")
            event_name = event_name[:max_event_name_length-3] + "..."
            thread_name = f"{event_name} - {date_str}"
        
        return thread_name
    
    @classmethod
    def create_notification_summary(cls, events: List[LarkEventRecord]) -> str:
        """通知サマリーテキストを作成"""
        if not events:
            return "本日開催予定のイベントはありません。"
        
        summary = f"本日は {len(events)}件のイベントが開催予定です:\n"
        for i, event in enumerate(events, 1):
            event_name = event.event_name or "イベント名未設定"
            time_info = event.get_formatted_time()
            summary += f"{i}. {event_name} ({time_info})\n"
        
        return summary.strip()


# テスト用の関数
def test_formatters():
    """フォーマッターのテスト"""
    from datetime import datetime
    import pytz
    
    # テスト用のイベントデータ
    test_event = LarkEventRecord(
        record_id="test123",
        event_name="Python勉強会",
        event_date=datetime.now(pytz.timezone('Asia/Tokyo')),
        start_time="19:00",
        end_time="21:00",
        location="オンライン",
        description="Pythonの基礎について学ぶ勉強会です。初心者歓迎！",
        participants=25,
        status="開催予定"
    )
    
    # 今日のイベント用Embed
    today_embed = DiscordFormatter.create_today_events_embed([test_event])
    print("Today's events embed created")
    
    # アーカイブ用Embed
    archive_embed = DiscordFormatter.create_event_archive_embed(test_event)
    print("Archive embed created")
    
    # スレッド名
    thread_name = DiscordFormatter.format_thread_name(test_event)
    print(f"Thread name: {thread_name}")


if __name__ == "__main__":
    test_formatters()