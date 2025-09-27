# 🚀 Lark to Discord Events Bot セットアップガイド

このガイドは、プログラミング初心者の方でも確実にBotを動かせるよう、ステップバイステップで説明しています。

## 📋 事前準備

### 必要なもの
- [ ] パソコン（Windows、Mac、Linux）
- [ ] インターネット接続
- [ ] Larkアカウント（管理者権限）
- [ ] Discordアカウント（サーバー管理権限）

---

## 🔧 STEP 1: Python環境のセットアップ

### 1-1. Pythonのインストール確認
ターミナル（コマンドプロンプト）を開いて以下を実行：

```bash
python3 --version
```

**結果例：** `Python 3.9.0` のような表示が出ればOK

**エラーが出た場合：**
- Mac: `brew install python3` または [Python公式サイト](https://www.python.org/downloads/)からダウンロード
- Windows: [Python公式サイト](https://www.python.org/downloads/)からダウンロード

### 1-2. プロジェクトフォルダに移動
```bash
cd /Users/mashimaro/SkillFreakEventsLark2DiscordBot
```

### 1-3. 必要なライブラリをインストール
```bash
pip3 install -r requirements.txt
```

**成功例：** `Successfully installed discord.py-2.3.2 ...` のような表示

---

## 🔑 STEP 2: Lark（飛書）アプリの設定

### 2-1. Larkアプリの作成

1. **Lark開発者コンソールにアクセス**
   - https://open.larksuite.com/ にアクセス
   - Larkアカウントでログイン

2. **新しいアプリを作成**
   - 「アプリを作成」をクリック
   - アプリ名: `SkillFreak Events Bot`
   - アプリタイプ: `企業自建アプリ`
   - 作成をクリック

3. **アプリ情報を記録**
   - 作成後、以下の情報をメモ帳にコピー：
     - **App ID**: `cli_xxxxxxxxx` の形式
     - **App Secret**: 長い英数字の文字列

### 2-2. アプリ権限の設定

1. **権限管理に移動**
   - 左メニューから「権限管理」をクリック

2. **必要な権限を追加**
   以下の権限を検索して追加：
   - [ ] `bitable:app` - 多維表格の読取り
   - [ ] `bitable:app:readonly` - 多維表格の読み取り専用アクセス

3. **権限を保存**
   - 「保存」ボタンをクリック

### 2-3. Base TokenとTable IDの取得

1. **Larkベースにアクセス**
   - 提供されたURL: https://ivygain-project.jp.larksuite.com/base/SU35bfdM4aa9emsMOZfjIpxdpCf にアクセス

2. **Base Tokenの取得**
   - URLの `base/` の後の部分が Base Token です
   - 例: `SU35bfdM4aa9emsMOZfjIpxdpCf`
   - これをメモ帳にコピー

3. **Table IDの取得**
   - ベース内で使用したいテーブル（表）をクリック
   - ブラウザのURLを確認
   - `table/` の後の部分が Table ID です
   - 例: `tblxxxxxxxxx` の形式
   - これもメモ帳にコピー

### 2-4. アプリをワークスペースに追加

1. **アプリ公開**
   - Lark開発者コンソールで「バージョン管理」→「公開」
   - 社内公開を選択

2. **ワークスペースに追加**
   - Larkアプリ内で作成したアプリを検索
   - ワークスペースに追加

---

## 🤖 STEP 3: Discord Botの設定

### 3-1. Discord Botの作成

1. **Discord Developer Portalにアクセス**
   - https://discord.com/developers/applications にアクセス
   - Discordアカウントでログイン

2. **新しいアプリケーションを作成**
   - 「New Application」をクリック
   - 名前: `SkillFreak Events Bot`
   - 「Create」をクリック

3. **Botを作成**
   - 左メニューから「Bot」をクリック
   - 「Add Bot」をクリック
   - 「Yes, do it!」をクリック

4. **Bot Tokenを取得**
   - 「Token」セクションで「Copy」をクリック
   - **⚠️ 重要**: このトークンは秘密情報です。誰にも教えないでください
   - メモ帳にコピー

### 3-2. Bot権限の設定

1. **OAuth2設定**
   - 左メニューから「OAuth2」→「URL Generator」をクリック

2. **スコープを選択**
   - [ ] `bot`
   - [ ] `applications.commands`

3. **Bot権限を選択**
   - [ ] `Send Messages` - メッセージ送信
   - [ ] `Use Slash Commands` - スラッシュコマンド使用
   - [ ] `Embed Links` - 埋め込みリンク
   - [ ] `Create Public Threads` - パブリックスレッド作成
   - [ ] `Send Messages in Threads` - スレッド内メッセージ送信
   - [ ] `Manage Threads` - スレッド管理

4. **招待URLを生成**
   - 下部に生成されたURLをコピー
   - このURLでBotをサーバーに招待

### 3-3. BotをDiscordサーバーに招待

1. **招待URLにアクセス**
   - 上記で生成したURLをブラウザで開く

2. **サーバーを選択**
   - Botを追加したいサーバーを選択
   - 「認証」をクリック

3. **権限を確認**
   - 必要な権限にチェックが入っていることを確認
   - 「認証」をクリック

### 3-4. Discord IDの取得

1. **開発者モードを有効化**
   - Discordで「設定」→「詳細設定」→「開発者モード」をON

2. **サーバーIDを取得**
   - サーバー名を右クリック→「IDをコピー」
   - メモ帳にコピー

3. **チャンネルIDを取得**
   - 通知を送りたいチャンネルを右クリック→「IDをコピー」
   - メモ帳にコピー

4. **フォーラムチャンネルIDを取得**
   - アーカイブ用フォーラムチャンネルを右クリック→「IDをコピー」
   - メモ帳にコピー

---

## ⚙️ STEP 4: 環境変数の設定

### 4-1. 環境変数ファイルの作成

1. **テンプレートファイルをコピー**
   ```bash
   cp .env.example .env
   ```

2. **環境変数ファイルを編集**
   - テキストエディタで `.env` ファイルを開く
   - 以下の値を先ほどメモした情報に置き換え

### 4-2. 環境変数の設定内容

```env
# Lark設定
LARK_APP_ID=cli_xxxxxxxxx                    # Step 2-1で取得
LARK_APP_SECRET=xxxxxxxxxxxxxxxx             # Step 2-1で取得  
LARK_BASE_TOKEN=SU35bfdM4aa9emsMOZfjIpxdpCf  # Step 2-3で取得
LARK_TABLE_ID=tblxxxxxxxxx                   # Step 2-3で取得

# Discord設定
DISCORD_BOT_TOKEN=xxxxxxxxxxxxxxxx           # Step 3-1で取得
DISCORD_GUILD_ID=123456789012345678          # Step 3-4で取得
DISCORD_NOTIFICATION_CHANNEL_ID=123456789012345679  # Step 3-4で取得
DISCORD_ARCHIVE_FORUM_ID=123456789012345680  # Step 3-4で取得

# スケジュール設定（そのまま使用）
DAILY_NOTIFICATION_CRON=0 9 * * *
ARCHIVE_CRON=0 18 * * *

# その他設定（そのまま使用）
LOG_LEVEL=INFO
TIMEZONE=Asia/Tokyo
API_TIMEOUT=30
API_RETRY_COUNT=3
```

### 4-3. 設定値の確認

**必須項目チェックリスト:**
- [ ] LARK_APP_ID が `cli_` で始まっている
- [ ] LARK_APP_SECRET が設定されている
- [ ] LARK_BASE_TOKEN が設定されている
- [ ] LARK_TABLE_ID が `tbl` で始まっている
- [ ] DISCORD_BOT_TOKEN が設定されている
- [ ] DISCORD_GUILD_ID が数字のみ
- [ ] DISCORD_NOTIFICATION_CHANNEL_ID が数字のみ
- [ ] DISCORD_ARCHIVE_FORUM_ID が数字のみ

---

## 🚀 STEP 5: Botの実行

### 5-1. 初回実行テスト

```bash
python3 run.py
```

**成功例:**
```
[INFO] Bot starting...
[INFO] Lark client initialized
[INFO] Discord bot logged in as: SkillFreak Events Bot#1234
[INFO] Scheduler started
[INFO] Bot is ready!
```

**エラーが出た場合:**
- 環境変数の設定を再確認
- インターネット接続を確認
- Bot権限を再確認

### 5-2. 動作確認

1. **Discordでコマンドテスト**
   - 設定したチャンネルで `/events` と入力
   - Botが応答すれば成功

2. **手動アーカイブテスト**
   - `/archive-manual` コマンドを実行
   - フォーラムにスレッドが作成されれば成功

### 5-3. 自動実行の確認

- **毎日9時**: 本日のイベント通知
- **毎日18時**: 過去イベントのアーカイブ

---

## 🔧 STEP 6: トラブルシューティング

### よくあるエラーと解決方法

#### エラー1: `ModuleNotFoundError`
**原因**: 必要なライブラリがインストールされていない
**解決**: `pip3 install -r requirements.txt` を再実行

#### エラー2: `discord.errors.LoginFailure`
**原因**: Discord Bot Tokenが間違っている
**解決**: `.env` ファイルの `DISCORD_BOT_TOKEN` を確認

#### エラー3: `Lark API authentication failed`
**原因**: Lark App IDまたはApp Secretが間違っている
**解決**: `.env` ファイルの Lark設定を確認

#### エラー4: `Table not found`
**原因**: Table IDが間違っているか、アプリに権限がない
**解決**: 
1. Table IDを再確認
2. Larkアプリの権限設定を確認
3. アプリがワークスペースに追加されているか確認

### ログの確認方法

```bash
# ログファイルの確認
tail -f logs/bot.log

# エラーログの確認
grep ERROR logs/bot.log
```

---

## 📞 サポート

### 設定確認コマンド

```bash
# 環境変数の確認
python3 -c "from src.config.settings import Settings; print('設定読み込み成功')"

# Lark接続テスト
python3 -c "
import asyncio
from src.lark.client import LarkClient
from src.config.settings import Settings

async def test():
    settings = Settings()
    client = LarkClient(settings)
    try:
        records = await client.get_today_events()
        print(f'Lark接続成功: {len(records)}件のイベント取得')
    except Exception as e:
        print(f'Lark接続エラー: {e}')

asyncio.run(test())
"
```

### 次のステップ

Botが正常に動作したら：
1. スケジュール時刻の調整（`.env` ファイル）
2. 通知メッセージのカスタマイズ
3. 追加機能の実装

---

**🎉 セットアップ完了！**

このガイドに従って設定すれば、SkillFreak Events Botが正常に動作するはずです。何か問題が発生した場合は、エラーメッセージとともにお知らせください。