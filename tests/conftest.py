"""
pytest 設定ファイル
テスト全体で使用される共通設定とフィクスチャ
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def event_loop():
    """セッション全体で使用するイベントループ"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def mock_environment():
    """テスト用環境変数のモック"""
    test_env = {
        # Lark設定
        'LARK_APP_ID': 'test_app_id',
        'LARK_APP_SECRET': 'test_app_secret',
        'LARK_BASE_TOKEN': 'test_base_token',
        'LARK_TABLE_ID': 'test_table_id',
        
        # Discord設定
        'DISCORD_BOT_TOKEN': 'test_bot_token',
        'DISCORD_GUILD_ID': '123456789012345678',
        'DISCORD_NOTIFICATION_CHANNEL_ID': '123456789012345679',
        'DISCORD_ARCHIVE_FORUM_ID': '123456789012345680',
        
        # スケジュール設定
        'DAILY_NOTIFICATION_CRON': '0 9 * * *',
        'ARCHIVE_CRON': '0 18 * * *',
        
        # その他設定
        'LOG_LEVEL': 'DEBUG',
        'TIMEZONE': 'Asia/Tokyo',
        'API_TIMEOUT': '30',
        'API_RETRY_COUNT': '3'
    }
    
    with patch.dict(os.environ, test_env, clear=False):
        yield test_env


@pytest.fixture
def mock_discord_bot():
    """Discord Bot のモック"""
    bot = MagicMock()
    bot.user = MagicMock()
    bot.user.id = 123456789012345681
    bot.user.name = "TestBot"
    bot.guilds = []
    bot.is_closed.return_value = False
    return bot


@pytest.fixture
def mock_discord_guild():
    """Discord Guild のモック"""
    guild = MagicMock()
    guild.id = 123456789012345678
    guild.name = "Test Guild"
    guild.channels = []
    return guild


@pytest.fixture
def mock_discord_channel():
    """Discord Channel のモック"""
    channel = MagicMock()
    channel.id = 123456789012345679
    channel.name = "test-channel"
    channel.send = MagicMock()
    return channel


@pytest.fixture
def mock_discord_forum():
    """Discord Forum のモック"""
    forum = MagicMock()
    forum.id = 123456789012345680
    forum.name = "test-forum"
    forum.create_thread = MagicMock()
    return forum


@pytest.fixture
def mock_lark_session():
    """Lark API セッションのモック"""
    session = MagicMock()
    session.closed = False
    session.close = MagicMock()
    return session


@pytest.fixture
def sample_lark_events():
    """サンプルLarkイベントデータ"""
    from src.lark.models import LarkEventRecord
    
    events = []
    for i in range(3):
        events.append(LarkEventRecord(
            record_id=f"rec{i+1}",
            event_name=f"テストイベント{i+1}",
            event_date="2024-01-15",
            start_time=f"{10+i}:00",
            end_time=f"{12+i}:00",
            participants=f"参加者{i+1}",
            location=f"会議室{chr(65+i)}",
            description=f"テストイベント{i+1}の説明",
            status="予定"
        ))
    return events


@pytest.fixture
def mock_scheduler():
    """スケジューラーのモック"""
    scheduler = MagicMock()
    scheduler.running = False
    scheduler.start = MagicMock()
    scheduler.shutdown = MagicMock()
    scheduler.add_job = MagicMock()
    scheduler.remove_job = MagicMock()
    scheduler.get_job = MagicMock(return_value=None)
    scheduler.get_jobs = MagicMock(return_value=[])
    return scheduler


@pytest.fixture
def mock_logger():
    """ロガーのモック"""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    logger.debug = MagicMock()
    logger.critical = MagicMock()
    return logger


@pytest.fixture
def temp_log_file(tmp_path):
    """一時ログファイル"""
    log_file = tmp_path / "test.log"
    return str(log_file)


@pytest.fixture
def mock_datetime():
    """日時のモック"""
    from datetime import datetime
    import pytz
    
    # 固定の日時を返すモック
    fixed_datetime = datetime(2024, 1, 15, 10, 0, 0, tzinfo=pytz.timezone('Asia/Tokyo'))
    
    with patch('src.utils.helpers.DateTimeHelper.now', return_value=fixed_datetime):
        yield fixed_datetime


class AsyncMock(MagicMock):
    """非同期関数用のモック"""
    
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


@pytest.fixture
def async_mock():
    """非同期モックのファクトリ"""
    return AsyncMock


# テスト用のマーカー定義
def pytest_configure(config):
    """pytest設定"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


# テスト実行前の共通処理
@pytest.fixture(autouse=True)
def setup_test_environment():
    """テスト環境のセットアップ"""
    # ログレベルを設定
    import logging
    logging.getLogger().setLevel(logging.CRITICAL)
    
    # テスト用ディレクトリの作成
    test_dirs = ['logs', 'data', 'temp']
    for dir_name in test_dirs:
        Path(dir_name).mkdir(exist_ok=True)
    
    yield
    
    # テスト後のクリーンアップ
    # 必要に応じてテンポラリファイルの削除など


# カスタムアサーション関数
def assert_valid_discord_embed(embed):
    """Discord埋め込みの妥当性をチェック"""
    import discord
    
    assert isinstance(embed, discord.Embed)
    assert embed.title is not None
    assert len(embed.title) <= 256
    
    if embed.description:
        assert len(embed.description) <= 4096
    
    assert len(embed.fields) <= 25
    
    for field in embed.fields:
        assert len(field.name) <= 256
        assert len(field.value) <= 1024


def assert_valid_lark_event(event):
    """Larkイベントの妥当性をチェック"""
    from src.lark.models import LarkEventRecord
    
    assert isinstance(event, LarkEventRecord)
    assert event.record_id is not None
    assert event.event_name is not None
    assert event.event_date is not None


# pytest プラグイン
pytest_plugins = []