#!/usr/bin/env python3
"""
2025年10月のモーリーさんのイベントを詳細検索するスクリプト
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

def get_lark_access_token():
    """Larkアクセストークンを取得"""
    app_id = os.getenv('LARK_APP_ID')
    app_secret = os.getenv('LARK_APP_SECRET')
    
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    data = {"app_id": app_id, "app_secret": app_secret}
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    if result.get('code') == 0:
        return result['tenant_access_token']
    else:
        raise Exception(f"Failed to get access token: {result}")

def get_all_records():
    """全レコードを取得"""
    access_token = get_lark_access_token()
    base_token = os.getenv('LARK_BASE_TOKEN')
    table_id = os.getenv('LARK_TABLE_ID')
    
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{base_token}/tables/{table_id}/records"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    all_records = []
    page_token = None
    
    while True:
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token
            
        response = requests.get(url, headers=headers, params=params)
        result = response.json()
        
        if result.get('code') != 0:
            raise Exception(f"Failed to get records: {result}")
            
        records = result['data']['items']
        all_records.extend(records)
        
        if not result['data'].get('has_more'):
            break
            
        page_token = result['data'].get('page_token')
    
    return all_records

def main():
    # 環境変数を読み込み
    load_dotenv()
    
    try:
        print("🔍 2025年10月のモーリーさんのイベントを検索中...")
        
        # 全レコードを取得
        records = get_all_records()
        print(f"📊 総レコード数: {len(records)}")
        
        # 2025年10月のモーリーさんのイベントを検索
        oct_2025_morrie_events = []
        all_2025_morrie_events = []
        
        for record in records:
            fields = record.get('fields', {})
            
            # 登壇者フィールドをチェック
            instructor = fields.get('登壇者', '')
            if not instructor or 'モーリー' not in str(instructor):
                continue
            
            # 2025年のイベントかチェック
            opening_month = fields.get('開催月', '')
            if '2025' in str(opening_month):
                event_data = {
                    'record_id': record.get('record_id'),
                    'title': fields.get('イベントタイトル', 'タイトル不明'),
                    'opening_month': opening_month,
                    'instructor': instructor,
                    'fields': fields
                }
                all_2025_morrie_events.append(event_data)
                
                # 10月かチェック
                if '2025-10' in str(opening_month):
                    oct_2025_morrie_events.append(event_data)
                    print(f"✅ 2025年10月のモーリーさんのイベント発見!")
                    print(f"   タイトル: {event_data['title']}")
                    print(f"   開催月: {opening_month}")
                    print(f"   Record ID: {event_data['record_id']}")
                    
                    # 詳細フィールドを確認
                    print(f"   詳細フィールド:")
                    for field_name, field_value in fields.items():
                        if field_value and any(keyword in field_name.lower() for keyword in ['日', 'date', 'time', '時間', '開始', '終了']):
                            print(f"     {field_name}: {field_value}")
                    print()
        
        print(f"\n📊 モーリーさんの2025年全イベント数: {len(all_2025_morrie_events)}")
        print(f"📊 モーリーさんの2025年10月イベント数: {len(oct_2025_morrie_events)}")
        
        if oct_2025_morrie_events:
            print(f"\n🎉 2025年10月のモーリーさんのイベント詳細:")
            for i, event in enumerate(oct_2025_morrie_events, 1):
                print(f"\n{i}. {event['title']}")
                print(f"   開催月: {event['opening_month']}")
                print(f"   Record ID: {event['record_id']}")
                
                # 全フィールドを表示
                print(f"   全フィールド:")
                for field_name, field_value in event['fields'].items():
                    if field_value:
                        print(f"     {field_name}: {field_value}")
                
                # データを保存
                filename = f"morrie_oct_2025_event_{i}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(event, f, ensure_ascii=False, indent=2)
                print(f"💾 保存: {filename}")
                print("-" * 80)
        else:
            print(f"\n❌ 2025年10月のモーリーさんのイベントが見つかりませんでした。")
            
            if all_2025_morrie_events:
                print(f"\n📋 モーリーさんの2025年の全イベント:")
                for i, event in enumerate(all_2025_morrie_events, 1):
                    print(f"{i}. {event['title']}")
                    print(f"   開催月: {event['opening_month']}")
                    print(f"   Record ID: {event['record_id']}")
                    print()
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()