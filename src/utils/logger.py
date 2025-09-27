"""
ロガー設定ユーティリティ
アプリケーション全体のログ設定を管理
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
import colorlog
from typing import Optional

from ..config.settings import settings


class LoggerSetup:
    """ロガー設定クラス"""
    
    @staticmethod
    def setup_logging(
        log_level: str = None,
        log_file: Optional[str] = None,
        enable_console: bool = True,
        enable_file: bool = True,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ):
        """ログ設定を初期化"""
        
        # ログレベルの設定
        if log_level is None:
            log_level = settings.log_level
        
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        
        # ルートロガーの設定
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)
        
        # 既存のハンドラーをクリア
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # フォーマッターの設定
        formatters = LoggerSetup._create_formatters()
        
        # コンソールハンドラー
        if enable_console:
            console_handler = LoggerSetup._create_console_handler(
                formatters['console'], numeric_level
            )
            root_logger.addHandler(console_handler)
        
        # ファイルハンドラー
        if enable_file:
            if log_file is None:
                log_file = f"logs/bot_{datetime.now().strftime('%Y%m%d')}.log"
            
            file_handler = LoggerSetup._create_file_handler(
                log_file, formatters['file'], numeric_level,
                max_file_size, backup_count
            )
            root_logger.addHandler(file_handler)
        
        # 外部ライブラリのログレベル調整
        LoggerSetup._configure_external_loggers()
        
        logging.info(f"Logging initialized - Level: {log_level}")
    
    @staticmethod
    def _create_formatters() -> dict:
        """フォーマッターを作成"""
        
        # 基本フォーマット
        base_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        detailed_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(funcName)s() | %(message)s"
        
        # コンソール用（カラー付き）
        console_formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s | %(levelname)-8s%(reset)s | "
            "%(cyan)s%(name)s%(reset)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                'DEBUG': 'blue',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        
        # ファイル用
        file_formatter = logging.Formatter(
            detailed_format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        return {
            'console': console_formatter,
            'file': file_formatter
        }
    
    @staticmethod
    def _create_console_handler(formatter, level) -> logging.StreamHandler:
        """コンソールハンドラーを作成"""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        handler.setFormatter(formatter)
        return handler
    
    @staticmethod
    def _create_file_handler(
        log_file: str,
        formatter,
        level,
        max_size: int,
        backup_count: int
    ) -> logging.handlers.RotatingFileHandler:
        """ファイルハンドラーを作成"""
        
        # ログディレクトリを作成
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        handler.setLevel(level)
        handler.setFormatter(formatter)
        return handler
    
    @staticmethod
    def _configure_external_loggers():
        """外部ライブラリのログレベルを調整"""
        
        # Discord.pyのログレベル調整
        logging.getLogger('discord').setLevel(logging.WARNING)
        logging.getLogger('discord.http').setLevel(logging.WARNING)
        logging.getLogger('discord.gateway').setLevel(logging.WARNING)
        
        # aiohttp
        logging.getLogger('aiohttp').setLevel(logging.WARNING)
        logging.getLogger('aiohttp.access').setLevel(logging.WARNING)
        
        # APScheduler
        logging.getLogger('apscheduler').setLevel(logging.WARNING)
        logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)
        
        # urllib3
        logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """名前付きロガーを取得"""
        return logging.getLogger(name)


class ContextFilter(logging.Filter):
    """コンテキスト情報を追加するフィルター"""
    
    def __init__(self, context_data: dict = None):
        super().__init__()
        self.context_data = context_data or {}
    
    def filter(self, record):
        """レコードにコンテキスト情報を追加"""
        for key, value in self.context_data.items():
            setattr(record, key, value)
        return True


class PerformanceLogger:
    """パフォーマンス測定用ロガー"""
    
    def __init__(self, logger_name: str = "performance"):
        self.logger = logging.getLogger(logger_name)
    
    def log_execution_time(self, func_name: str, execution_time: float):
        """実行時間をログ"""
        if execution_time > 1.0:
            self.logger.warning(
                f"Slow execution: {func_name} took {execution_time:.2f}s"
            )
        else:
            self.logger.debug(
                f"Execution time: {func_name} took {execution_time:.3f}s"
            )
    
    def log_api_call(self, api_name: str, response_time: float, status_code: int = None):
        """API呼び出しをログ"""
        status_info = f" (status: {status_code})" if status_code else ""
        
        if response_time > 5.0:
            self.logger.warning(
                f"Slow API call: {api_name} took {response_time:.2f}s{status_info}"
            )
        else:
            self.logger.debug(
                f"API call: {api_name} took {response_time:.3f}s{status_info}"
            )
    
    def log_memory_usage(self, context: str, memory_mb: float):
        """メモリ使用量をログ"""
        if memory_mb > 100:
            self.logger.warning(
                f"High memory usage in {context}: {memory_mb:.1f}MB"
            )
        else:
            self.logger.debug(
                f"Memory usage in {context}: {memory_mb:.1f}MB"
            )


class ErrorLogger:
    """エラー専用ロガー"""
    
    def __init__(self, logger_name: str = "errors"):
        self.logger = logging.getLogger(logger_name)
    
    def log_api_error(self, api_name: str, error: Exception, context: dict = None):
        """API エラーをログ"""
        context_str = f" | Context: {context}" if context else ""
        self.logger.error(
            f"API Error in {api_name}: {type(error).__name__}: {str(error)}{context_str}",
            exc_info=True
        )
    
    def log_discord_error(self, command: str, error: Exception, user_id: int = None):
        """Discord エラーをログ"""
        user_info = f" | User: {user_id}" if user_id else ""
        self.logger.error(
            f"Discord Error in {command}: {type(error).__name__}: {str(error)}{user_info}",
            exc_info=True
        )
    
    def log_scheduler_error(self, job_id: str, error: Exception):
        """スケジューラー エラーをログ"""
        self.logger.error(
            f"Scheduler Error in job {job_id}: {type(error).__name__}: {str(error)}",
            exc_info=True
        )
    
    def log_unexpected_error(self, context: str, error: Exception, extra_data: dict = None):
        """予期しないエラーをログ"""
        extra_str = f" | Extra: {extra_data}" if extra_data else ""
        self.logger.critical(
            f"Unexpected Error in {context}: {type(error).__name__}: {str(error)}{extra_str}",
            exc_info=True
        )


# グローバルインスタンス
performance_logger = PerformanceLogger()
error_logger = ErrorLogger()


def setup_application_logging():
    """アプリケーション用ログ設定"""
    LoggerSetup.setup_logging()


def get_logger(name: str) -> logging.Logger:
    """ロガー取得のショートカット"""
    return LoggerSetup.get_logger(name)