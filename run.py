#!/usr/bin/env python3
"""
Lark to Discord Events Bot Webhook Server for Railway
"""

import os
import sys
from pathlib import Path
from flask import Flask, request, jsonify

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# webhook.pyから関数をインポート
from api.webhook import handler_sync

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Lark webhook endpoint"""
    try:
        import json
        
        # Flaskリクエストから必要なデータを抽出
        class MockRequest:
            def __init__(self, json_string):
                self.body = json_string
                self.method = 'POST'
        
        # JSONデータを取得
        json_data = request.get_json()
        if not json_data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # JSONデータを文字列に変換してMockRequestオブジェクトを作成
        json_string = json.dumps(json_data)
        mock_request = MockRequest(json_string)
        result = handler_sync(mock_request)
        
        # resultが辞書の場合はそのまま返す、そうでなければJSONとしてパース
        if isinstance(result, dict):
            return jsonify(result), result.get('statusCode', 200)
        else:
            return result
    except Exception as e:
        print(f"Webhook error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for Railway"""
    return jsonify({"status": "healthy"}), 200

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        "message": "Lark to Discord Events Bot Webhook Server",
        "endpoints": {
            "webhook": "/webhook (POST)",
            "health": "/health (GET)"
        }
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)