"""LINE WORKS Bot API Webhookサーバー。

Flask Webフレームワークを使用して、LINE WORKS BotのWebhookを処理します。
ngrokを使用してローカルサーバーを公開します。
"""
import os
import json
import requests
import subprocess
import threading
import time
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from auth import get_access_token
from callback_handler import CallbackHandler, create_webhook_response

# .env ファイルから環境変数を読み込む
load_dotenv()

app = Flask(__name__)

# グローバル変数
bot_id = os.getenv("LINE_WORKS_BOT_NO")
callback_handler = None
access_token = None

# favicon.ico リクエストに対応するルート
@app.route('/favicon.ico')
def favicon():
    """フロントエンドはちゃんとした提供できないので空のレスポンスを返す"""
    return "", 204


def get_ngrok_url() -> Optional[str]:
    """ngrokが公開しているURLを取得する。
    
    Returns:
        ngrokのパブリックURL。取得できない場合はNone。
    """
    try:
        # ngrokのAPIを呼び出して公開URLを取得
        response = requests.get("http://localhost:4040/api/tunnels")
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get("tunnels", [])
            for tunnel in tunnels:
                if tunnel.get("proto") == "https":
                    return tunnel.get("public_url")
        
        print("ngrokのURLを取得できませんでした。ngrokが起動しているか確認してください。")
        return None
    except Exception as e:
        print(f"ngrokのURL取得中にエラーが発生しました: {e}")
        return None


def start_ngrok(port: int = 5000) -> None:
    """ngrokを起動する。
    
    Args:
        port: 公開するローカルポート番号
    """
    try:
        # ngrokが既に起動しているか確認
        try:
            requests.get("http://localhost:4040/api/tunnels", timeout=1)
            print("ngrokは既に起動しています。")
            return
        except requests.RequestException:
            # ngrokが起動していない場合は起動
            print(f"ngrokを起動しています（ポート {port}）...")
    
        # バックグラウンドでngrokを起動
        subprocess.Popen(
            ["ngrok", "http", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # ngrokが起動するまで少し待機
        time.sleep(3)
        
        # 公開URLを取得して表示
        ngrok_url = get_ngrok_url()
        if ngrok_url:
            print(f"ngrokが起動しました。公開URL: {ngrok_url}")
            print(f"このURLをLINE WORKS Developer ConsoleのBot WebhookURLに設定してください。")
            print(f"フルパス: {ngrok_url}/webhook")
            
            # .envファイルにURLを保存
            update_env_file(ngrok_url)
        else:
            print("ngrokの起動は成功しましたが、公開URLを取得できませんでした。")
    except Exception as e:
        print(f"ngrokの起動中にエラーが発生しました: {e}")


def update_env_file(ngrok_url: str) -> None:
    """環境変数ファイルにngrokのURLを保存する。
    
    Args:
        ngrok_url: ngrokの公開URL
    """
    try:
        env_file_path = ".env"
        
        # 既存の.envファイルを読み込む
        if os.path.exists(env_file_path):
            with open(env_file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        else:
            lines = []
        
        # CALLBACK_URLの行があるか確認
        callback_url_exists = False
        for i, line in enumerate(lines):
            if line.startswith("CALLBACK_URL="):
                lines[i] = f"CALLBACK_URL={ngrok_url}/webhook\n"
                callback_url_exists = True
                break
        
        # なければ追加
        if not callback_url_exists:
            lines.append(f"CALLBACK_URL={ngrok_url}/webhook\n")
        
        # ファイルに書き戻す
        with open(env_file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        
        print(f".envファイルにCALLBACK_URL={ngrok_url}/webhookを保存しました。")
    except Exception as e:
        print(f".envファイルの更新中にエラーが発生しました: {e}")


def initialize_bot() -> None:
    """Botの初期化を行う。
    
    アクセストークンの取得とコールバックハンドラーの初期化を行います。
    """
    global callback_handler, access_token
    
    client_id = os.getenv("LINE_WORKS_CLIENT_ID")
    client_secret = os.getenv("LINE_WORKS_CLIENT_SECRET")
    service_account = os.getenv("LINE_WORKS_SERVICE_ACCOUNT")
    private_key_path = os.getenv("PRIVATE_KEY_PATH")
    
    if not (client_id and client_secret and service_account and bot_id and private_key_path):
        print("必要な環境変数が設定されていません。")
        return
    
    # アクセストークンを取得
    access_token = get_access_token(
        client_id, client_secret, service_account, private_key_path
    )
    if not access_token:
        print("アクセストークンの取得に失敗しました。")
        return
    
    # コールバックハンドラーの初期化
    callback_handler = CallbackHandler(bot_id)
    
    print("Botの初期化が完了しました。")


@app.route('/webhook', methods=['POST', 'GET', 'HEAD'])
def webhook():
    """LINE WORKS Botのwebhookエンドポイント。
    
    Returns:
        応答データのJSONレスポンス
    """
    # HEAD, GETリクエストの場合はシンプルな応答を返す
    if request.method in ['HEAD', 'GET']:
        return jsonify({"status": "success", "message": "Webhook endpoint is working"}), 200
    global callback_handler, access_token
    
    # リクエストボディを取得
    try:
        payload = request.json
        print("Webhookリクエストを受信しました:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        
        # コールバックハンドラーが初期化されているか確認
        if not callback_handler or not access_token:
            print("コールバックハンドラーまたはアクセストークンが初期化されていません。")
            return jsonify({"status": "error", "message": "Bot not initialized"}), 500
        
        # コールバックを処理して応答を生成
        response_data = callback_handler.handle_callback(payload)
        if response_data:
            # 応答先のチャンネルIDを取得
            channel_id = payload.get("source", {}).get("channelId")
            # チャンネルIDがない場合はユーザーIDを取得
            user_id = payload.get("source", {}).get("userId")
            
            if channel_id:
                # チャンネルへメッセージを送信するAPIエンドポイント
                url = f"https://www.worksapis.com/v1.0/bots/{bot_id}/channels/{channel_id}/messages"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                }
                
                # 応答メッセージを送信
                print("チャンネルに応答メッセージを送信します:")
                print(json.dumps(response_data, indent=2, ensure_ascii=False))
                
                response = requests.post(url, headers=headers, json=response_data, timeout=30)
                if response.status_code in (200, 201):
                    print("応答メッセージの送信に成功しました。")
                else:
                    print(f"応答メッセージの送信に失敗しました: {response.status_code}")
                    print(response.text)
            elif user_id:
                # ユーザーIDが存在する場合は、ユーザーに直接メッセージを送信
                url = f"https://www.worksapis.com/v1.0/bots/{bot_id}/users/{user_id}/messages"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                }
                
                # 応答メッセージを送信
                print("ユーザーに応答メッセージを送信します:")
                print(json.dumps(response_data, indent=2, ensure_ascii=False))
                
                response = requests.post(url, headers=headers, json=response_data, timeout=30)
                if response.status_code in (200, 201):
                    print("ユーザーへの応答メッセージの送信に成功しました。")
                else:
                    print(f"ユーザーへの応答メッセージの送信に失敗しました: {response.status_code}")
                    print(response.text)
            else:
                print("チャンネルIDもユーザーIDも取得できませんでした。応答を送信できません。")
        
        # LINE WORKSのWebhookは常に成功レスポンスを返す必要がある
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Webhook処理中にエラーが発生しました: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/', methods=['GET', 'POST'])
def home():
    """ホームエンドポイント。
    
    サーバーが稼働していることを確認するためのシンプルなエンドポイント。
    
    Returns:
        シンプルなテキストレスポンス
    """
    # POSTリクエストの場合はwebhookエンドポイントと同じように処理する
    if request.method == 'POST':
        # webhookメソッドをリダイレクトすることで同じコードで処理
        return webhook()
    ngrok_url = get_ngrok_url()
    webhook_url = f"{ngrok_url}/webhook" if ngrok_url else "Unknown"
    
    return f"""
    <html>
    <head>
        <title>LINE WORKS Bot Webhook Server</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
            h1 {{ color: #333; }}
            .info {{ background-color: #f5f5f5; padding: 20px; border-radius: 5px; }}
            pre {{ background-color: #eee; padding: 10px; border-radius: 3px; }}
        </style>
    </head>
    <body>
        <h1>LINE WORKS Bot Webhook Server</h1>
        <div class="info">
            <h2>サーバー情報</h2>
            <p>Webhookサーバーが正常に動作しています。</p>
            <p><strong>Webhook URL:</strong> <pre>{webhook_url}</pre></p>
            <p>LINE WORKS Developer ConsoleでこのURLをBot設定のWebhook URLに登録してください。</p>
            <p>コンソールに詳細なログが出力されています。</p>
        </div>
    </body>
    </html>
    """


def main():
    """メイン関数。
    
    Webhookサーバーの実行を行います。
    注: ngrokは別のターミナルで手動で起動してください。
    """
    # ngrokは手動で起動するためコメントアウト
    # threading.Thread(target=start_ngrok, args=(5000,)).start()
    
    # 手動で起動したngrokのURLを入力
    ngrok_url = input("手動で起動したngrokのURLを入力してください (例: https://xxxx-xxxx-xxxx.ngrok-free.app): ")
    if ngrok_url:
        print(f"入力されたngrokのURL: {ngrok_url}")
        print(f"Webhook URL: {ngrok_url}/webhook")
        # .envファイルを更新
        update_env_file(ngrok_url)
    
    # Botの初期化
    initialize_bot()
    
    # Flaskサーバーを起動
    app.run(debug=True, host="0.0.0.0", port=5000)


if __name__ == '__main__':
    main()