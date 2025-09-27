# Deployment Guide

このガイドでは、Lark to Discord BotをRailwayにデプロイする方法を説明します。

## 前提条件

- GitHubアカウント
- Railwayアカウント（[railway.app](https://railway.app)で作成）
- 必要なAPI キー（Lark、Discord）

## Railway デプロイメント手順

### 1. Railwayアカウントの作成とGitHub連携

1. [Railway](https://railway.app)にアクセス
2. "Start a New Project"をクリック
3. GitHubアカウントでサインイン
4. GitHubリポジトリへのアクセスを許可

### 2. プロジェクトの作成

1. Railwayダッシュボードで"New Project"をクリック
2. "Deploy from GitHub repo"を選択
3. `SkillFreakEventsLark2DiscordBot`リポジトリを選択
4. "Deploy Now"をクリック

### 3. 環境変数の設定

Railwayプロジェクトの設定で以下の環境変数を設定してください：

#### 必須環境変数

```bash
# Lark (Feishu) Configuration
LARK_APP_ID=your_lark_app_id_here
LARK_APP_SECRET=your_lark_app_secret_here
LARK_BASE_TOKEN=your_lark_base_token_here
LARK_TABLE_ID=your_lark_table_id_here

# Discord Configuration
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_GUILD_ID=your_discord_guild_id_here
DISCORD_NOTIFICATION_CHANNEL_ID=your_notification_channel_id_here
DISCORD_ARCHIVE_FORUM_ID=your_archive_forum_id_here
```

#### オプション環境変数

```bash
# Schedule Configuration (Cron format)
NOTIFICATION_SCHEDULE=0 9 * * *  # 毎日9:00に通知
ARCHIVE_SCHEDULE=0 22 * * *      # 毎日22:00にアーカイブ

# Logging Configuration
LOG_LEVEL=INFO

# Timezone
TIMEZONE=Asia/Tokyo

# API Configuration
API_TIMEOUT=30
MAX_RETRIES=3
RETRY_DELAY=1
```

### 4. デプロイメント設定の確認

プロジェクトには以下のファイルが含まれており、自動的にRailwayで認識されます：

- `railway.json` - Railway固有の設定
- `Procfile` - プロセス起動設定
- `Dockerfile` - コンテナ設定
- `requirements.txt` - Python依存関係

### 5. デプロイメントの実行

1. 環境変数設定後、Railwayが自動的にデプロイを開始
2. ビルドログを確認してエラーがないことを確認
3. デプロイ完了後、ヘルスチェックエンドポイント（`/health`）で動作確認

### 6. Webhook URLの設定

1. Railwayでデプロイされたアプリケーションのドメインを確認
2. Larkアプリケーションの設定で以下のWebhook URLを設定：
   ```
   https://your-app-name.railway.app/webhook/lark/event
   ```

## 自動デプロイメントの設定

Railwayは自動的にGitHubリポジトリと連携し、`main`ブランチへのプッシュ時に自動デプロイを実行します。

### ブランチ保護の設定（推奨）

1. GitHubリポジトリの設定で"Branches"を選択
2. `main`ブランチの保護ルールを追加
3. "Require pull request reviews before merging"を有効化

## モニタリングとログ

### ログの確認

Railwayダッシュボードの"Logs"タブでアプリケーションのログを確認できます。

### メトリクス監視

Railwayの"Metrics"タブで以下を監視できます：
- CPU使用率
- メモリ使用量
- ネットワークトラフィック
- レスポンス時間

## トラブルシューティング

### よくある問題

1. **環境変数が設定されていない**
   - Railwayの"Variables"タブで全ての必要な環境変数が設定されているか確認

2. **ビルドエラー**
   - `requirements.txt`の依存関係を確認
   - Pythonバージョンの互換性を確認

3. **起動エラー**
   - `railway.json`の`startCommand`が正しいか確認
   - ポート設定（`$PORT`環境変数）が正しいか確認

4. **Webhook接続エラー**
   - Railwayアプリケーションのドメインが正しいか確認
   - Larkアプリケーションの設定でWebhook URLが正しいか確認

### ログレベルの調整

デバッグが必要な場合は、環境変数`LOG_LEVEL`を`DEBUG`に設定してください。

## セキュリティ考慮事項

1. **環境変数の管理**
   - 機密情報は必ずRailwayの環境変数として設定
   - `.env`ファイルはリポジトリにコミットしない

2. **アクセス制御**
   - Railwayプロジェクトへのアクセス権限を適切に管理
   - 必要に応じてチームメンバーを招待

3. **API キーの定期更新**
   - LarkとDiscordのAPIキーを定期的に更新
   - 古いキーは無効化

## スケーリング

Railwayでは使用量に応じて自動的にスケーリングされますが、必要に応じて以下を調整できます：

- メモリ制限
- CPU制限
- インスタンス数

## バックアップとリストア

1. **設定のバックアップ**
   - 環境変数の設定をドキュメント化
   - `railway.json`などの設定ファイルをバージョン管理

2. **データベース（該当する場合）**
   - Railwayのデータベースサービスを使用している場合は定期バックアップを設定

## サポート

問題が発生した場合は、以下を確認してください：

1. Railwayの[ドキュメント](https://docs.railway.app/)
2. プロジェクトのGitHubリポジトリのIssues
3. Railwayのコミュニティフォーラム

---

このガイドに従って、Lark to Discord BotをRailwayに正常にデプロイできるはずです。