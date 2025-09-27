"""
Lark API データモデル
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date, time
from pydantic import BaseModel, field_validator
import pytz


class LarkEventRecord(BaseModel):
    """Larkイベントレコード"""
    record_id: str
    event_name: Optional[str] = None
    event_title: Optional[str] = None
    event_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    description: Optional[str] = None
    speakers: Optional[str] = None
    seminar_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    status: Optional[str] = None
    
    # 追加フィールド
    event_start_datetime: Optional[datetime] = None
    event_end_datetime: Optional[datetime] = None
    
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

    @field_validator('seminar_url', mode='before')
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
        if not self.event_date:
            return None, None
        
        try:
            # 日付をパース
            event_date_obj = datetime.strptime(self.event_date, "%Y-%m-%d").date()
            
            # 開始時間をパース
            start_dt = None
            if self.start_time:
                try:
                    start_time_obj = datetime.strptime(self.start_time, "%H:%M").time()
                    start_dt = datetime.combine(event_date_obj, start_time_obj)
                    # 日本時間として設定
                    start_dt = pytz.timezone('Asia/Tokyo').localize(start_dt)
                except ValueError:
                    pass
            
            # 終了時間をパース
            end_dt = None
            if self.end_time:
                try:
                    end_time_obj = datetime.strptime(self.end_time, "%H:%M").time()
                    end_dt = datetime.combine(event_date_obj, end_time_obj)
                    # 日本時間として設定
                    end_dt = pytz.timezone('Asia/Tokyo').localize(end_dt)
                except ValueError:
                    pass
            
            return start_dt, end_dt
            
        except ValueError:
            return None, None


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
    'event_name': 'イベント名',
    'event_title': 'タイトル',
    'event_date': '開催日',
    'start_time': '開始時間',
    'end_time': '終了時間',
    'description': '説明',
    'speakers': '講師',
    'seminar_url': 'セミナーURL',
    'thumbnail_url': 'サムネイル',
    'status': 'ステータス'
}


def create_field_mapping(custom_mapping: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """フィールドマッピングを作成"""
    mapping = DEFAULT_FIELD_MAPPING.copy()
    if custom_mapping:
        mapping.update(custom_mapping)
    return mapping