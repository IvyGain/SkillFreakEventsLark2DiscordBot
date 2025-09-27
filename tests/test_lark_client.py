"""
Lark クライアントのテスト
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import pytz

from src.lark.client import LarkClient, LarkAPIError
from src.lark.models import LarkEventRecord, LarkTableResponse
from src.config.settings import get_settings


class TestLarkClient:
    """LarkClient のテストクラス"""
    
    @pytest.fixture
    def mock_settings(self):
        """モック設定"""
        with patch('src.lark.client.get_settings') as mock:
            # 実際のオブジェクトを作成してMagicMockの問題を回避
            from types import SimpleNamespace
            mock_settings_obj = SimpleNamespace()
            mock_settings_obj.lark_app_id = "test_app_id"
            mock_settings_obj.lark_app_secret = "test_app_secret"
            mock_settings_obj.lark_table_id = "test_table_id"
            mock_settings_obj.lark_base_token = "test_base_token"
            mock_settings_obj.api_timeout = 30
            mock_settings_obj.max_retries = 3
            mock_settings_obj.retry_delay = 1
            mock.return_value = mock_settings_obj
            yield mock_settings_obj
    
    @pytest.fixture
    def sample_event_data(self):
        """サンプルイベントデータ"""
        return {
            "record_id": "rec123456",
            "fields": {
                "イベント名": "テストイベント",
                "開催日": "2024-01-15",
                "開始時間": "10:00",
                "終了時間": "12:00",
                "参加者": "田中, 佐藤, 鈴木",
                "場所": "会議室A",
                "説明": "テストイベントの説明です。",
                "ステータス": "開催予定"
            }
        }
    
    @pytest.fixture
    def sample_table_response(self, sample_event_data):
        """サンプルテーブルレスポンス"""
        return {
            "code": 0,
            "msg": "success",
            "data": {
                "has_more": False,
                "page_token": "",
                "total": 1,
                "items": [sample_event_data]
            }
        }
    
    @pytest.fixture
    def sample_auth_response(self):
        """サンプル認証レスポンス"""
        return {
            "code": 0,
            "msg": "success",
            "app_access_token": "test_access_token",
            "expire": 7200
        }
    
    @pytest.mark.asyncio
    async def test_get_access_token_success(self, mock_settings, sample_auth_response):
        """アクセストークン取得成功のテスト"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.json.return_value = sample_auth_response
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response
            
            async with LarkClient() as client:
                token = await client._get_access_token()
                
                assert token == "test_access_token"
                assert client._access_token == "test_access_token"
                mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_access_token_failure(self, mock_settings):
        """アクセストークン取得失敗のテスト"""
        error_response = {
            "code": 99991663,
            "msg": "app not found"
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.json.return_value = error_response
            mock_response.status = 400
            mock_post.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(LarkAPIError) as exc_info:
                async with LarkClient() as client:
                    await client._get_access_token()
            
            assert "app not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_table_records_success(self, mock_settings, sample_table_response):
        """テーブルレコード取得成功のテスト"""
        with patch.object(LarkClient, '_get_access_token', return_value="test_token"), \
             patch('aiohttp.ClientSession.request') as mock_request:
            
            mock_response = AsyncMock()
            mock_response.json.return_value = sample_table_response
            mock_response.status = 200
            mock_request.return_value.__aenter__.return_value = mock_response
            
            async with LarkClient() as client:
                response = await client.get_table_records()
                
                assert isinstance(response, LarkTableResponse)
                records = response.get_records(client.field_mapping)
                assert len(records) == 1
                assert records[0].event_name == "テストイベント"
    
    @pytest.mark.asyncio
    async def test_get_today_events(self, mock_settings, sample_event_data):
        """今日のイベント取得のテスト"""
        # 今日の日付でイベントデータを作成
        today = datetime.now(pytz.timezone("Asia/Tokyo")).strftime("%Y-%m-%d")
        sample_event_data["fields"]["開催日"] = today
        
        table_response = {
            "code": 0,
            "msg": "success",
            "data": {
                "has_more": False,
                "page_token": "",
                "total": 1,
                "items": [sample_event_data]
            }
        }
        
        with patch.object(LarkClient, '_get_access_token', return_value="test_token"), \
             patch('aiohttp.ClientSession.request') as mock_request:
            
            mock_response = AsyncMock()
            mock_response.json.return_value = table_response
            mock_response.status = 200
            mock_request.return_value.__aenter__.return_value = mock_response
            
            async with LarkClient() as client:
                events = await client.get_today_events()
                
                assert len(events) == 1
                assert events[0].event_name == "テストイベント"
    
    @pytest.mark.asyncio
    async def test_get_past_events(self, mock_settings, sample_event_data):
        """過去のイベント取得のテスト"""
        # 昨日の日付でイベントデータを作成
        yesterday = (datetime.now(pytz.timezone("Asia/Tokyo")) - timedelta(days=1)).strftime("%Y-%m-%d")
        sample_event_data["fields"]["開催日"] = yesterday
        sample_event_data["fields"]["ステータス"] = "終了"
        
        table_response = {
            "code": 0,
            "msg": "success",
            "data": {
                "has_more": False,
                "page_token": "",
                "total": 1,
                "items": [sample_event_data]
            }
        }
        
        with patch.object(LarkClient, '_get_access_token', return_value="test_token"), \
             patch('aiohttp.ClientSession.request') as mock_request:
            
            mock_response = AsyncMock()
            mock_response.json.return_value = table_response
            mock_response.status = 200
            mock_request.return_value.__aenter__.return_value = mock_response
            
            async with LarkClient() as client:
                events = await client.get_past_events(days_back=7)
                
                assert len(events) == 1
                assert events[0].event_name == "テストイベント"
    
    @pytest.mark.asyncio
    async def test_pagination(self, mock_settings, sample_event_data):
        """ページネーションのテスト"""
        # 最初のページ
        first_page_response = {
            "code": 0,
            "msg": "success",
            "data": {
                "has_more": True,
                "page_token": "next_page_token",
                "total": 2,
                "items": [sample_event_data]
            }
        }
        
        # 2ページ目
        import copy
        second_event_data = copy.deepcopy(sample_event_data)
        second_event_data["record_id"] = "rec789012"
        second_event_data["fields"]["イベント名"] = "テストイベント2"
        
        second_page_response = {
            "code": 0,
            "msg": "success",
            "data": {
                "has_more": False,
                "page_token": "",
                "total": 2,
                "items": [second_event_data]
            }
        }
        
        with patch.object(LarkClient, '_get_access_token', return_value="test_token"), \
             patch('aiohttp.ClientSession.request') as mock_request:
            
            # 最初の呼び出しで1ページ目、2回目の呼び出しで2ページ目を返す
            mock_response_1 = AsyncMock()
            mock_response_1.json.return_value = first_page_response
            mock_response_1.status = 200
            
            mock_response_2 = AsyncMock()
            mock_response_2.json.return_value = second_page_response
            mock_response_2.status = 200
            
            mock_request.return_value.__aenter__.side_effect = [mock_response_1, mock_response_2]
            
            async with LarkClient() as client:
                all_records = await client.get_all_records()
                

                assert len(all_records) == 2
                assert all_records[0].event_name == "テストイベント"
                assert all_records[1].event_name == "テストイベント2"
                assert mock_request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, mock_settings):
        """APIエラーハンドリングのテスト"""
        error_response = {
            "code": 1254005,
            "msg": "invalid table id"
        }
        
        with patch.object(LarkClient, '_get_access_token', return_value="test_token"), \
             patch('aiohttp.ClientSession.request') as mock_request:
            
            mock_response = AsyncMock()
            mock_response.json.return_value = error_response
            mock_response.status = 400
            mock_request.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(LarkAPIError) as exc_info:
                async with LarkClient() as client:
                    await client.get_table_records()
            
            assert "invalid table id" in str(exc_info.value)
            assert exc_info.value.code == 1254005
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self, mock_settings):
        """ネットワークエラーハンドリングのテスト"""
        with patch.object(LarkClient, '_get_access_token', return_value="test_token"), \
             patch('aiohttp.ClientSession.request') as mock_request:
            
            mock_request.side_effect = asyncio.TimeoutError("Request timeout")
            
            with pytest.raises(LarkAPIError) as exc_info:
                async with LarkClient() as client:
                    await client.get_table_records()
            
            assert "Request timeout" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_context_manager(self, mock_settings):
        """コンテキストマネージャーのテスト"""
        async with LarkClient() as client:
            assert client._session is not None
            assert not client._session.closed
        
        # コンテキストを出た後はセッションが閉じられている
        assert client._session.closed
    
    def test_custom_field_mapping(self, mock_settings):
        """カスタムフィールドマッピングのテスト"""
        custom_mapping = {
            "event_name": "カスタムイベント名",
            "event_date": "カスタム開催日",
            "start_time": "カスタム開始時間"
        }
        
        client = LarkClient()
        client.set_field_mapping(custom_mapping)
        
        assert client.field_mapping["event_name"] == "カスタムイベント名"
        assert client.field_mapping["event_date"] == "カスタム開催日"
        assert client.field_mapping["start_time"] == "カスタム開始時間"