#!/usr/bin/env python3
"""
実際のLarkイベントデータを使用してwebhook機能をテストするスクリプト
"""

import json
import asyncio
import sys
import os
from datetime import datetime, timezone

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.webhook import create_discord_event_and_announcement

def load_real_event_data():
    """実際のLarkイベントデータを読み込み"""
    with open('real_mori_manus_event_data.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def create_test_webhook_data(real_data):
    """実際のLarkデータからwebhook形式のテストデータを作成"""
    fields = real_data['fields']
    
    # 実際のLarkデータの日時情報を未来の日時に調整
    original_start = fields.get("イベント開始日時", 0)
    original_end = fields.get("イベント終了日時", 0)
    
    # 実際のデータの開始・終了時間の差を計算
    duration_ms = original_end - original_start if original_end and original_start else 2 * 60 * 60 * 1000  # デフォルト2時間
    
    # 未来の日時を設定（現在時刻から1時間後）
    future_start_ms = int((datetime.now(timezone.utc).timestamp() + 3600) * 1000)  # 1時間後
    future_end_ms = future_start_ms + duration_ms
    
    # 実際のLarkデータ構造に合わせてwebhookデータを作成
    webhook_data = {
        "record_id": real_data['record_id'],
        "fields": {
            # 基本情報
            "イベントタイトル": fields.get("イベントタイトル", ""),
            "登壇者(セレクト)": fields.get("登壇者(セレクト)", []),
            
            # 日時情報（未来の日時に調整）
            "イベント開始日時": future_start_ms,  # Unix timestamp (ms)
            "イベント終了日時": future_end_ms,  # Unix timestamp (ms)
            
            # URL情報
            "セミナーURL": fields.get("セミナーURL", {}),
            "本番Peatixページ": fields.get("本番Peatixページ", {}),
            
            # 画像情報
            "サムネイル": fields.get("サムネイル", []),
            
            # 特典情報
            "特典配布": fields.get("特典配布", False),
            
            # イベント概要（実際のデータにはないため、テスト用に追加）
            "イベント概要": "AIとNotionを組み合わせた次世代の情報活用術を学べるセミナーです。実践的な内容で、業務効率化や情報整理のスキルを身につけることができます。参加者限定の特典もご用意しています。"
        }
    }
    
    return webhook_data

async def test_real_webhook():
    """実際のデータを使ってwebhook機能をテスト"""
    print("🚀 実際のLarkデータを使用したwebhookテストを開始...")
    
    try:
        # 実際のLarkデータを読み込み
        real_data = load_real_event_data()
        print(f"✅ 実際のLarkデータを読み込み完了: {real_data['record_id']}")
        
        # webhook形式のテストデータを作成
        webhook_data = create_test_webhook_data(real_data)
        print(f"✅ webhookテストデータを作成完了")
        
        # データ構造を確認
        print("\n📋 テストデータの構造:")
        print(f"  - イベントタイトル: {webhook_data['fields'].get('イベントタイトル')}")
        print(f"  - 登壇者: {webhook_data['fields'].get('登壇者(セレクト)')}")
        
        # 実際のLarkデータの日時を表示
        real_data = load_real_event_data()
        original_start = real_data['fields'].get("イベント開始日時", 0)
        original_end = real_data['fields'].get("イベント終了日時", 0)
        if original_start:
            original_start_dt = datetime.fromtimestamp(original_start / 1000, tz=timezone.utc)
            print(f"  - 実際のLarkデータ開始日時: {original_start_dt.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        if original_end:
            original_end_dt = datetime.fromtimestamp(original_end / 1000, tz=timezone.utc)
            print(f"  - 実際のLarkデータ終了日時: {original_end_dt.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        # 調整後の日時を表示
        start_timestamp_ms = webhook_data['fields'].get('イベント開始日時', 0)
        end_timestamp_ms = webhook_data['fields'].get('イベント終了日時', 0)
        if start_timestamp_ms:
            start_dt = datetime.fromtimestamp(start_timestamp_ms / 1000, tz=timezone.utc)
            print(f"  - テスト用調整後開始日時: {start_dt.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        if end_timestamp_ms:
            end_dt = datetime.fromtimestamp(end_timestamp_ms / 1000, tz=timezone.utc)
            print(f"  - テスト用調整後終了日時: {end_dt.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        print(f"  - 特典配布: {webhook_data['fields'].get('特典配布')}")
        
        print(f"\n🔗 URL情報:")
        seminar_url = webhook_data['fields'].get('セミナーURL', {})
        peatix_url = webhook_data['fields'].get('本番Peatixページ', {})
        print(f"  - セミナーURL: {seminar_url.get('link', 'なし')}")
        print(f"  - PeatixURL: {peatix_url.get('link', 'なし')}")
        
        print(f"\n🖼️ サムネイル情報:")
        thumbnail = webhook_data['fields'].get('サムネイル', [])
        if thumbnail:
            print(f"  - ファイル名: {thumbnail[0].get('name', 'なし')}")
            print(f"  - ファイルサイズ: {thumbnail[0].get('size', 0)} bytes")
        else:
            print("  - サムネイルなし")
        
        print(f"\n📝 イベント概要:")
        overview = webhook_data['fields'].get('イベント概要', '')
        print(f"  {overview[:100]}..." if len(overview) > 100 else f"  {overview}")
        
        # webhook関数を実行
        print(f"\n🎯 Discord webhook関数を実行中...")
        result = await create_discord_event_and_announcement(webhook_data)
        
        if result.get('success'):
            print(f"✅ webhook実行成功!")
            print(f"📅 Discordイベント作成: {result.get('discord_event', {}).get('name', 'N/A')}")
            print(f"📢 アナウンスメント投稿: 完了")
            
            # 結果の詳細を表示
            discord_event = result.get('discord_event', {})
            if discord_event:
                print(f"\n📋 作成されたDiscordイベントの詳細:")
                print(f"  - イベントID: {discord_event.get('id')}")
                print(f"  - イベント名: {discord_event.get('name')}")
                print(f"  - 開始時間: {discord_event.get('start_time')}")
                print(f"  - 終了時間: {discord_event.get('end_time')}")
                print(f"  - イベントURL: {discord_event.get('url')}")
                print(f"  - 説明: {discord_event.get('description', '')[:100]}...")
                print(f"  - カバー画像: {'あり' if discord_event.get('has_cover') else 'なし'}")
            
            announcement = result.get('announcement', {})
            if announcement:
                print(f"\n📢 投稿されたアナウンスメントの詳細:")
                print(f"  - メッセージID: {announcement.get('id')}")
                print(f"  - チャンネルID: {announcement.get('channel_id')}")
        else:
            print(f"❌ webhook実行失敗: {result.get('error', '不明なエラー')}")
            
    except Exception as e:
        print(f"❌ テスト実行中にエラーが発生: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 実際のLarkデータを使用したWebhookテスト")
    print("=" * 60)
    
    # 環境変数の確認
    required_env_vars = [
        'DISCORD_BOT_TOKEN',
        'DISCORD_GUILD_ID', 
        'DISCORD_NOTIFICATION_CHANNEL_ID',
        'LARK_APP_ID',
        'LARK_APP_SECRET',
        'LARK_TABLE_ID'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ 以下の環境変数が設定されていません: {', '.join(missing_vars)}")
        print("💡 .envファイルを確認してください")
        sys.exit(1)
    
    print("✅ 環境変数の確認完了")
    
    # テスト実行
    asyncio.run(test_real_webhook())