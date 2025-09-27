# Lark to Discord Events Bot

Larkのベーステーブルからイベント情報を取得し、Discordに自動通知するBotシステムです。

## 機能

- **本日のイベント告知**: Larkのイベントテーブルから本日のイベントを取得し、Discord指定チャンネルに投稿
- **アーカイブフォーラム**: 過去のイベントをフォーラム形式のチャンネルにアーカイブし、スレッドを作成

## 必要な環境

- Python 3.9+
- Lark (Feishu) アプリケーション
- Discord Bot アプリケーション

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env.example`をコピーして`.env`ファイルを作成し、必要な値を設定してください。

```bash
cp .env.example .env
```

### 3. Lark アプリケーションの設定

1. [Lark Developer Console](https://open.larksuite.com/)でアプリを作成
2. 必要な権限を設定:
   - `bitable:app`
   - `bitable:app:readonly`
3. App ID と App Secret を取得

### 4. Discord Bot の設定

1. [Discord Developer Portal](https://discord.com/developers/applications)でアプリケーションを作成
2. Bot を作成し、トークンを取得
3. 必要な権限を設定:
   - `Send Messages`
   - `Create Public Threads`
   - `Send Messages in Threads`
4. サーバーにBotを招待

## 使用方法

### 基本実行

```bash
python src/main.py
```

### 開発モード

```bash
python -m src.main
```

## 設定

### 環境変数

| 変数名 | 説明 | 必須 |
|--------|------|------|
| `LARK_APP_ID` | Lark アプリケーション ID | ✓ |
| `LARK_APP_SECRET` | Lark アプリケーション Secret | ✓ |
| `LARK_BASE_TOKEN` | Lark ベース トークン | ✓ |
| `LARK_TABLE_ID` | Lark テーブル ID | ✓ |
| `DISCORD_BOT_TOKEN` | Discord Bot トークン | ✓ |
| `DISCORD_GUILD_ID` | Discord サーバー ID | ✓ |
| `DISCORD_NOTIFICATION_CHANNEL_ID` | 通知チャンネル ID | ✓ |
| `DISCORD_ARCHIVE_FORUM_ID` | アーカイブフォーラム ID | ✓ |
| `NOTIFICATION_SCHEDULE` | 通知スケジュール (cron形式) | - |
| `ARCHIVE_SCHEDULE` | アーカイブスケジュール (cron形式) | - |
| `LOG_LEVEL` | ログレベル | - |

### スケジュール設定

cron形式でスケジュールを設定できます：

- `0 9 * * *` - 毎日9時
- `0 22 * * *` - 毎日22時
- `0 9 * * 1-5` - 平日の9時

## プロジェクト構造

```
SkillFreakEventsLark2DiscordBot/
├── src/
│   ├── main.py                 # メインエントリーポイント
│   ├── config/
│   │   └── settings.py         # 設定管理
│   ├── lark/
│   │   ├── client.py           # Lark API クライアント
│   │   └── models.py           # Lark データモデル
│   ├── discord/
│   │   ├── bot.py              # Discord Bot メイン
│   │   ├── commands.py         # Discord コマンド
│   │   └── formatters.py       # メッセージフォーマッター
│   ├── services/
│   │   ├── event_service.py    # イベント処理サービス
│   │   └── scheduler.py        # スケジューラー
│   └── utils/
│       ├── logger.py           # ログ設定
│       └── helpers.py          # ユーティリティ関数
├── tests/                      # テストファイル
├── .env.example               # 環境変数テンプレート
├── requirements.txt           # 依存関係
└── README.md                  # このファイル
```

## 開発

### テスト実行

```bash
pytest tests/
```

### コードフォーマット

```bash
black src/
```

### 型チェック

```bash
mypy src/
```

## トラブルシューティング

### よくある問題

1. **Lark API エラー**
   - App ID と App Secret が正しいか確認
   - ベーストークンとテーブルIDが正しいか確認
   - 必要な権限が設定されているか確認

2. **Discord API エラー**
   - Bot トークンが正しいか確認
   - チャンネルIDが正しいか確認
   - Botに必要な権限があるか確認

3. **スケジューラーが動作しない**
   - cron形式が正しいか確認
   - タイムゾーン設定を確認

## ライセンス

MIT License

## 貢献

プルリクエストやイシューの報告を歓迎します。