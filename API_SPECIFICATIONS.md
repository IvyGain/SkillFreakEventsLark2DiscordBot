# API仕様書 - Lark to Discord Events Bot

## Lark API 仕様

### 認証方式
- **App Token**: `Bearer {app_access_token}`
- **取得方法**: App ID + App Secret でトークン取得

### 必要なAPI エンドポイント

#### 1. App Access Token 取得
```
POST https://open.larksuite.com/open-apis/auth/v3/app_access_token/internal
Content-Type: application/json

{
    "app_id": "your_app_id",
    "app_secret": "your_app_secret"
}
```

#### 2. ベーステーブル レコード取得
```
GET https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records
Authorization: Bearer {app_access_token}

Query Parameters:
- page_size: 500 (最大値)
- page_token: ページネーション用
- filter: 日付フィルター用
- sort: ソート条件
```

### Lark データモデル例
```json
{
    "code": 0,
    "msg": "success",
    "data": {
        "items": [
            {
                "record_id": "recXXXXXX",
                "fields": {
                    "イベント名": "技術勉強会",
                    "開催日": 1640995200000,
                    "開始時間": "19:00",
                    "終了時間": "21:00",
                    "場所": "オンライン",
                    "説明": "Pythonの基礎について学びます",
                    "参加者数": 25,
                    "ステータス": "開催予定"
                }
            }
        ],
        "has_more": false,
        "page_token": "",
        "total": 1
    }
}
```

## Discord API 仕様

### 認証方式
- **Bot Token**: `Bot {bot_token}`

### 必要なAPI エンドポイント

#### 1. チャンネルにメッセージ送信
```
POST https://discord.com/api/v10/channels/{channel_id}/messages
Authorization: Bot {bot_token}
Content-Type: application/json

{
    "content": "メッセージ内容",
    "embeds": [
        {
            "title": "イベントタイトル",
            "description": "イベント説明",
            "color": 3447003,
            "fields": [
                {
                    "name": "開催日時",
                    "value": "2024-01-15 19:00-21:00",
                    "inline": true
                }
            ]
        }
    ]
}
```

#### 2. フォーラムチャンネルにスレッド作成
```
POST https://discord.com/api/v10/channels/{forum_channel_id}/threads
Authorization: Bot {bot_token}
Content-Type: application/json

{
    "name": "イベント名 - 2024/01/15",
    "message": {
        "content": "アーカイブ内容",
        "embeds": [...]
    },
    "applied_tags": ["tag_id_1", "tag_id_2"]
}
```

#### 3. フォーラムチャンネル情報取得
```
GET https://discord.com/api/v10/channels/{forum_channel_id}
Authorization: Bot {bot_token}
```

## 機能要件詳細

### 1. 本日のイベント告知機能

#### 処理フロー
1. **データ取得**
   - Larkベーステーブルから本日の日付でフィルタリング
   - ステータスが「開催予定」のイベントのみ取得

2. **データ変換**
   - Larkの日付フィールド（Unix timestamp）を日本時間に変換
   - イベント情報をDiscord Embed形式に整形

3. **Discord投稿**
   - 指定されたチャンネルにEmbed形式で投稿
   - 複数イベントがある場合は1つのメッセージにまとめる

#### メッセージフォーマット例
```
🎉 **本日のイベント情報** 🎉

📅 **技術勉強会**
🕐 時間: 19:00 - 21:00
📍 場所: オンライン
👥 参加者: 25名
📝 説明: Pythonの基礎について学びます

📅 **ネットワーキング**
🕐 時間: 20:00 - 22:00
📍 場所: 渋谷オフィス
👥 参加者: 15名
📝 説明: 業界の最新トレンドについて議論
```

### 2. アーカイブフォーラム機能

#### 処理フロー
1. **過去イベント検索**
   - 前日または指定期間の終了したイベントを取得
   - ステータスが「終了」のイベントを対象

2. **スレッド作成**
   - フォーラムチャンネルに新しいスレッドを作成
   - スレッド名: 「{イベント名} - {開催日}」

3. **詳細投稿**
   - イベントの詳細情報をスレッドに投稿
   - 参加者数、フィードバック等も含める

#### スレッド投稿フォーマット例
```
📋 **イベントアーカイブ**

**基本情報**
• イベント名: 技術勉強会
• 開催日: 2024年1月15日
• 時間: 19:00 - 21:00
• 場所: オンライン

**結果**
• 参加者数: 25名
• ステータス: 終了

**詳細**
Pythonの基礎について学ぶ勉強会を開催しました。
初心者から中級者まで幅広い参加者に好評でした。
```

## エラーハンドリング仕様

### Lark API エラー
- **401 Unauthorized**: トークン再取得
- **403 Forbidden**: 権限不足エラーログ
- **429 Too Many Requests**: 指数バックオフでリトライ
- **500 Internal Server Error**: 3回リトライ後エラー報告

### Discord API エラー
- **401 Unauthorized**: Bot Token確認
- **403 Forbidden**: 権限不足エラーログ
- **429 Too Many Requests**: Rate Limit遵守
- **404 Not Found**: チャンネルID確認

## レート制限対応

### Lark API
- **制限**: 100 requests/minute
- **対応**: リクエスト間隔を600ms以上空ける

### Discord API
- **制限**: 50 requests/second (グローバル)
- **対応**: discord.py の内蔵レート制限機能を使用

## データ変換仕様

### 日付・時刻変換
```python
# Lark timestamp (Unix) → 日本時間
import datetime
import pytz

def convert_lark_timestamp(timestamp):
    dt = datetime.datetime.fromtimestamp(timestamp / 1000)
    jst = pytz.timezone('Asia/Tokyo')
    return dt.replace(tzinfo=pytz.UTC).astimezone(jst)
```

### フィールドマッピング
```python
LARK_FIELD_MAPPING = {
    'event_name': 'イベント名',
    'event_date': '開催日',
    'start_time': '開始時間',
    'end_time': '終了時間',
    'location': '場所',
    'description': '説明',
    'participants': '参加者数',
    'status': 'ステータス'
}
```

## セキュリティ仕様

### 機密情報管理
- 全ての API キーは環境変数で管理
- ログに機密情報を出力しない
- トークンの定期ローテーション対応

### 入力値検証
- Larkから取得したデータの型チェック
- Discord投稿前の文字数制限チェック
- 不正な文字のエスケープ処理