"""
ヘルパー関数とユーティリティ
共通で使用される便利な関数群
"""

import asyncio
import functools
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional, Union, List, Dict
import pytz
import re
import hashlib
import json
from pathlib import Path

from ..config.settings import settings
from .logger import performance_logger


def timing_decorator(func: Callable) -> Callable:
    """実行時間を測定するデコレータ"""
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            performance_logger.log_execution_time(func.__name__, execution_time)
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            performance_logger.log_execution_time(f"{func.__name__} (failed)", execution_time)
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            performance_logger.log_execution_time(func.__name__, execution_time)
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            performance_logger.log_execution_time(f"{func.__name__} (failed)", execution_time)
            raise
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


def retry_decorator(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """リトライ機能付きデコレータ"""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise last_exception
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


class DateTimeHelper:
    """日時関連のヘルパー関数"""
    
    @staticmethod
    def get_timezone() -> pytz.BaseTzInfo:
        """設定されたタイムゾーンを取得"""
        return pytz.timezone(settings.timezone)
    
    @staticmethod
    def now() -> datetime:
        """現在時刻を設定されたタイムゾーンで取得"""
        return datetime.now(DateTimeHelper.get_timezone())
    
    @staticmethod
    def today() -> datetime:
        """今日の日付（00:00:00）を取得"""
        now = DateTimeHelper.now()
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    @staticmethod
    def tomorrow() -> datetime:
        """明日の日付（00:00:00）を取得"""
        return DateTimeHelper.today() + timedelta(days=1)
    
    @staticmethod
    def yesterday() -> datetime:
        """昨日の日付（00:00:00）を取得"""
        return DateTimeHelper.today() - timedelta(days=1)
    
    @staticmethod
    def parse_date_string(date_str: str) -> Optional[datetime]:
        """日付文字列をパース"""
        if not date_str:
            return None
        
        # 一般的な日付フォーマットを試行
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%fZ"
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                # タイムゾーン情報がない場合は設定されたタイムゾーンを適用
                if dt.tzinfo is None:
                    dt = DateTimeHelper.get_timezone().localize(dt)
                return dt
            except ValueError:
                continue
        
        return None
    
    @staticmethod
    def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """日時をフォーマット"""
        if dt.tzinfo is None:
            dt = DateTimeHelper.get_timezone().localize(dt)
        elif dt.tzinfo != DateTimeHelper.get_timezone():
            dt = dt.astimezone(DateTimeHelper.get_timezone())
        
        return dt.strftime(format_str)
    
    @staticmethod
    def get_date_range(days_back: int = 0, days_forward: int = 0) -> tuple[datetime, datetime]:
        """日付範囲を取得"""
        today = DateTimeHelper.today()
        start_date = today - timedelta(days=days_back)
        end_date = today + timedelta(days=days_forward + 1)  # 翌日の00:00まで
        return start_date, end_date
    
    @staticmethod
    def is_today(dt: datetime) -> bool:
        """指定された日時が今日かどうか判定"""
        today = DateTimeHelper.today()
        tomorrow = DateTimeHelper.tomorrow()
        
        if dt.tzinfo is None:
            dt = DateTimeHelper.get_timezone().localize(dt)
        elif dt.tzinfo != DateTimeHelper.get_timezone():
            dt = dt.astimezone(DateTimeHelper.get_timezone())
        
        return today <= dt < tomorrow
    
    @staticmethod
    def days_until(target_date: datetime) -> int:
        """指定日までの日数を計算"""
        today = DateTimeHelper.today()
        
        if target_date.tzinfo is None:
            target_date = DateTimeHelper.get_timezone().localize(target_date)
        elif target_date.tzinfo != DateTimeHelper.get_timezone():
            target_date = target_date.astimezone(DateTimeHelper.get_timezone())
        
        target_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        return (target_day - today).days


class TextHelper:
    """テキスト処理のヘルパー関数"""
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """テキストを指定長で切り詰め"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def clean_text(text: str) -> str:
        """テキストをクリーンアップ"""
        if not text:
            return ""
        
        # 改行を正規化
        text = re.sub(r'\r\n|\r|\n', '\n', text)
        
        # 連続する空白を単一スペースに
        text = re.sub(r'[ \t]+', ' ', text)
        
        # 連続する改行を最大2つまでに
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    @staticmethod
    def extract_mentions(text: str) -> List[str]:
        """テキストからメンションを抽出"""
        # Discord形式のメンション <@123456789>
        discord_mentions = re.findall(r'<@!?(\d+)>', text)
        
        # @username形式のメンション
        username_mentions = re.findall(r'@(\w+)', text)
        
        return discord_mentions + username_mentions
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """ファイル名として安全な文字列に変換"""
        # 危険な文字を除去
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # 連続するアンダースコアを単一に
        filename = re.sub(r'_{2,}', '_', filename)
        
        # 先頭末尾のアンダースコアを除去
        filename = filename.strip('_')
        
        return filename or "unnamed"
    
    @staticmethod
    def generate_hash(text: str, length: int = 8) -> str:
        """テキストのハッシュ値を生成"""
        return hashlib.md5(text.encode()).hexdigest()[:length]


class DataHelper:
    """データ処理のヘルパー関数"""
    
    @staticmethod
    def safe_get(data: dict, key: str, default: Any = None) -> Any:
        """安全に辞書から値を取得"""
        try:
            keys = key.split('.')
            value = data
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    return default
            return value if value is not None else default
        except (KeyError, TypeError, AttributeError):
            return default
    
    @staticmethod
    def flatten_dict(data: dict, separator: str = '.') -> dict:
        """ネストした辞書を平坦化"""
        def _flatten(obj, parent_key=''):
            items = []
            if isinstance(obj, dict):
                for k, v in obj.items():
                    new_key = f"{parent_key}{separator}{k}" if parent_key else k
                    items.extend(_flatten(v, new_key).items())
            else:
                return {parent_key: obj}
            return dict(items)
        
        return _flatten(data)
    
    @staticmethod
    def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
        """リストを指定サイズのチャンクに分割"""
        return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
    
    @staticmethod
    def remove_duplicates(lst: List[Any], key: Callable = None) -> List[Any]:
        """リストから重複を除去"""
        if key is None:
            return list(dict.fromkeys(lst))
        
        seen = set()
        result = []
        for item in lst:
            k = key(item)
            if k not in seen:
                seen.add(k)
                result.append(item)
        return result


class FileHelper:
    """ファイル操作のヘルパー関数"""
    
    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> Path:
        """ディレクトリが存在することを確認（なければ作成）"""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def read_json_file(file_path: Union[str, Path]) -> Optional[dict]:
        """JSONファイルを読み込み"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
            return None
    
    @staticmethod
    def write_json_file(file_path: Union[str, Path], data: dict) -> bool:
        """JSONファイルに書き込み"""
        try:
            FileHelper.ensure_directory(Path(file_path).parent)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_file_size(file_path: Union[str, Path]) -> int:
        """ファイルサイズを取得（バイト）"""
        try:
            return Path(file_path).stat().st_size
        except FileNotFoundError:
            return 0
    
    @staticmethod
    def is_file_older_than(file_path: Union[str, Path], hours: int) -> bool:
        """ファイルが指定時間より古いかチェック"""
        try:
            file_time = datetime.fromtimestamp(Path(file_path).stat().st_mtime)
            return datetime.now() - file_time > timedelta(hours=hours)
        except FileNotFoundError:
            return True


class ValidationHelper:
    """バリデーション関連のヘルパー関数"""
    
    @staticmethod
    def is_valid_discord_id(discord_id: Union[str, int]) -> bool:
        """Discord IDの形式をチェック"""
        try:
            id_int = int(discord_id)
            return 17 <= len(str(id_int)) <= 19
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """URLの形式をチェック"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None
    
    @staticmethod
    def is_valid_cron(cron_expression: str) -> bool:
        """Cron式の形式をチェック"""
        parts = cron_expression.split()
        if len(parts) != 5:
            return False
        
        # 簡単な形式チェック（完全ではない）
        for part in parts:
            if not re.match(r'^[\d\*\-\,\/]+$', part):
                return False
        
        return True


# 便利な関数のエイリアス
now = DateTimeHelper.now
today = DateTimeHelper.today
safe_get = DataHelper.safe_get
truncate = TextHelper.truncate_text
clean_text = TextHelper.clean_text