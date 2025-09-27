"""
Lark API データモデル
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date, time
from pydantic import BaseModel, field_validator
import pytz


class LarkEventRecord(BaseModel):
    """Larkイベントレコード"""
    record_id: str
    event_name: Optional[str] = None
    event_title: Optional[str] = None
    event_date: Optional[Union[str, int, float]] = None  # UNIXタイムスタンプまたは文字列
    start_time: Optional[Union[str, int, float]] = None  # UNIXタイムスタンプまたは文字列
    end_time: Optional[Union[str, int, float]] = None    # UNIXタイムスタンプまたは文字列
    description: Optional[str] = None
    speakers: Optional[str] = None
    seminar_url: Optional[str] = None    # YouTube Liveのリンク
    peatix_url: Optional[str] = None     # イベント申し込み用ページ
    thumbnail_url: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None
    participants: Optional[str] = None
    created_time: Optional[str] = None
    modified_time: Optional[str] = None
    
    # 追加フィールド
    event_start_datetime: Optional[datetime] = None
    event_end_datetime: Optional[datetime] = None
    
    def model_post_init(self, __context) -> None:
        """モデル初期化後の処理"""
        # datetime フィールドを自動設定
        start_dt, end_dt = self.get_datetime_range()
        if start_dt:
            self.event_start_datetime = start_dt
        if end_dt:
            self.event_end_datetime = end_dt
    
    @field_validator('thumbnail_url', mode='before')
    @classmethod
    def parse_thumbnail_url(cls, v):
        """サムネイル画像URLをパース"""
        if v is None:
            return None
        
        # リスト形式の場合（Larkの標準形式）
        if isinstance(v, list) and len(v) > 0:
            thumbnail_item = v[0]
            if isinstance(thumbnail_item, dict):
                # 'url'フィールドを優先的に使用
                if 'url' in thumbnail_item:
                    return thumbnail_item['url']
                # 'tmp_url'をフォールバック
                elif 'tmp_url' in thumbnail_item:
                    return thumbnail_item['tmp_url']
                # 'link'フィールドもチェック
                elif 'link' in thumbnail_item:
                    return thumbnail_item['link']
        
        # 辞書形式の場合
        elif isinstance(v, dict):
            if 'url' in v:
                return v['url']
            elif 'tmp_url' in v:
                return v['tmp_url']
            elif 'link' in v:
                return v['link']
        
        # 文字列の場合（直接URL）
        elif isinstance(v, str):
            return v if v.strip() else None
        
        return None

    @field_validator('event_name', 'event_title', 'speakers', 'status', mode='before')
    @classmethod
    def parse_text_fields(cls, v):
        """テキストフィールドをパース（Larkの複雑な形式に対応）"""
        if v is None:
            return None
        
        # リスト形式の場合（Larkの標準形式）
        if isinstance(v, list) and len(v) > 0:
            item = v[0]
            if isinstance(item, dict):
                # 'text'フィールドを使用
                if 'text' in item:
                    return item['text']
                # 'name'フィールドもチェック
                elif 'name' in item:
                    return item['name']
        
        # 辞書形式の場合
        elif isinstance(v, dict):
            if 'text' in v:
                return v['text']
            elif 'name' in v:
                return v['name']
        
        # 文字列の場合（直接テキスト）
        elif isinstance(v, str):
            return v if v.strip() else None
        
        return None

    @field_validator('seminar_url', 'peatix_url', mode='before')
    @classmethod
    def parse_url_fields(cls, v):
        """URLフィールドをパース（Larkの複雑な形式に対応）"""
        if v is None:
            return None
        
        # リスト形式の場合（Larkの標準形式）
        if isinstance(v, list) and len(v) > 0:
            item = v[0]
            if isinstance(item, dict):
                # 'link'フィールドを使用
                if 'link' in item:
                    return item['link']
                # 'url'フィールドもチェック
                elif 'url' in item:
                    return item['url']
        
        # 辞書形式の場合
        elif isinstance(v, dict):
            if 'link' in v:
                return v['link']
            elif 'url' in v:
                return v['url']
        
        # 文字列の場合（直接URL）
        elif isinstance(v, str):
            return v if v.strip() else None
        
        return None

    @field_validator('event_date', 'start_time', 'end_time', mode='before')
    @classmethod
    def parse_datetime_fields(cls, v):
        """日時フィールドをパース"""
        if v is None:
            return None
        
        # UNIXタイムスタンプ（ミリ秒）の場合はそのまま返す
        if isinstance(v, (int, float)):
            return v
        
        # 文字列の場合もそのまま返す（従来の形式との互換性）
        if isinstance(v, str):
            return v
        
        return None
    
    def is_today(self) -> bool:
        """今日のイベントかどうかを判定"""
        if not self.event_date:
            return False
        
        try:
            # 日付文字列をパース
            event_date_obj = datetime.strptime(self.event_date, "%Y-%m-%d").date()
            today = datetime.now(pytz.timezone('Asia/Tokyo')).date()
            return event_date_obj == today
        except ValueError:
            return False
    
    def is_past(self) -> bool:
        """過去のイベントかどうかを判定"""
        if not self.event_date:
            return False
        
        try:
            # 日付文字列をパース
            event_date_obj = datetime.strptime(self.event_date, "%Y-%m-%d").date()
            today = datetime.now(pytz.timezone('Asia/Tokyo')).date()
            return event_date_obj < today
        except ValueError:
            return False
    
    def get_title(self) -> str:
        """イベントタイトルを取得（event_nameまたはevent_titleから）"""
        return self.event_name or self.event_title or "タイトル未設定"
    
    def get_datetime_range(self) -> tuple[Optional[datetime], Optional[datetime]]:
        """イベントの開始・終了日時を取得"""
        start_dt = None
        end_dt = None
        
        # 開始日時の処理（UNIXタイムスタンプまたは文字列）
        if self.event_date:
            try:
                if isinstance(self.event_date, (int, float)):
                    # UNIXタイムスタンプ（ミリ秒）の場合
                    start_dt = datetime.fromtimestamp(self.event_date / 1000, tz=pytz.timezone('Asia/Tokyo'))
                elif isinstance(self.event_date, str):
                    # 文字列の場合（従来の形式との互換性）
                    if self.start_time:
                        event_date_obj = datetime.strptime(self.event_date, "%Y-%m-%d").date()
                        start_time_obj = datetime.strptime(self.start_time, "%H:%M").time()
                        start_dt = datetime.combine(event_date_obj, start_time_obj)
                        start_dt = pytz.timezone('Asia/Tokyo').localize(start_dt)
            except (ValueError, TypeError):
                pass
        
        # 終了日時の処理（UNIXタイムスタンプまたは文字列）
        if self.end_time:
            try:
                if isinstance(self.end_time, (int, float)):
                    # UNIXタイムスタンプ（ミリ秒）の場合
                    end_dt = datetime.fromtimestamp(self.end_time / 1000, tz=pytz.timezone('Asia/Tokyo'))
                elif isinstance(self.end_time, str) and start_dt:
                    # 文字列の場合（従来の形式との互換性）
                    end_time_obj = datetime.strptime(self.end_time, "%H:%M").time()
                    end_dt = datetime.combine(start_dt.date(), end_time_obj)
                    end_dt = pytz.timezone('Asia/Tokyo').localize(end_dt)
            except (ValueError, TypeError):
                pass
        
        return start_dt, end_dt
    
    def get_formatted_date(self) -> str:
        """フォーマットされた日付文字列を取得"""
        if not self.event_date:
            return "日付未設定"
        
        try:
            # 日付文字列をパース
            event_date_obj = datetime.strptime(self.event_date, "%Y-%m-%d").date()
            # 日本語形式でフォーマット
            return event_date_obj.strftime("%Y年%m月%d日")
        except ValueError:
            return self.event_date  # パースできない場合は元の文字列を返す
    
    def get_iso_date_string(self) -> str:
        """ISO形式の日付文字列を取得（YYYY-MM-DD）"""
        if not self.event_date:
            return "日付未設定"
        
        try:
            # 日付文字列をパース
            event_date_obj = datetime.strptime(self.event_date, "%Y-%m-%d").date()
            # ISO形式でフォーマット
            return event_date_obj.strftime("%Y-%m-%d")
        except ValueError:
            return self.event_date  # パースできない場合は元の文字列を返す
    
    def get_formatted_time(self) -> str:
        """フォーマットされた時間文字列を取得"""
        if self.start_time and self.end_time:
            return f"{self.start_time} - {self.end_time}"
        elif self.start_time:
            return f"{self.start_time} -"
        elif self.end_time:
            return f"- {self.end_time}"
        else:
            return "時間未設定"
    
    def get_status_emoji(self) -> str:
        """ステータスに応じた絵文字を返す"""
        status_emoji_map = {
            '開催予定': '🔵',
            '開催中': '🟡',
            '終了': '🟢',
            '中止': '🔴',
            '延期': '⚪'
        }
        return status_emoji_map.get(self.status, '⚫')


class LarkTableResponse(BaseModel):
    """Larkテーブルレスポンス"""
    code: int
    msg: str
    data: Dict[str, Any]
    
    def get_records(self, field_mapping: Dict[str, str]) -> List[LarkEventRecord]:
        """レコードリストを取得"""
        records = []
        
        if self.data and 'items' in self.data:
            for item in self.data['items']:
                record_data = {'record_id': item.get('record_id', '')}
                
                # フィールドマッピングに基づいてデータを抽出
                if 'fields' in item:
                    for field_name, lark_field_name in field_mapping.items():
                        if lark_field_name in item['fields']:
                            record_data[field_name] = item['fields'][lark_field_name]
                
                try:
                    record = LarkEventRecord(**record_data)
                    # 日時情報を設定
                    start_dt, end_dt = record.get_datetime_range()
                    record.event_start_datetime = start_dt
                    record.event_end_datetime = end_dt
                    records.append(record)
                except Exception as e:
                    print(f"Warning: Failed to create record from {record_data}: {e}")
                    continue
        
        return records


class LarkAuthResponse(BaseModel):
    """Lark認証レスポンス"""
    code: int
    msg: str
    app_access_token: Optional[str] = None
    expire: Optional[int] = None
    
    def is_success(self) -> bool:
        """認証成功かどうか判定"""
        return self.code == 0 and self.app_access_token is not None


# フィールドマッピング設定
DEFAULT_FIELD_MAPPING = {
    'event_name': 'イベント',
    'event_title': 'イベントタイトル',
    'event_date': 'イベント開始日時',  # UNIXタイムスタンプ（ミリ秒）
    'start_time': 'イベント開始日時',  # 同じフィールドを参照（互換性のため）
    'end_time': 'イベント終了日時',    # UNIXタイムスタンプ（ミリ秒）
    'description': 'イベント概要',
    'speakers': '登壇者',
    'seminar_url': 'セミナーURL',      # YouTube Liveのリンク
    'peatix_url': '本番Peatixページ',  # イベント申し込み用ページ
    'thumbnail_url': 'サムネイル',
    'status': '進捗',
    'location': '場所',  # 実際のフィールドが存在しない場合はNoneになる
    'participants': '参加者',  # 実際のフィールドが存在しない場合はNoneになる
    'created_time': '作成日時',  # 実際のフィールドが存在しない場合はNoneになる
    'modified_time': '更新日時'  # 実際のフィールドが存在しない場合はNoneになる
}


def create_field_mapping(custom_mapping: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """フィールドマッピングを作成"""
    mapping = DEFAULT_FIELD_MAPPING.copy()
    if custom_mapping:
        mapping.update(custom_mapping)
    return mapping