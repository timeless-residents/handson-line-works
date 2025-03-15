"""LINE WORKS Bot API Webhookサーバー。

Flask Webフレームワークを使用して、LINE WORKS BotのWebhookを処理します。
GPT-4とRAGを活用して、社内規定に関する質問に回答します。
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
from gpt_client import GPTClient
from message_handler import MessageHandler
from vector_store import load_or_create_vector_store
from rag_engine import RAGEngine

# .env ファイルから環境変数を読み込む
load_dotenv()

app = Flask(__name__)

# グローバル変数
bot_id = os.getenv("LINE_WORKS_BOT_NO")
message_handler = None
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


def check_vector_store() -> bool:
    """ベクトルストアが存在するか確認する。
    
    Returns:
        ベクトルストアが存在する場合はTrue、そうでない場合はFalse
    """
    vector_db_path = os.getenv("VECTOR_DB_PATH", "./vector_db")
    return os.path.exists(vector_db_path) and os.path.exists(f"{vector_db_path}.faiss")


def initialize_bot() -> None:
    """Botの初期化を行う。
    
    アクセストークンの取得とメッセージハンドラーの初期化を行います。
    """
    global message_handler, access_token
    
    # LINE WORKS API設定
    client_id = os.getenv("LINE_WORKS_CLIENT_ID")
    client_secret = os.getenv("LINE_WORKS_CLIENT_SECRET")
    service_account = os.getenv("LINE_WORKS_SERVICE_ACCOUNT")
    private_key_path = os.getenv("PRIVATE_KEY_PATH")
    
    # OpenAI API設定
    openai_api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("COMPLETION_MODEL", "gpt-4")
    max_tokens = int(os.getenv("MAX_TOKENS", "1024"))
    temperature = float(os.getenv("TEMPERATURE", "0.2"))
    
    # ベクトルストア設定
    vector_db_path = os.getenv("VECTOR_DB_PATH", "./vector_db")
    top_k = int(os.getenv("TOP_K", "5"))
    
    if not (client_id and client_secret and service_account and bot_id and private_key_path):
        print("必要なLINE WORKS API環境変数が設定されていません。")
        return
    
    if not openai_api_key:
        print("必要なOPENAI_API_KEY環境変数が設定されていません。")
        return
    
    # ベクトルストアが存在するか確認
    if not check_vector_store():
        print("ベクトルストアが見つかりません。index_documents.pyを実行してインデックスを作成してください。")
        return
    
    # アクセストークンを取得
    access_token = get_access_token(
        client_id, client_secret, service_account, private_key_path
    )
    if not access_token:
        print("アクセストークンの取得に失敗しました。")
        return
    
    # GPTクライアントを初期化
    gpt_client = GPTClient(
        api_key=openai_api_key,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    
    # ベクトルストアをロード
    vector_store = load_or_create_vector_store(vector_db_path)
    
    # RAGエンジンを初期化
    rag_engine = RAGEngine(
        gpt_client=gpt_client,
        vector_store=vector_store,
        top_k=top_k
    )
    
    # メッセージハンドラーの初期化
    message_handler = MessageHandler(
        bot_id=bot_id,
        access_token=access_token,
        gpt_client=gpt_client,
        rag_engine=rag_engine,
    )
    
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
    
    global message_handler, access_token
    
    # リクエストボディを取得
    try:
        payload = request.json
        print("Webhookリクエストを受信しました:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        
        # メッセージハンドラーが初期化されているか確認
        if not message_handler or not access_token:
            print("メッセージハンドラーまたはアクセストークンが初期化されていません。")
            return jsonify({"status": "error", "message": "Bot not initialized"}), 500
        
        # メッセージを処理して応答を生成
        response_data = message_handler.handle_message(payload)
        if response_data:
            # 応答先のIDを取得（チャンネルIDまたはユーザーID）
            channel_id = payload.get("source", {}).get("channelId")
            user_id = payload.get("source", {}).get("userId")
            
            if channel_id:
                # チャンネルに応答
                success = message_handler.send_message(channel_id, response_data, is_user=False)
                if success:
                    print("チャンネルへの応答メッセージの送信に成功しました。")
                else:
                    print("チャンネルへの応答メッセージの送信に失敗しました。")
            elif user_id:
                # ユーザーに直接応答
                success = message_handler.send_message(user_id, response_data, is_user=True)
                if success:
                    print("ユーザーへの応答メッセージの送信に成功しました。")
                else:
                    print("ユーザーへの応答メッセージの送信に失敗しました。")
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
    
    # ベクトルストアの情報を取得
    vector_store_info = "ベクトルストアが見つかりません。" 
    if check_vector_store():
        try:
            vector_db_path = os.getenv("VECTOR_DB_PATH", "./vector_db")
            vector_store = load_or_create_vector_store(vector_db_path)
            stats = vector_store.get_stats()
            vector_store_info = f"""
            <p>ドキュメント数: {stats['document_count']}</p>
            <p>ドキュメントタイプ: {stats.get('document_types', {})}</p>
            <p>ベクトル次元数: {stats.get('vector_dimension', 'N/A')}</p>
            """
        except Exception as e:
            vector_store_info = f"ベクトルストア情報の取得中にエラーが発生しました: {str(e)}"
    
    return f"""
    <html>
    <head>
        <title>社内規定Q&Aボット</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
            h1 {{ color: #333; }}
            .info {{ background-color: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
            pre {{ background-color: #eee; padding: 10px; border-radius: 3px; }}
            .features {{ margin-top: 20px; }}
            .features h2 {{ margin-bottom: 10px; }}
            .features ul {{ margin-top: 5px; }}
            .rag-info {{ background-color: #e0f7fa; padding: 20px; border-radius: 5px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <h1>社内規定Q&Aボット</h1>
        <div class="info">
            <h2>サーバー情報</h2>
            <p>Webhookサーバーが正常に動作しています。</p>
            <p><strong>Webhook URL:</strong> <pre>{webhook_url}</pre></p>
            <p>LINE WORKS Developer ConsoleでこのURLをBot設定のWebhook URLに登録してください。</p>
            <p>コンソールに詳細なログが出力されています。</p>
        </div>
        
        <div class="rag-info">
            <h2>RAG (検索拡張生成) 情報</h2>
            <p>使用モデル: {os.getenv("COMPLETION_MODEL", "gpt-4")}</p>
            <p>エンベディングモデル: {os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")}</p>
            <div>
                <h3>ベクトルストア状態:</h3>
                {vector_store_info}
            </div>
            <p>設定:
                <ul>
                    <li>最大トークン数: {os.getenv("MAX_TOKENS", "1024")}</li>
                    <li>温度パラメータ: {os.getenv("TEMPERATURE", "0.2")}</li>
                    <li>検索結果数: {os.getenv("TOP_K", "5")}件</li>
                    <li>会話保持ターン数: {os.getenv("MAX_CONVERSATION_TURNS", "10")}</li>
                    <li>会話タイムアウト: {os.getenv("CONVERSATION_TIMEOUT_MINUTES", "60")}分</li>
                </ul>
            </p>
        </div>
        
        <div class="features">
            <h2>実装されている機能</h2>
            <ul>
                <li>社内規定や文書に基づく質問応答</li>
                <li>文脈を考慮した会話</li>
                <li>検索機能（/search または「検索」で始まるメッセージ）</li>
                <li>特殊コマンド（/help, /reset, /feedback）</li>
                <li>回答の出典表示</li>
            </ul>
        </div>
    </body>
    </html>
    """


def main():
    """メイン関数。
    
    Webhookサーバーの実行を行います。
    """
    server_host = os.getenv("SERVER_HOST", "0.0.0.0")
    server_port = int(os.getenv("SERVER_PORT", "5000"))
    debug_mode = os.getenv("DEBUG_MODE", "True").lower() == "true"
    
    # ベクトルストアの確認
    if not check_vector_store():
        print("警告: ベクトルストアが見つかりません。")
        print("index_documents.pyを実行して、文書のインデックスを作成してください。")
        print("例: python index_documents.py")
        print("このままサーバーを起動しますが、質問応答機能は動作しません。")
    
    # ngrok起動オプションを確認
    auto_start_ngrok = os.getenv("AUTO_START_NGROK", "False").lower() == "true"
    if auto_start_ngrok:
        # バックグラウンドでngrokを起動
        threading.Thread(target=start_ngrok, args=(server_port,)).start()
    else:
        # 手動で起動したngrokのURLを入力
        ngrok_url = input("手動で起動したngrokのURLを入力してください (例: https://xxxx-xxxx-xxxx.ngrok-free.app): ")
        if ngrok_url:
            print(f"入力されたngrokのURL: {ngrok_url}")
            print(f"Webhook URL: {ngrok_url}/webhook")
            # .envファイルを更新
            update_env_file(ngrok_url)
    
    # 必要なディレクトリの作成
    os.makedirs("conversations", exist_ok=True)
    os.makedirs("feedback", exist_ok=True)
    
    # Botの初期化
    initialize_bot()
    
    # Flaskサーバーを起動
    print(f"Webhookサーバーを起動します: {server_host}:{server_port}")
    app.run(debug=debug_mode, host=server_host, port=server_port)


if __name__ == '__main__':
    main()