#!/usr/bin/env python3
"""
モーリーさんの2025年のイベントを詳細検索するスクリプト
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
        print("🔍 モーリーさんの2025年のイベントを詳細検索中...")
        
        # 全レコードを取得
        records = get_all_records()
        print(f"📊 総レコード数: {len(records)}")
        
        # モーリーさんのイベントを検索
        morrie_events_2025 = []
        all_morrie_events = []
        
        for record in records:
            fields = record.get('fields', {})
            
            # 登壇者フィールドをチェック
            instructor = fields.get('登壇者', '')
            if not instructor:
                continue
                
            # モーリーが含まれているかチェック
            if 'モーリー' in str(instructor):
                event_data = {
                    'record_id': record.get('record_id'),
                    'title': fields.get('イベントタイトル', 'タイトル不明'),
                    'date': fields.get('イベント', '日付不明'),
                    'instructor': instructor,
                    'fields': fields
                }
                all_morrie_events.append(event_data)
                
                # 2025年を含むかチェック
                event_date = str(fields.get('イベント', ''))
                if '2025' in event_date:
                    morrie_events_2025.append(event_data)
                    print(f"✅ 2025年のイベント発見: {event_data['title']}")
                    print(f"   日付: {event_date}")
                    print(f"   Record ID: {event_data['record_id']}")
                    
                    # 10月3日かチェック
                    if any(pattern in event_date for pattern in ['10/3', '10-3', '10月3日', '10月03日']):
                        print(f"🎯 10月3日のイベントです！")
        
        print(f"\n📊 モーリーさんの全イベント数: {len(all_morrie_events)}")
        print(f"📊 モーリーさんの2025年イベント数: {len(morrie_events_2025)}")
        
        if morrie_events_2025:
            print("\n🎉 2025年のモーリーさんのイベント一覧:")
            for i, event in enumerate(morrie_events_2025, 1):
                print(f"{i}. {event['title']}")
                print(f"   日付: {event['date']}")
                print(f"   Record ID: {event['record_id']}")
                print()
                
                # 詳細データを保存
                filename = f"morrie_2025_event_{i}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(event, f, ensure_ascii=False, indent=2)
                print(f"💾 保存: {filename}")
        else:
            print("\n❌ 2025年のモーリーさんのイベントが見つかりませんでした。")
            print("\n📋 最近のモーリーさんのイベント（最新10件）:")
            for i, event in enumerate(all_morrie_events[:10], 1):
                print(f"{i}. {event['title']}")
                print(f"   日付: {event['date']}")
                print(f"   Record ID: {event['record_id']}")
                print()
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()