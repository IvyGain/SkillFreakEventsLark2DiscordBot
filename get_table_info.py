#!/usr/bin/env python3
"""
Lark Table ID 取得ヘルパースクリプト

このスクリプトは、LarkのBase内にあるテーブルの一覧とTable IDを取得します。
初心者の方でも簡単にTable IDを見つけることができます。
"""

import requests
import json
import sys
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

def get_access_token(app_id: str, app_secret: str) -> Optional[str]:
    """
    Lark APIのアクセストークンを取得
    """
    url = "https://open.larksuite.com/open-apis/auth/v3/app_access_token/internal"
    
    payload = {
        "app_id": app_id,
        "app_secret": app_secret
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if data.get("code") == 0:
            return data.get("app_access_token")
        else:
            print(f"❌ アクセストークン取得エラー: {data.get('msg', 'Unknown error')}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ネットワークエラー: {e}")
        return None

def get_tables_info(base_token: str, access_token: str) -> Optional[List[Dict]]:
    """
    指定されたBase内のテーブル一覧を取得
    """
    url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{base_token}/tables"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if data.get("code") == 0:
            return data.get("data", {}).get("items", [])
        else:
            print(f"❌ テーブル情報取得エラー: {data.get('msg', 'Unknown error')}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ネットワークエラー: {e}")
        return None

def get_table_fields(base_token: str, table_id: str, access_token: str) -> Optional[List[Dict]]:
    """
    指定されたテーブルのフィールド情報を取得
    """
    url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{base_token}/tables/{table_id}/fields"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if data.get("code") == 0:
            return data.get("data", {}).get("items", [])
        else:
            print(f"❌ フィールド情報取得エラー: {data.get('msg', 'Unknown error')}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ネットワークエラー: {e}")
        return None

def main():
    """
    メイン処理
    """
    print("🔍 Lark Table ID 取得ツール")
    print("=" * 50)
    
    # .envファイルを読み込み
    load_dotenv()
    
    # 環境変数から設定値を取得
    app_id = os.getenv("LARK_APP_ID")
    app_secret = os.getenv("LARK_APP_SECRET")
    base_token = os.getenv("LARK_BASE_TOKEN")
    
    if not app_id or not app_secret or not base_token:
        print("❌ .envファイルに以下の環境変数が設定されていません:")
        if not app_id:
            print("   - LARK_APP_ID")
        if not app_secret:
            print("   - LARK_APP_SECRET")
        if not base_token:
            print("   - LARK_BASE_TOKEN")
        print("\n📝 .envファイルを確認してください")
        sys.exit(1)
    
    print(f"\n📝 .envファイルから設定を読み込みました:")
    print(f"App ID: {app_id}")
    print(f"App Secret: {app_secret[:8]}...")
    print(f"Base Token: {base_token}")
    
    print("\n🔐 アクセストークンを取得中...")
    access_token = get_access_token(app_id, app_secret)
    
    if not access_token:
        print("❌ アクセストークンの取得に失敗しました")
        print("\n🔧 確認事項:")
        print("1. App IDとApp Secretが正しいか確認")
        print("2. Larkアプリが正しく作成されているか確認")
        print("3. インターネット接続を確認")
        sys.exit(1)
    
    print("✅ アクセストークン取得成功")
    
    print("\n📊 テーブル一覧を取得中...")
    tables = get_tables_info(base_token, access_token)
    
    if not tables:
        print("❌ テーブル情報の取得に失敗しました")
        print("\n🔧 確認事項:")
        print("1. Base Tokenが正しいか確認")
        print("2. Larkアプリに適切な権限があるか確認")
        print("3. ベースにアクセス権限があるか確認")
        sys.exit(1)
    
    print(f"✅ {len(tables)}個のテーブルを発見")
    
    print("\n" + "=" * 80)
    print("📋 利用可能なテーブル一覧")
    print("=" * 80)
    
    for i, table in enumerate(tables, 1):
        table_id = table.get("table_id", "")
        table_name = table.get("name", "名前なし")
        
        print(f"\n{i}. テーブル名: {table_name}")
        print(f"   Table ID: {table_id}")
        
        # フィールド情報も取得
        print("   📝 フィールド情報を取得中...")
        fields = get_table_fields(base_token, table_id, access_token)
        
        if fields:
            print(f"   📊 フィールド数: {len(fields)}個")
            print("   📋 フィールド一覧:")
            
            # セミナーURLフィールドを特定するため、全フィールドを表示
            seminar_url_fields = []
            for field in fields:
                field_name = field.get("field_name", "名前なし")
                field_type = field.get("type", "不明")
                print(f"      - {field_name} ({field_type})")
                
                # セミナーURLに関連しそうなフィールドをマーク
                if any(keyword in field_name.lower() for keyword in ['url', 'セミナー', 'seminar', 'link', 'リンク']):
                    seminar_url_fields.append(field_name)
            
            # セミナーURL関連フィールドがあれば強調表示
            if seminar_url_fields:
                print(f"   🎯 セミナーURL関連フィールド: {', '.join(seminar_url_fields)}")
        else:
            print("   ❌ フィールド情報の取得に失敗")
        
        print("-" * 80)
    
    print("\n🎯 .envファイル用の設定値")
    print("=" * 50)
    print(f"LARK_APP_ID={app_id}")
    print(f"LARK_APP_SECRET={app_secret}")
    print(f"LARK_BASE_TOKEN={base_token}")
    
    if len(tables) == 1:
        print(f"LARK_TABLE_ID={tables[0]['table_id']}")
        print("\n✅ テーブルが1つだけなので、このTable IDを使用してください")
    else:
        print("LARK_TABLE_ID=<使用したいテーブルのTable IDを上記から選択>")
        print(f"\n📝 {len(tables)}個のテーブルがあります。")
        print("   イベント管理に使用するテーブルのTable IDを.envファイルに設定してください")
    
    print("\n🔧 次のステップ:")
    print("1. 上記の設定値を .env ファイルにコピー")
    print("2. 適切なTable IDを選択して設定")
    print("3. Discord Botの設定を完了")
    print("4. python3 run.py でBotを実行")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 処理を中断しました")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 予期しないエラーが発生しました: {e}")
        sys.exit(1)