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
        result = handler_sync(request)
        return jsonify(result)
    except Exception as e:
        print(f"Webhook error: {e}")
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