"""
設定管理モジュール
環境変数から設定を読み込み、バリデーションを行う
"""

import os
from typing import Optional
from pydantic import field_validator, ConfigDict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()


class Settings(BaseSettings):
    """アプリケーション設定"""
    
    # Lark設定
    lark_app_id: str
    lark_app_secret: str
    lark_base_token: str
    lark_table_id: str
    
    # Discord設定
    discord_bot_token: str
    discord_guild_id: int
    discord_notification_channel_id: int
    discord_archive_forum_id: int
    
    # Webhook設定
    webhook_verification_token: Optional[str] = None
    webhook_encrypt_key: Optional[str] = None
    
    # スケジュール設定
    notification_schedule: str = "0 9 * * *"  # 毎日9時
    archive_schedule: str = "0 18 * * *"      # 毎日18時
    
    # ログ設定
    log_level: str = "INFO"
    
    # API設定
    api_timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 1
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    @field_validator('lark_app_id')
    @classmethod
    def validate_lark_app_id(cls, v):
        if not v or not v.startswith('cli_'):
            raise ValueError('Lark App ID must be provided and start with "cli_"')
        return v
    
    @field_validator('lark_app_secret')
    @classmethod
    def validate_lark_app_secret(cls, v):
        if not v or len(v) < 20:
            raise ValueError('Lark App Secret must be provided and valid')
        return v
    
    @field_validator('discord_bot_token')
    @classmethod
    def validate_discord_bot_token(cls, v):
        if not v or not v.startswith(('Bot ', 'MTk')):
            raise ValueError('Discord Bot Token must be provided and valid')
        return v
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()
    
    @field_validator('notification_schedule', 'archive_schedule')
    @classmethod
    def validate_cron_schedule(cls, v):
        # 簡単なcron形式の検証
        parts = v.split()
        if len(parts) != 5:
            raise ValueError('Schedule must be in cron format (5 parts)')
        return v


# グローバル設定インスタンス
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """設定インスタンスを取得"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """設定を再読み込み"""
    global _settings
    _settings = None
    return get_settings()


# 開発用の設定確認
if __name__ == "__main__":
    try:
        settings = get_settings()
        print("✅ 設定の読み込みが成功しました")
        print(f"Lark App ID: {settings.lark_app_id[:10]}...")
        print(f"Discord Guild ID: {settings.discord_guild_id}")
        print(f"Log Level: {settings.log_level}")
    except Exception as e:
        print(f"❌ 設定エラー: {e}")
        print("💡 .envファイルの設定を確認してください")