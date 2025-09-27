# Lark to Discord Events Bot 設計書

## 概要
Larkのベーステーブルからイベント情報を取得し、Discordに自動通知するBotシステム。
本日のイベント告知とフォーラム形式のアーカイブチャンネルでのスレッド作成機能を提供。

## 主要機能

### 1. 本日のイベント告知機能
- Larkのイベントテーブルから本日のイベントを取得
- Discord指定チャンネルに整形されたイベント情報を投稿
- 定期実行（例：毎朝9時）

### 2. アーカイブフォーラム機能
- 過去のイベントをフォーラム形式のチャンネルにアーカイブ
- イベントごとにスレッドを作成
- イベント詳細情報を含む投稿

## システムアーキテクチャ

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Lark Base     │    │   Discord Bot   │    │   Discord       │
│   (Events)      │◄───┤   Application   ├───►│   Server        │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Scheduler     │
                       │   (Cron Jobs)   │
                       └─────────────────┘
```

## 技術スタック
- **言語**: Python 3.9+
- **フレームワーク**: discord.py
- **HTTP クライアント**: aiohttp
- **スケジューラー**: APScheduler
- **設定管理**: python-dotenv
- **ログ**: logging

## ディレクトリ構造

```
SkillFreakEventsLark2DiscordBot/
├── src/
│   ├── __init__.py
│   ├── main.py                 # メインエントリーポイント
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py         # 設定管理
│   ├── lark/
│   │   ├── __init__.py
│   │   ├── client.py           # Lark API クライアント
│   │   └── models.py           # Lark データモデル
│   ├── discord/
│   │   ├── __init__.py
│   │   ├── bot.py              # Discord Bot メイン
│   │   ├── commands.py         # Discord コマンド
│   │   └── formatters.py       # メッセージフォーマッター
│   ├── services/
│   │   ├── __init__.py
│   │   ├── event_service.py    # イベント処理サービス
│   │   └── scheduler.py        # スケジューラー
│   └── utils/
│       ├── __init__.py
│       ├── logger.py           # ログ設定
│       └── helpers.py          # ユーティリティ関数
├── tests/
│   ├── __init__.py
│   ├── test_lark.py
│   ├── test_discord.py
│   └── test_services.py
├── .env.example                # 環境変数テンプレート
├── .gitignore
├── requirements.txt
├── README.md
└── DESIGN.md
```

## データフロー

### 1. イベント取得フロー
```
1. スケジューラーが定期実行をトリガー
2. Lark API クライアントがベーステーブルからイベントデータを取得
3. イベントサービスがデータを処理・フィルタリング
4. Discord フォーマッターがメッセージを整形
5. Discord Bot がチャンネルに投稿
```

### 2. アーカイブフロー
```
1. 過去のイベントを検索
2. フォーラムチャンネルに新しいスレッドを作成
3. イベント詳細をスレッドに投稿
4. 必要に応じてタグ付け
```

## API 仕様

### Lark API 連携
- **ベーステーブル読み取り**: イベント情報の取得
- **認証**: App Token 方式
- **必要な権限**: 
  - `bitable:app`
  - `bitable:app:readonly`

### Discord API 連携
- **メッセージ送信**: 通常チャンネルへの投稿
- **フォーラムスレッド作成**: フォーラムチャンネルでのスレッド作成
- **必要な権限**:
  - `Send Messages`
  - `Create Public Threads`
  - `Send Messages in Threads`

## 設定項目

### 環境変数
```
# Lark 設定
LARK_APP_ID=your_lark_app_id
LARK_APP_SECRET=your_lark_app_secret
LARK_BASE_TOKEN=your_base_token
LARK_TABLE_ID=your_table_id

# Discord 設定
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_GUILD_ID=your_guild_id
DISCORD_NOTIFICATION_CHANNEL_ID=your_notification_channel_id
DISCORD_ARCHIVE_FORUM_ID=your_archive_forum_id

# スケジューラー設定
NOTIFICATION_SCHEDULE=0 9 * * *  # 毎日9時
ARCHIVE_SCHEDULE=0 22 * * *      # 毎日22時

# ログ設定
LOG_LEVEL=INFO
```

## エラーハンドリング
- API レート制限対応
- ネットワークエラーのリトライ機能
- 設定値検証
- 詳細なログ出力

## セキュリティ考慮事項
- 環境変数による機密情報管理
- API トークンの適切な権限設定
- ログでの機密情報マスキング

## 拡張性
- 複数のLarkベースへの対応
- カスタムメッセージテンプレート
- Webhook による即座通知
- 多言語対応

## 運用考慮事項
- ヘルスチェック機能
- メトリクス収集
- 障害時の通知機能
- バックアップ・復旧手順