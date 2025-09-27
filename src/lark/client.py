"""
Lark API クライアント
Lark (Feishu) APIとの通信を担当
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin

from ..config.settings import get_settings
from .models import LarkEventRecord, LarkTableResponse, LarkAuthResponse, create_field_mapping

logger = logging.getLogger(__name__)


class LarkAPIError(Exception):
    """Lark API エラー"""
    def __init__(self, message: str, code: Optional[int] = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class LarkClient:
    """Lark API クライアント"""
    
    BASE_URL = "https://open.larksuite.com/open-apis"
    
    def __init__(self):
        self.settings = get_settings()
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self.field_mapping = create_field_mapping()
    
    async def __aenter__(self):
        """非同期コンテキストマネージャー開始"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャー終了"""
        await self.close()
    
    async def _ensure_session(self):
        """HTTPセッションの確保"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.settings.api_timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
    
    async def close(self):
        """リソースのクリーンアップ"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def _get_access_token(self) -> str:
        """アクセストークンを取得"""
        # トークンが有効な場合はそのまま返す
        if (self._access_token and self._token_expires_at and 
            datetime.now() < self._token_expires_at - timedelta(minutes=5)):
            return self._access_token
        
        await self._ensure_session()
        
        url = urljoin(self.BASE_URL, "/auth/v3/app_access_token/internal")
        payload = {
            "app_id": self.settings.lark_app_id,
            "app_secret": self.settings.lark_app_secret
        }
        
        try:
            async with self._session.post(url, json=payload) as response:
                data = await response.json()
                auth_response = LarkAuthResponse(**data)
                
                if not auth_response.is_success():
                    raise LarkAPIError(f"Authentication failed: {auth_response.msg}", auth_response.code)
                
                self._access_token = auth_response.app_access_token
                # トークンの有効期限を設定（通常2時間）
                self._token_expires_at = datetime.now() + timedelta(seconds=auth_response.expire or 7200)
                
                logger.info("Successfully obtained Lark access token")
                return self._access_token
                
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise LarkAPIError(f"Network error during authentication: {str(e)}")
        except Exception as e:
            raise LarkAPIError(f"Unexpected error during authentication: {str(e)}")
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """API リクエストを実行"""
        await self._ensure_session()
        token = await self._get_access_token()
        
        url = urljoin(self.BASE_URL, endpoint)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        for attempt in range(self.settings.max_retries):
            try:
                async with self._session.request(method, url, headers=headers, **kwargs) as response:
                    data = await response.json()
                    
                    # レート制限の処理
                    if response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', 60))
                        logger.warning(f"Rate limited, waiting {retry_after} seconds")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    # エラーレスポンスの処理
                    if data.get('code', 0) != 0:
                        error_msg = data.get('msg', 'Unknown error')
                        raise LarkAPIError(f"API error: {error_msg}", data.get('code'))
                    
                    return data
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == self.settings.max_retries - 1:
                    raise LarkAPIError(f"Network error: {str(e)}")
                
                wait_time = self.settings.retry_delay * (2 ** attempt)
                logger.warning(f"Request failed, retrying in {wait_time} seconds: {str(e)}")
                await asyncio.sleep(wait_time)
        
        raise LarkAPIError("Max retries exceeded")
    
    async def get_table_records(self, 
                               page_size: int = 500,
                               page_token: Optional[str] = None,
                               filter_condition: Optional[str] = None,
                               sort_condition: Optional[List[Dict]] = None) -> LarkTableResponse:
        """テーブルレコードを取得"""
        endpoint = f"/bitable/v1/apps/{self.settings.lark_base_token}/tables/{self.settings.lark_table_id}/records"
        
        params = {
            "page_size": min(page_size, 500)  # 最大500件
        }
        
        if page_token:
            params["page_token"] = page_token
        
        if filter_condition:
            params["filter"] = filter_condition
        
        if sort_condition:
            params["sort"] = sort_condition
        
        data = await self._make_request("GET", endpoint, params=params)
        return LarkTableResponse(**data)
    
    async def get_all_records(self, 
                             filter_condition: Optional[str] = None,
                             sort_condition: Optional[List[Dict]] = None) -> List[LarkEventRecord]:
        """全てのレコードを取得（ページネーション対応）"""
        all_records = []
        page_token = None
        
        while True:
            response = await self.get_table_records(
                page_token=page_token,
                filter_condition=filter_condition,
                sort_condition=sort_condition
            )
            
            records = response.get_records(self.field_mapping)
            all_records.extend(records)
            
            # 次のページがあるかチェック
            if not response.data.get('has_more', False):
                break
            
            page_token = response.data.get('page_token')
            
            # レート制限対応のための待機
            await asyncio.sleep(0.6)  # 100 requests/minute = 0.6秒間隔
        
        logger.info(f"Retrieved {len(all_records)} records from Lark")
        return all_records
    
    async def get_today_events(self) -> List[LarkEventRecord]:
        """本日のイベントを取得"""
        # 今日の日付でフィルタリング
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Larkのフィルター条件（日付フィールドが今日の日付と一致）
        filter_condition = f'CurrentValue.[開催日] = "{today}"'
        
        try:
            records = await self.get_all_records(filter_condition=filter_condition)
            
            # 追加のフィルタリング（開催予定のイベントのみ）
            today_events = [
                record for record in records 
                if record.is_today() and record.status in ["開催予定", "開催中"]
            ]
            
            logger.info(f"Found {len(today_events)} events for today")
            return today_events
            
        except Exception as e:
            logger.error(f"Failed to get today's events: {str(e)}")
            raise
    
    async def get_past_events(self, days_back: int = 1) -> List[LarkEventRecord]:
        """過去のイベントを取得"""
        try:
            records = await self.get_all_records()
            
            # 過去のイベントをフィルタリング
            past_events = [
                record for record in records 
                if record.is_past() and record.status == "終了"
            ]
            
            # 指定日数以内のイベントのみ
            if days_back > 0:
                cutoff_date = datetime.now().date() - timedelta(days=days_back)
                filtered_events = []
                for event in past_events:
                    if event.event_date:
                        try:
                            # 文字列の日付をdateオブジェクトに変換
                            if isinstance(event.event_date, str):
                                event_date_obj = datetime.strptime(event.event_date, "%Y-%m-%d").date()
                            else:
                                event_date_obj = event.event_date.date() if hasattr(event.event_date, 'date') else event.event_date
                            
                            if event_date_obj >= cutoff_date:
                                filtered_events.append(event)
                        except (ValueError, AttributeError):
                            # 日付の解析に失敗した場合はスキップ
                            continue
                past_events = filtered_events
            
            logger.info(f"Found {len(past_events)} past events")
            return past_events
            
        except Exception as e:
            logger.error(f"Failed to get past events: {str(e)}")
            raise
    
    async def get_recently_ended_events(self, hours_back: int = 24) -> List[LarkEventRecord]:
        """最近終了したイベントを取得（アーカイブ対象）"""
        try:
            records = await self.get_all_records()
            
            # 現在時刻から指定時間前までの範囲
            now = datetime.now()
            cutoff_time = now - timedelta(hours=hours_back)
            
            recently_ended = []
            
            for record in records:
                # イベントが終了しているかチェック
                if not record.is_ended():
                    continue
                
                # 終了時間を取得
                end_time = None
                if record.event_end_datetime:
                    end_time = record.event_end_datetime
                elif record.event_start_datetime:
                    # 終了時間がない場合は開始時間から推定（24時間後）
                    end_time = record.event_start_datetime + timedelta(hours=24)
                elif record.event_date:
                    # 古い形式の場合は日付の終わりを使用
                    end_time = datetime.combine(record.event_date.date(), datetime.min.time()) + timedelta(days=1)
                
                # 指定時間内に終了したイベントのみ
                if end_time and cutoff_time <= end_time <= now:
                    recently_ended.append(record)
            
            logger.info(f"Found {len(recently_ended)} recently ended events (within {hours_back} hours)")
            return recently_ended
            
        except Exception as e:
            logger.error(f"Failed to get recently ended events: {str(e)}")
            raise
    
    async def get_all_events(self) -> List[LarkEventRecord]:
        """全てのイベントを取得"""
        try:
            all_records = await self.get_all_records()
            logger.info(f"Retrieved {len(all_records)} total events")
            return all_records
            
        except Exception as e:
            logger.error(f"Failed to get all events: {str(e)}")
            raise
    
    def set_field_mapping(self, custom_mapping: Dict[str, str]):
        """カスタムフィールドマッピングを設定"""
        self.field_mapping = create_field_mapping(custom_mapping)
        logger.info("Updated field mapping")


# 使用例とテスト用の関数
async def test_lark_client():
    """Lark クライアントのテスト"""
    async with LarkClient() as client:
        try:
            # 今日のイベントを取得
            today_events = await client.get_today_events()
            print(f"Today's events: {len(today_events)}")
            
            for event in today_events:
                print(f"- {event.event_name} at {event.get_formatted_time()}")
            
            # 過去のイベントを取得
            past_events = await client.get_past_events(days_back=7)
            print(f"Past events (last 7 days): {len(past_events)}")
            
        except LarkAPIError as e:
            print(f"Lark API Error: {e.message} (Code: {e.code})")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_lark_client())