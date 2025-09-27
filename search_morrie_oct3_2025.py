#!/usr/bin/env python3
"""
2025年10月3日のモーリーさんのセミナーを検索するスクリプト
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
        print("🔍 2025年10月3日のモーリーさんのセミナーを検索中...")
        
        # 全レコードを取得
        records = get_all_records()
        print(f"📊 総レコード数: {len(records)}")
        
        # モーリーさんのイベントを検索
        morrie_events = []
        for record in records:
            fields = record.get('fields', {})
            
            # 登壇者フィールドをチェック
            instructor = fields.get('登壇者', '')
            if not instructor:
                continue
                
            # モーリーが含まれているかチェック
            if 'モーリー' in str(instructor):
                # 日付フィールドをチェック
                event_date = fields.get('イベント', '')
                if event_date:
                    # 2025年10月3日を含むかチェック
                    if '2025' in str(event_date) and ('10/3' in str(event_date) or '10-3' in str(event_date) or '10月3日' in str(event_date)):
                        morrie_events.append({
                            'record_id': record.get('record_id'),
                            'fields': fields
                        })
                        print(f"✅ 見つかりました: {fields.get('イベントタイトル', 'タイトル不明')}")
                        print(f"   日付: {event_date}")
                        print(f"   講師: {instructor}")
        
        if not morrie_events:
            print("❌ 2025年10月3日のモーリーさんのセミナーが見つかりませんでした。")
            print("\n📋 モーリーさんの全イベントを確認してみます...")
            
            # モーリーさんの全イベントを表示
            all_morrie_events = []
            for record in records:
                fields = record.get('fields', {})
                instructor = fields.get('登壇者', '')
                if 'モーリー' in str(instructor):
                    all_morrie_events.append({
                        'record_id': record.get('record_id'),
                        'title': fields.get('イベントタイトル', 'タイトル不明'),
                        'date': fields.get('イベント', '日付不明'),
                        'instructor': instructor
                    })
            
            print(f"📊 モーリーさんの全イベント数: {len(all_morrie_events)}")
            for i, event in enumerate(all_morrie_events[:10], 1):  # 最初の10件を表示
                print(f"{i}. {event['title']}")
                print(f"   日付: {event['date']}")
                print(f"   講師: {event['instructor']}")
                print(f"   Record ID: {event['record_id']}")
                print()
            
            if len(all_morrie_events) > 10:
                print(f"... 他 {len(all_morrie_events) - 10} 件")
            
            return
        
        # 見つかったイベントを保存
        for i, event in enumerate(morrie_events):
            filename = f"morrie_oct3_2025_event_{i+1}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(event, f, ensure_ascii=False, indent=2)
            print(f"💾 イベントデータを保存しました: {filename}")
        
        print(f"\n🎉 {len(morrie_events)}件のイベントが見つかりました！")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()