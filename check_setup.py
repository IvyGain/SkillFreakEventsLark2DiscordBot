#!/usr/bin/env python3
"""
🔧 SkillFreak Events Bot 設定確認ツール

このスクリプトは、Bot実行前に必要な設定がすべて正しく行われているかを確認します。
初心者の方でも分かりやすいように、詳細な説明とトラブルシューティング情報を提供します。

使用方法:
    python3 check_setup.py

実行前に必要なもの:
    1. .envファイルが作成されていること
    2. 必要なライブラリがインストールされていること (pip3 install -r requirements.txt)
"""

import asyncio
import os
import sys
import aiohttp
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def print_header(title):
    """セクションヘッダーを表示"""
    print(f"\n{'='*60}")
    print(f"📋 {title}")
    print('='*60)

def print_step(step_num, title):
    """ステップタイトルを表示"""
    print(f"\n🔸 ステップ {step_num}: {title}")
    print("-" * 40)

def check_env_file():
    """
    .envファイルの存在確認
    """
    print_step(1, ".envファイルの確認")
    
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .envファイルが見つかりません")
        print("\n💡 解決方法:")
        print("1. .env.exampleファイルをコピーして.envファイルを作成してください")
        print("   コマンド: cp .env.example .env")
        print("2. .envファイルを開いて、必要な値を設定してください")
        print("3. 設定方法は SETUP_GUIDE.md を参照してください")
        return False
    
    print("✅ .envファイルが存在します")
    
    # .envファイルを読み込み
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ .envファイルの読み込み成功")
        return True
    except Exception as e:
        print(f"❌ .envファイルの読み込みエラー: {e}")
        print("\n💡 解決方法:")
        print("1. .envファイルの形式を確認してください")
        print("2. 不正な文字や改行がないか確認してください")
        return False

def check_environment():
    """環境変数の確認"""
    print_step(2, "環境変数の設定確認")
    
    required_vars = {
        'LARK_APP_ID': 'Larkアプリケーションのアプリケーションid (cli_で始まる)',
        'LARK_APP_SECRET': 'Larkアプリケーションのアプリケーションシークレット',
        'LARK_BASE_TOKEN': 'Larkベースのトークン',
        'LARK_TABLE_ID': 'Larkテーブルのid (tblで始まる)',
        'DISCORD_BOT_TOKEN': 'Discord BotのToken',
        'DISCORD_GUILD_ID': 'DiscordサーバーのID (数字)',
        'DISCORD_NOTIFICATION_CHANNEL_ID': '通知を送信するチャンネルのID (数字)',
        'DISCORD_ARCHIVE_FORUM_ID': 'アーカイブ用フォーラムチャンネルのID (数字)'
    }
    
    missing_vars = []
    invalid_vars = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value or value.strip() == "":
            print(f"❌ {var}: 未設定")
            print(f"   説明: {description}")
            missing_vars.append(var)
        else:
            # 値の形式チェック
            is_valid = True
            
            if var == 'LARK_APP_ID' and not value.startswith('cli_'):
                is_valid = False
                print(f"❌ {var}: 形式が正しくありません (cli_で始まる必要があります)")
            elif var == 'LARK_TABLE_ID' and not value.startswith('tbl'):
                is_valid = False
                print(f"❌ {var}: 形式が正しくありません (tblで始まる必要があります)")
            elif 'DISCORD_' in var and 'ID' in var and (not value.isdigit() or len(value) < 15):
                is_valid = False
                print(f"❌ {var}: 形式が正しくありません (15桁以上の数字である必要があります)")
            else:
                # 機密情報は一部のみ表示
                if 'TOKEN' in var or 'SECRET' in var:
                    display_value = f"{value[:8]}..." if len(value) > 8 else "***"
                else:
                    display_value = value
                print(f"✅ {var}: {display_value}")
            
            if not is_valid:
                invalid_vars.append(var)
    
    if missing_vars or invalid_vars:
        print(f"\n⚠️  問題が見つかりました:")
        if missing_vars:
            print(f"   未設定: {len(missing_vars)}個")
        if invalid_vars:
            print(f"   形式エラー: {len(invalid_vars)}個")
        
        print("\n💡 解決方法:")
        print("1. SETUP_GUIDE.md の手順に従って環境変数を設定してください")
        print("2. get_table_info.py を実行してTable IDを取得してください")
        print("3. Discord Developer Portal で正しいIDを確認してください")
        return False
    else:
        print("\n✅ 全ての環境変数が設定されています")
        return True

def check_dependencies():
    """
    必要なライブラリがインストールされているかチェック
    """
    print_step(3, "必要なライブラリの確認")
    
    required_packages = {
        'discord.py': 'Discord Bot開発用ライブラリ',
        'aiohttp': 'HTTP通信用ライブラリ',
        'requests': 'HTTP通信用ライブラリ',
        'python-dotenv': '環境変数読み込み用ライブラリ',
        'apscheduler': 'スケジューラーライブラリ',
        'pytz': 'タイムゾーン処理用ライブラリ',
        'pydantic': 'データ検証用ライブラリ'
    }
    
    missing_packages = []
    
    for package, description in required_packages.items():
        try:
            if package == 'discord.py':
                import discord
            elif package == 'python-dotenv':
                import dotenv
            elif package == 'apscheduler':
                import apscheduler
            else:
                __import__(package)
            print(f"✅ {package}: インストール済み")
        except ImportError:
            print(f"❌ {package}: 未インストール")
            print(f"   説明: {description}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  {len(missing_packages)}個のライブラリが不足しています")
        print("\n💡 解決方法:")
        print("以下のコマンドを実行してライブラリをインストールしてください:")
        print("   pip3 install -r requirements.txt")
        print("\nまたは個別にインストール:")
        for package in missing_packages:
            print(f"   pip3 install {package}")
        return False
    
    print("\n✅ すべての必要なライブラリがインストールされています")
    return True

async def check_lark_connection():
    """Lark API接続確認"""
    print_step(4, "Lark API接続テスト")
    
    # 環境変数の取得
    app_id = os.getenv('LARK_APP_ID')
    app_secret = os.getenv('LARK_APP_SECRET')
    base_token = os.getenv('LARK_BASE_TOKEN')
    table_id = os.getenv('LARK_TABLE_ID')
    
    if not all([app_id, app_secret, base_token, table_id]):
        print("❌ Lark関連の環境変数が不足しています")
        return False
    
    try:
        print("🔐 Lark認証テスト中...")
        
        # 認証API呼び出し
        auth_url = "https://open.larksuite.com/open-apis/auth/v3/app_access_token/internal"
        auth_payload = {
            "app_id": app_id,
            "app_secret": app_secret
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(auth_url, json=auth_payload) as response:
                auth_data = await response.json()
                
                if auth_data.get("code") != 0:
                    print(f"❌ Lark認証エラー: {auth_data.get('msg', 'Unknown error')}")
                    print("\n💡 解決方法:")
                    print("1. LARK_APP_ID が正しいか確認してください (cli_で始まる)")
                    print("2. LARK_APP_SECRET が正しいか確認してください")
                    print("3. Lark開発者コンソールでアプリの状態を確認してください")
                    return False
                
                access_token = auth_data.get("app_access_token")
                print("✅ Lark認証成功")
                
                print("📋 テーブルアクセステスト中...")
                
                # テーブルアクセステスト
                table_url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{base_token}/tables/{table_id}/records"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
                
                async with session.get(table_url, headers=headers) as response:
                    table_data = await response.json()
                    
                    if table_data.get("code") != 0:
                        print(f"❌ テーブルアクセスエラー: {table_data.get('msg', 'Unknown error')}")
                        print("\n💡 解決方法:")
                        print("1. LARK_BASE_TOKEN が正しいか確認してください")
                        print("2. LARK_TABLE_ID が正しいか確認してください (tblで始まる)")
                        print("3. get_table_info.py を実行して正しいTable IDを取得してください")
                        print("4. Larkアプリに以下の権限が設定されているか確認してください:")
                        print("   - ビューとテーブルの読み取り")
                        print("   - レコードの読み取り")
                        return False
                    
                    records = table_data.get("data", {}).get("items", [])
                    print(f"✅ テーブルアクセス成功")
                    print(f"📊 テーブル内のレコード数: {len(records)}件")
                    
                    if len(records) == 0:
                        print("⚠️  テーブルにレコードがありません")
                        print("💡 テーブルにイベントデータを追加してからテストしてください")
                    
                    return True
                    
    except aiohttp.ClientError as e:
        print(f"❌ ネットワークエラー: {e}")
        print("\n💡 解決方法:")
        print("1. インターネット接続を確認してください")
        print("2. ファイアウォールの設定を確認してください")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

async def check_discord_connection():
    """Discord Bot接続確認"""
    print_step(5, "Discord Bot接続テスト")
    
    # 環境変数の取得
    bot_token = os.getenv('DISCORD_BOT_TOKEN')
    guild_id = os.getenv('DISCORD_GUILD_ID')
    channel_id = os.getenv('DISCORD_NOTIFICATION_CHANNEL_ID')
    forum_id = os.getenv('DISCORD_ARCHIVE_FORUM_ID')
    
    if not all([bot_token, guild_id, channel_id, forum_id]):
        print("❌ Discord関連の環境変数が不足しています")
        return False
    
    try:
        import discord
        from discord.ext import commands
        
        print("🤖 Discord Bot接続テスト中...")
        
        # Bot設定
        intents = discord.Intents.default()
        intents.message_content = True
        
        bot = commands.Bot(command_prefix='!', intents=intents)
        
        connection_success = False
        
        @bot.event
        async def on_ready():
            nonlocal connection_success
            print(f"✅ Discord Bot接続成功: {bot.user}")
            
            # ギルド確認
            guild = bot.get_guild(int(guild_id))
            if guild:
                print(f"✅ サーバー確認成功: {guild.name}")
                
                # チャンネル確認
                channel = guild.get_channel(int(channel_id))
                forum = guild.get_channel(int(forum_id))
                
                if channel:
                    print(f"✅ 通知チャンネル確認成功: #{channel.name}")
                    
                    # チャンネルタイプ確認
                    if isinstance(channel, discord.TextChannel):
                        print("✅ 通知チャンネルはテキストチャンネルです")
                    else:
                        print(f"⚠️  通知チャンネルのタイプ: {type(channel).__name__}")
                        print("💡 テキストチャンネルを使用することを推奨します")
                else:
                    print(f"❌ 通知チャンネルが見つかりません (ID: {channel_id})")
                    print("💡 チャンネルIDを確認するか、Botに適切な権限を付与してください")
                
                if forum:
                    print(f"✅ フォーラムチャンネル確認成功: #{forum.name}")
                    
                    # フォーラムタイプ確認
                    if isinstance(forum, discord.ForumChannel):
                        print("✅ アーカイブチャンネルはフォーラムチャンネルです")
                    else:
                        print(f"⚠️  アーカイブチャンネルのタイプ: {type(forum).__name__}")
                        print("💡 フォーラムチャンネルを使用することを推奨します")
                else:
                    print(f"❌ フォーラムチャンネルが見つかりません (ID: {forum_id})")
                    print("💡 チャンネルIDを確認するか、Botに適切な権限を付与してください")
                
                # 権限確認
                bot_member = guild.get_member(bot.user.id)
                if bot_member:
                    permissions = bot_member.guild_permissions
                    required_perms = [
                        ('send_messages', 'メッセージ送信'),
                        ('embed_links', 'リンク埋め込み'),
                        ('create_public_threads', 'パブリックスレッド作成'),
                        ('send_messages_in_threads', 'スレッド内メッセージ送信')
                    ]
                    
                    print("\n🔐 Bot権限確認:")
                    for perm, desc in required_perms:
                        if getattr(permissions, perm):
                            print(f"✅ {desc}")
                        else:
                            print(f"❌ {desc}")
                            print(f"💡 Botに '{desc}' 権限を付与してください")
                
                connection_success = True
            else:
                print(f"❌ サーバーが見つかりません (ID: {guild_id})")
                print("\n💡 解決方法:")
                print("1. DISCORD_GUILD_ID が正しいか確認してください")
                print("2. Botがサーバーに招待されているか確認してください")
                print("3. SETUP_GUIDE.md の手順に従ってBotを招待してください")
            
            await bot.close()
        
        # 短時間だけ接続テスト
        await asyncio.wait_for(bot.start(bot_token), timeout=15.0)
        return connection_success
        
    except asyncio.TimeoutError:
        print("❌ Discord接続タイムアウト")
        print("\n💡 解決方法:")
        print("1. インターネット接続を確認してください")
        print("2. Discord Bot Tokenが正しいか確認してください")
        return False
    except discord.LoginFailure:
        print("❌ Discord Bot Token が無効です")
        print("\n💡 解決方法:")
        print("1. Discord Developer Portal でBot Tokenを再確認してください")
        print("2. Tokenをコピーし直してください")
        print("3. Botが無効化されていないか確認してください")
        return False
    except Exception as e:
        print(f"❌ Discord接続エラー: {e}")
        print("\n💡 解決方法:")
        print("1. discord.py ライブラリがインストールされているか確認してください")
        print("2. 環境変数の設定を確認してください")
        return False

def check_file_structure():
    """プロジェクトファイル構造確認"""
    print_step(7, "プロジェクトファイル構造確認")
    
    required_files = [
        'src/main.py',
        'src/config/settings.py',
        'src/lark/client.py',
        'src/discord/bot.py',
        'src/discord/formatters.py',
        'src/services/scheduler.py',
        'requirements.txt',
        '.env.example'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}: ファイルが見つかりません")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️  {len(missing_files)}個のファイルが不足しています")
        print("💡 プロジェクトファイルが正しく配置されているか確認してください")
        return False
    
    print("\n✅ すべての必要なファイルが存在します")
    return True

async def main():
    """メイン実行関数"""
    print_header("SkillFreak Events Bot 設定確認ツール")
    
    print("このツールは、Bot実行前に必要な設定がすべて正しく行われているかを確認します。")
    print("問題が見つかった場合は、詳細な解決方法も表示されます。")
    
    all_checks_passed = True
    
    # ステップ1: .envファイル確認
    if not check_env_file():
        all_checks_passed = False
        print("\n❌ .envファイルの設定を完了してから再実行してください")
        return
    
    # ステップ2: 環境変数確認
    if not check_environment():
        all_checks_passed = False
    
    # ステップ3: 依存関係確認
    if not check_dependencies():
        all_checks_passed = False
        print("\n❌ 必要なライブラリをインストールしてから再実行してください")
        return
    
    # ステップ4: Lark API接続テスト
    if not await check_lark_connection():
        all_checks_passed = False
    
    # ステップ5: Discord Bot接続テスト
    if not await check_discord_connection():
        all_checks_passed = False
    
    # ステップ6: ファイル構造確認
    if not check_file_structure():
        all_checks_passed = False
    
    # 結果サマリー
    print_header("確認結果")
    
    if all_checks_passed:
        print("🎉 おめでとうございます！すべてのチェックが完了しました！")
        print("✅ Bot を実行する準備ができています")
        print("\n🚀 次のステップ:")
        print("1. 以下のコマンドでBotを起動してください:")
        print("   python3 run.py")
        print("\n2. Botが正常に起動したら、Discordサーバーで以下のコマンドをテストしてください:")
        print("   /events - 今日のイベントを表示")
        print("   /bot-info - Bot情報を表示")
        print("\n3. 問題が発生した場合は、ターミナルのログを確認してください")
        
    else:
        print("❌ いくつかの問題が見つかりました")
        print("💡 上記のエラーメッセージと解決方法を参考に、問題を修正してください")
        print("\n🔧 よくある問題と解決方法:")
        print("1. 環境変数の設定ミス → SETUP_GUIDE.md を参照")
        print("2. Table IDが不明 → get_table_info.py を実行")
        print("3. Discord IDが不明 → Discord開発者モードでIDをコピー")
        print("4. ライブラリ不足 → pip3 install -r requirements.txt")
        print("\n🔄 問題を修正したら、再度このスクリプトを実行してください:")
        print("   python3 check_setup.py")

if __name__ == "__main__":
    asyncio.run(main())