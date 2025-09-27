#!/usr/bin/env python3
"""
Test webhook.py with actual future event data (October 3, 2025)
This test uses real future event data to verify that webhook.py correctly processes
the actual Lark datetime fields without needing date adjustments.
"""

import json
import sys
from datetime import datetime, timezone

def load_future_event_data():
    """Load the future event data from morrie_oct_2025_event_1.json"""
    try:
        with open('morrie_oct_2025_event_1.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: morrie_oct_2025_event_1.json not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        sys.exit(1)

def display_event_info(event_data):
    """Display the event information"""
    print("=== 未来のイベントデータ ===")
    print(f"タイトル: {event_data.get('title', 'N/A')}")
    
    # Extract instructor
    instructor_info = event_data.get('instructor', [])
    instructor = instructor_info[0].get('text', 'N/A') if instructor_info else 'N/A'
    print(f"講師: {instructor}")
    
    # Extract datetime fields
    fields = event_data.get('fields', {})
    start_timestamp = fields.get('イベント開始日時')
    end_timestamp = fields.get('イベント終了日時')
    
    if start_timestamp and end_timestamp:
        start_dt = datetime.fromtimestamp(start_timestamp / 1000, tz=timezone.utc)
        end_dt = datetime.fromtimestamp(end_timestamp / 1000, tz=timezone.utc)
        
        print(f"開始日時: {start_dt.strftime('%Y-%m-%d %H:%M:%S')} UTC ({start_dt.astimezone().strftime('%Y-%m-%d %H:%M:%S')} JST)")
        print(f"終了日時: {end_dt.strftime('%Y-%m-%d %H:%M:%S')} UTC ({end_dt.astimezone().strftime('%Y-%m-%d %H:%M:%S')} JST)")
        print(f"開始タイムスタンプ: {start_timestamp}")
        print(f"終了タイムスタンプ: {end_timestamp}")
    else:
        print("日時情報が見つかりません")
    
    print()

def create_webhook_payload(event_data):
    """Create webhook payload in the format expected by webhook.py"""
    
    # Extract basic info
    title = event_data.get('title', '')
    instructor_info = event_data.get('instructor', [])
    instructor = instructor_info[0].get('text', '') if instructor_info else ''
    
    # Extract fields
    fields = event_data.get('fields', {})
    
    # Create the webhook payload structure
    payload = {
        "schema": "2.0",
        "header": {
            "event_id": "test_future_event_001",
            "event_type": "app.open.record.updated",
            "create_time": "2024-09-27T12:00:00.000Z",
            "token": "test_token",
            "app_id": "test_app_id",
            "tenant_key": "test_tenant"
        },
        "event": {
            "object": {
                "record_id": event_data.get('record_id', 'test_record'),
                "fields": fields
            }
        }
    }
    
    return payload

def test_webhook():
    """Test the webhook with future event data"""
    print("=== 未来のイベントデータでのWebhookテスト ===")
    
    # Load future event data
    event_data = load_future_event_data()
    display_event_info(event_data)
    
    # Import and test webhook
    try:
        import sys
        import asyncio
        sys.path.append('api')
        from webhook import create_discord_event_and_announcement
        
        print("Discord イベント作成処理を開始...")
        
        # Create event data in the format expected by the function
        # The function expects event_data with 'fields' inside
        fields = event_data.get('fields', {}).copy()
        
        # Use the actual Peatix確認 field structure from the JSON data
        # No need to modify it since webhook.py should handle it correctly
        
        formatted_event_data = {
            "fields": fields
        }
        
        # Run the async function
        result = asyncio.run(create_discord_event_and_announcement(formatted_event_data))
        
        if result:
            print("✅ Discord イベント作成が成功しました！")
            print(f"結果: {result}")
        else:
            print("❌ Discord イベント作成が失敗しました")
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_webhook()