#!/usr/bin/env python3
"""
Larkテーブルの日付フィールドの形式を分析するスクリプト
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
        print("🔍 日付フィールドの形式を分析中...")
        
        # 全レコードを取得
        records = get_all_records()
        print(f"📊 総レコード数: {len(records)}")
        
        # 日付フィールドのパターンを分析
        date_patterns = set()
        morrie_events = []
        
        for record in records:
            fields = record.get('fields', {})
            
            # 登壇者フィールドをチェック
            instructor = fields.get('登壇者', '')
            if 'モーリー' in str(instructor):
                # 全フィールドを確認
                event_data = {
                    'record_id': record.get('record_id'),
                    'fields': fields
                }
                morrie_events.append(event_data)
                
                # 日付関連フィールドを探す
                for field_name, field_value in fields.items():
                    if any(keyword in field_name for keyword in ['日', 'date', 'Date', 'イベント', '開催']):
                        date_patterns.add(f"{field_name}: {type(field_value)} = {str(field_value)[:100]}")
        
        print(f"\n📊 モーリーさんのイベント数: {len(morrie_events)}")
        print(f"📊 日付パターン数: {len(date_patterns)}")
        
        print("\n📅 日付関連フィールドのパターン:")
        for pattern in sorted(date_patterns):
            print(f"  {pattern}")
        
        # 最新のモーリーさんのイベントを詳細表示
        if morrie_events:
            print(f"\n🔍 最新のモーリーさんのイベント詳細 (最初の3件):")
            for i, event in enumerate(morrie_events[:3], 1):
                print(f"\n{i}. Record ID: {event['record_id']}")
                fields = event['fields']
                for field_name, field_value in fields.items():
                    if field_value:  # 空でないフィールドのみ表示
                        print(f"   {field_name}: {field_value}")
                print("-" * 50)
                
                # 詳細データを保存
                filename = f"morrie_event_detail_{i}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(event, f, ensure_ascii=False, indent=2)
        
        # 2025年を含むレコードを検索
        print(f"\n🔍 2025年を含むレコードを検索中...")
        records_with_2025 = []
        for record in records:
            record_str = json.dumps(record, ensure_ascii=False)
            if '2025' in record_str:
                records_with_2025.append(record)
        
        print(f"📊 2025年を含むレコード数: {len(records_with_2025)}")
        
        if records_with_2025:
            print("\n🎯 2025年を含むレコード (最初の5件):")
            for i, record in enumerate(records_with_2025[:5], 1):
                fields = record.get('fields', {})
                title = fields.get('イベントタイトル', 'タイトル不明')
                instructor = fields.get('登壇者', '講師不明')
                print(f"{i}. {title}")
                print(f"   講師: {instructor}")
                print(f"   Record ID: {record.get('record_id')}")
                
                # 2025年を含むフィールドを特定
                for field_name, field_value in fields.items():
                    if '2025' in str(field_value):
                        print(f"   🎯 {field_name}: {field_value}")
                print()
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()