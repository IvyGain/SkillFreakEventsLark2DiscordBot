#!/usr/bin/env python3
"""
サムネイル画像処理のテストスクリプト
"""

import json
import asyncio
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.lark.models import LarkEventRecord, create_field_mapping


async def test_thumbnail_processing():
    """サムネイル画像処理をテスト"""
    print("🧪 サムネイル画像処理テストを開始...")
    
    # テストデータファイルを読み込み
    test_files = [
        "morrie_oct_2025_event_1.json",
        "morrie_event_detail_1.json",
        "real_mori_manus_event_data.json"
    ]
    
    field_mapping = create_field_mapping()
    
    for test_file in test_files:
        file_path = project_root / test_file
        if not file_path.exists():
            print(f"⚠️  テストファイルが見つかりません: {test_file}")
            continue
            
        print(f"\n📄 テストファイル: {test_file}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                event_data = json.load(f)
            
            # LarkEventRecordオブジェクトを作成
            record_data = {
                'record_id': event_data.get('record_id', 'test_id'),
            }
            
            # フィールドマッピングに基づいてデータを変換
            fields = event_data.get('fields', {})
            for model_field, lark_field in field_mapping.items():
                value = fields.get(lark_field)
                record_data[model_field] = value
            
            # LarkEventRecordを作成
            event_record = LarkEventRecord(**record_data)
            
            # サムネイル情報を表示
            print(f"  📋 イベントタイトル: {event_record.get_title()}")
            print(f"  🖼️  サムネイルURL: {event_record.thumbnail_url}")
            
            if event_record.thumbnail_url:
                print(f"  ✅ サムネイル画像が正常に取得されました")
                print(f"     URL: {event_record.thumbnail_url[:100]}...")
            else:
                print(f"  ❌ サムネイル画像が取得できませんでした")
                
                # デバッグ情報を表示
                thumbnail_field = fields.get('サムネイル')
                print(f"     サムネイルフィールドの内容: {thumbnail_field}")
            
        except Exception as e:
            print(f"  ❌ エラーが発生しました: {str(e)}")
    
    print("\n🎯 サムネイル画像処理テスト完了")


async def test_discord_formatter():
    """Discord Formatterでのサムネイル処理をテスト"""
    print("\n🎨 Discord Formatter サムネイルテストを開始...")
    
    try:
        from src.discord.formatters import DiscordFormatter
        
        # テストイベントデータを作成
        test_file = project_root / "morrie_oct_2025_event_1.json"
        if not test_file.exists():
            print("⚠️  テストファイルが見つかりません")
            return
        
        with open(test_file, 'r', encoding='utf-8') as f:
            event_data = json.load(f)
        
        # LarkEventRecordを作成
        field_mapping = create_field_mapping()
        record_data = {'record_id': event_data.get('record_id', 'test_id')}
        fields = event_data.get('fields', {})
        
        for model_field, lark_field in field_mapping.items():
            value = fields.get(lark_field)
            record_data[model_field] = value
        
        event_record = LarkEventRecord(**record_data)
        
        # Embedを作成
        embed = DiscordFormatter.create_today_events_embed([event_record])
        
        print(f"  📋 Embed タイトル: {embed.title}")
        print(f"  🖼️  Embed サムネイル: {embed.thumbnail.url if embed.thumbnail else 'なし'}")
        
        if embed.thumbnail and embed.thumbnail.url:
            print(f"  ✅ Discord Embed にサムネイルが正常に設定されました")
        else:
            print(f"  ❌ Discord Embed にサムネイルが設定されませんでした")
        
        # アーカイブ用Embedもテスト
        archive_embed = DiscordFormatter.create_event_archive_embed(event_record)
        print(f"  📋 アーカイブ Embed サムネイル: {archive_embed.thumbnail.url if archive_embed.thumbnail else 'なし'}")
        
    except Exception as e:
        print(f"  ❌ Discord Formatter テストでエラーが発生しました: {str(e)}")
    
    print("🎨 Discord Formatter サムネイルテスト完了")


async def main():
    """メイン関数"""
    print("🚀 サムネイル画像処理の総合テストを開始...")
    
    await test_thumbnail_processing()
    await test_discord_formatter()
    
    print("\n✨ 全てのテストが完了しました！")


if __name__ == "__main__":
    asyncio.run(main())