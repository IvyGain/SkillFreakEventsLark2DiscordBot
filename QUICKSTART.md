# 🚀 クイックスタートガイド

このガイドは、**プログラミング初心者**の方でも簡単にSkillFreak Events Botを動かせるように作成されています。

## 📋 必要なもの

- **Python 3.8以上** がインストールされたコンピューター
- **インターネット接続**
- **Larkアカウント** (イベントデータが入っているベース)
- **Discordアカウント** (Botを動かすサーバー)

## ⚡ 5分で始める手順

### 1️⃣ プロジェクトの準備

```bash
# ターミナル/コマンドプロンプトを開いて、以下を実行
cd /Users/mashimaro/SkillFreakEventsLark2DiscordBot

# 必要なライブラリをインストール
pip3 install -r requirements.txt
```

### 2️⃣ 設定ファイルの作成

```bash
# .envファイルを作成
cp .env.example .env
```

### 3️⃣ Lark情報の取得

```bash
# Table IDを取得するスクリプトを実行
python3 get_table_info.py
```

**実行すると以下のような情報が表示されます：**
```
テーブル一覧:
1. イベント管理 (tbl1234567890abcdef)
   - フィールド: タイトル, 日付, 時間, 場所
```

**この `tbl1234567890abcdef` の部分をメモしてください！**

### 4️⃣ 環境変数の設定

`.env`ファイルを開いて、以下の値を設定してください：

```env
# Lark設定 (get_table_info.pyの結果を使用)
LARK_APP_ID=cli_xxxxxxxxxx
LARK_APP_SECRET=xxxxxxxxxx
LARK_BASE_TOKEN=xxxxxxxxxx
LARK_TABLE_ID=tbl1234567890abcdef  # ← get_table_info.pyで取得した値

# Discord設定 (Discord Developer Portalで取得)
DISCORD_BOT_TOKEN=xxxxxxxxxx
DISCORD_GUILD_ID=123456789012345678
DISCORD_NOTIFICATION_CHANNEL_ID=123456789012345678
DISCORD_ARCHIVE_FORUM_ID=123456789012345678
```

### 5️⃣ 設定確認

```bash
# 設定が正しいかチェック
python3 check_setup.py
```

**すべて✅が表示されればOK！**

### 6️⃣ Bot起動

```bash
# Botを起動
python3 run.py
```

**「Bot is ready!」と表示されれば成功です！**

## 🆘 困ったときは

### よくあるエラーと解決方法

| エラー | 解決方法 |
|--------|----------|
| `ModuleNotFoundError` | `pip3 install -r requirements.txt` を実行 |
| `Lark認証エラー` | App IDとApp Secretを確認 |
| `Discord接続エラー` | Bot TokenとサーバーIDを確認 |
| `テーブルアクセスエラー` | Table IDとBase Tokenを確認 |

### 詳細な設定方法

詳しい設定方法は **[SETUP_GUIDE.md](./SETUP_GUIDE.md)** を参照してください。

### サポート

- 設定でわからないことがあれば、`check_setup.py`を実行してエラーメッセージを確認
- 各エラーメッセージには解決方法が表示されます

## 🎯 次のステップ

Botが起動したら、Discordサーバーで以下のコマンドを試してみてください：

- `/events` - 今日のイベントを表示
- `/bot-info` - Bot情報を表示
- `/archive-manual` - 手動でアーカイブを作成

## 📱 使い方

1. **毎日自動で通知**: 設定した時間に今日のイベントが自動投稿されます
2. **フォーラムアーカイブ**: 過去のイベントはフォーラムチャンネルに整理されます
3. **手動コマンド**: いつでもコマンドでイベント情報を確認できます

---

**🎉 これでSkillFreak Events Botの設定は完了です！**

何か問題があれば、`check_setup.py`を実行して問題を特定してください。