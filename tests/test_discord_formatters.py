"""
Discord フォーマッターのテスト
"""

import pytest
from datetime import datetime
import pytz
import discord

from src.discord.formatters import DiscordFormatter
from src.lark.models import LarkEventRecord


class TestDiscordFormatter:
    """DiscordFormatter のテストクラス"""
    
    @pytest.fixture
    def sample_event(self):
        """サンプルイベントデータ"""
        return LarkEventRecord(
            record_id="rec123456",
            event_name="テストイベント",
            event_date="2024-01-15",
            start_time="10:00",
            end_time="12:00",
            participants="田中, 佐藤, 鈴木",
            location="会議室A",
            description="テストイベントの説明です。",
            status="予定"
        )
    
    @pytest.fixture
    def multiple_events(self):
        """複数のサンプルイベント"""
        events = []
        for i in range(3):
            events.append(LarkEventRecord(
                record_id=f"rec{i}",
                event_name=f"イベント{i+1}",
                event_date="2024-01-15",
                start_time=f"{10+i}:00",
                end_time=f"{12+i}:00",
                participants=f"参加者{i+1}",
                location=f"会議室{chr(65+i)}",
                description=f"イベント{i+1}の説明",
                status="予定"
            ))
        return events
    
    def test_create_today_events_embed_with_events(self, multiple_events):
        """今日のイベント埋め込み作成（イベントあり）のテスト"""
        embed = DiscordFormatter.create_today_events_embed(multiple_events)
        
        assert isinstance(embed, discord.Embed)
        assert "📅 本日のイベント" in embed.title
        assert embed.color.value == DiscordFormatter.COLORS['primary']
        assert len(embed.fields) == 3  # 3つのイベント
        
        # 最初のイベントの内容をチェック
        first_field = embed.fields[0]
        assert "📅 イベント1" in first_field.name
        assert "10:00" in first_field.value
        assert "会議室A" in first_field.value
    
    def test_create_today_events_embed_no_events(self):
        """今日のイベント埋め込み作成（イベントなし）のテスト"""
        embed = DiscordFormatter.create_today_events_embed([])
        
        assert isinstance(embed, discord.Embed)
        assert "📅 本日のイベント" in embed.title
        assert embed.color.value == DiscordFormatter.COLORS['info']
        assert "本日はイベントがありません" in embed.description
    
    def test_create_archive_embed(self, sample_event):
        """アーカイブ埋め込み作成のテスト"""
        embed = DiscordFormatter.create_archive_embed(sample_event)
        
        assert isinstance(embed, discord.Embed)
        assert sample_event.event_name in embed.title
        assert embed.color.value == DiscordFormatter.COLORS['archive']
        
        # フィールドの確認
        field_names = [field.name for field in embed.fields]
        assert "📅 開催日時" in field_names
        assert "👥 参加者" in field_names
        assert "📍 場所" in field_names
        assert "📝 説明" in field_names
        assert "📊 ステータス" in field_names
    
    def test_create_error_embed(self):
        """エラー埋め込み作成のテスト"""
        error_message = "テストエラーメッセージ"
        embed = DiscordFormatter.create_error_embed(error_message)
        
        assert isinstance(embed, discord.Embed)
        assert "❌ エラー" in embed.title
        assert embed.color.value == DiscordFormatter.COLORS['error']
        assert error_message in embed.description
    
    def test_create_success_embed(self):
        """成功埋め込み作成のテスト"""
        success_message = "テスト成功メッセージ"
        embed = DiscordFormatter.create_success_embed(success_message)
        
        assert isinstance(embed, discord.Embed)
        assert "✅ 成功" in embed.title
        assert embed.color.value == DiscordFormatter.COLORS['success']
        assert success_message in embed.description
    
    def test_create_info_embed(self):
        """情報埋め込み作成のテスト"""
        info_message = "テスト情報メッセージ"
        embed = DiscordFormatter.create_info_embed(info_message)
        
        assert isinstance(embed, discord.Embed)
        assert "ℹ️ 情報" in embed.title
        assert embed.color.value == DiscordFormatter.COLORS['info']
        assert info_message in embed.description
    
    def test_create_archive_summary_embed(self, multiple_events):
        """アーカイブサマリー埋め込み作成のテスト"""
        embed = DiscordFormatter.create_archive_summary_embed(multiple_events)
        
        assert isinstance(embed, discord.Embed)
        assert "📚 アーカイブサマリー" in embed.title
        assert embed.color.value == DiscordFormatter.COLORS['archive']
        assert "3件のイベント" in embed.description
        
        # イベントリストの確認
        for i, event in enumerate(multiple_events):
            field = embed.fields[i]
            assert event.event_name in field.name
            assert event.get_formatted_date() in field.value
    
    def test_format_thread_name(self, sample_event):
        """スレッド名フォーマットのテスト"""
        thread_name = DiscordFormatter.format_thread_name(sample_event)
        
        assert sample_event.event_name in thread_name
        assert "2024-01-15" in thread_name
        assert len(thread_name) <= 100  # Discordの制限
    
    def test_format_thread_name_long_title(self):
        """長いタイトルのスレッド名フォーマットのテスト"""
        long_event = LarkEventRecord(
            record_id="rec123",
            event_name="非常に長いイベント名" * 10,  # 意図的に長くする
            event_date="2024-01-15",
            start_time="10:00",
            end_time="12:00"
        )
        
        thread_name = DiscordFormatter.format_thread_name(long_event)
        
        assert len(thread_name) <= 100  # Discordの制限内
        assert "..." in thread_name  # 切り詰められている
        assert "2024-01-15" in thread_name  # 日付は含まれている
    
    def test_format_notification_summary(self, multiple_events):
        """通知サマリーフォーマットのテスト"""
        summary = DiscordFormatter.format_notification_summary(multiple_events)
        
        assert "本日は3件のイベントがあります" in summary
        
        for event in multiple_events:
            assert event.event_name in summary
            assert event.get_formatted_time() in summary
    
    def test_format_notification_summary_no_events(self):
        """通知サマリーフォーマット（イベントなし）のテスト"""
        summary = DiscordFormatter.format_notification_summary([])
        
        assert "本日はイベントがありません" in summary
    
    def test_format_notification_summary_many_events(self):
        """通知サマリーフォーマット（多数のイベント）のテスト"""
        # 10個以上のイベントを作成
        many_events = []
        for i in range(12):
            many_events.append(LarkEventRecord(
                record_id=f"rec{i}",
                event_name=f"イベント{i+1}",
                event_date="2024-01-15",
                start_time=f"{10}:00",
                end_time=f"{12}:00"
            ))
        
        summary = DiscordFormatter.format_notification_summary(many_events)
        
        assert "本日は12件のイベントがあります" in summary
        # 最初の10件のみ表示されることを確認
        assert "イベント1" in summary
        assert "イベント10" in summary
        assert "他に2件のイベント" in summary
    
    def test_embed_field_limits(self, sample_event):
        """埋め込みフィールド制限のテスト"""
        # 非常に長い説明を持つイベント
        long_description_event = LarkEventRecord(
            record_id="rec123",
            event_name="テストイベント",
            event_date="2024-01-15",
            start_time="10:00",
            end_time="12:00",
            description="非常に長い説明" * 100  # 意図的に長くする
        )
        
        embed = DiscordFormatter.create_archive_embed(long_description_event)
        
        # 説明フィールドを見つける
        description_field = None
        for field in embed.fields:
            if "📝 説明" in field.name:
                description_field = field
                break
        
        assert description_field is not None
        assert len(description_field.value) <= 1024  # Discordの制限
        assert "..." in description_field.value  # 切り詰められている
    
    def test_color_constants(self):
        """カラー定数のテスト"""
        colors = DiscordFormatter.COLORS
        
        # 必要なカラーが定義されていることを確認
        required_colors = ['primary', 'success', 'error', 'warning', 'info', 'archive']
        for color_name in required_colors:
            assert color_name in colors
            assert isinstance(colors[color_name], int)
            assert 0 <= colors[color_name] <= 0xFFFFFF  # 有効な色値
    
    def test_embed_timestamp(self, sample_event):
        """埋め込みタイムスタンプのテスト"""
        embed = DiscordFormatter.create_archive_embed(sample_event)
        
        assert embed.timestamp is not None
        assert isinstance(embed.timestamp, datetime)
        
        # タイムスタンプが現在時刻に近いことを確認（1分以内）
        now = datetime.now(pytz.UTC)
        time_diff = abs((now - embed.timestamp).total_seconds())
        assert time_diff < 60
    
    def test_embed_footer(self, sample_event):
        """埋め込みフッターのテスト"""
        embed = DiscordFormatter.create_archive_embed(sample_event)
        
        assert embed.footer is not None
        assert "Lark Events Bot" in embed.footer.text
    
    def test_special_characters_handling(self):
        """特殊文字処理のテスト"""
        special_event = LarkEventRecord(
            record_id="rec123",
            event_name="テスト🎉イベント",
            event_date="2024-01-15",
            start_time="10:00",
            end_time="12:00",
            description="特殊文字: @#$%^&*()_+{}|:<>?[]\\;'\",./"
        )
        
        embed = DiscordFormatter.create_archive_embed(special_event)
        
        # 特殊文字が適切に処理されることを確認
        assert "🎉" in embed.title
        
        # 説明フィールドを見つける
        description_field = None
        for field in embed.fields:
            if "📝 説明" in field.name:
                description_field = field
                break
        
        assert description_field is not None
        assert "@#$%^&*" in description_field.value  # 説明フィールド