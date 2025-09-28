#!/bin/bash

# Railway Environment Variables Setup Script
# このスクリプトは Railway CLI を使って環境変数を設定します

echo "🚂 Railway Environment Variables Setup"
echo "======================================"

# Railway CLI がインストールされているかチェック
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI がインストールされていません"
    echo "📦 インストール方法:"
    echo "   npm install -g @railway/cli"
    echo "   または"
    echo "   curl -fsSL https://railway.app/install.sh | sh"
    exit 1
fi

# ログインチェック
if ! railway whoami &> /dev/null; then
    echo "🔐 Railway にログインしてください:"
    railway login
fi

echo ""
echo "📝 環境変数を設定します..."
echo "⚠️  実際の値を入力してください（プレースホルダーは使用しないでください）"
echo ""

# 環境変数の入力を求める
read -p "🔑 LARK_APP_ID: " LARK_APP_ID
read -p "🔐 LARK_APP_SECRET: " LARK_APP_SECRET
read -p "📊 LARK_TABLE_ID: " LARK_TABLE_ID
read -p "🤖 DISCORD_BOT_TOKEN: " DISCORD_BOT_TOKEN
read -p "🏠 DISCORD_GUILD_ID: " DISCORD_GUILD_ID
read -p "📢 DISCORD_NOTIFICATION_CHANNEL_ID: " DISCORD_NOTIFICATION_CHANNEL_ID

echo ""
echo "🔄 環境変数を設定中..."

# Railway に環境変数を設定
railway variables set LARK_APP_ID="$LARK_APP_ID"
railway variables set LARK_APP_SECRET="$LARK_APP_SECRET"
railway variables set LARK_TABLE_ID="$LARK_TABLE_ID"
railway variables set DISCORD_BOT_TOKEN="$DISCORD_BOT_TOKEN"
railway variables set DISCORD_GUILD_ID="$DISCORD_GUILD_ID"
railway variables set DISCORD_NOTIFICATION_CHANNEL_ID="$DISCORD_NOTIFICATION_CHANNEL_ID"

echo ""
echo "✅ 環境変数の設定が完了しました！"
echo "🔄 Railway が自動的に再デプロイを開始します..."
echo ""
echo "📊 設定された環境変数を確認:"
railway variables

echo ""
echo "🎉 セットアップ完了！"
echo "🌐 アプリケーション URL: https://web-production-e41e2.up.railway.app"