"""LINE WORKS Botを使用してメッセージを送信するモジュール。

JWTを用いた認証と、LINE WORKS Bot APIを使用したメッセージ送信機能を提供します。
"""
import os
import json
import time
from typing import Optional

import jwt
import requests
from dotenv import load_dotenv

# .env ファイルから環境変数を読み込む
load_dotenv()


def _prepare_jwt_payload(client_id: str, service_account: str) -> dict:
    """JWT認証用のペイロードを準備する。

    Args:
        client_id: LINE WORKS APIのクライアントID
        service_account: サービスアカウント

    Returns:
        JWT用のペイロード辞書
    """
    current_time = int(time.time())
    return {
        "iss": client_id,
        "sub": service_account,
        "iat": current_time,
        "exp": current_time + 3600,
    }


def _prepare_token_request_data(
    jwt_token: str, client_id: str, client_secret: str
) -> dict:
    """アクセストークンリクエスト用のデータを準備する。

    Args:
        jwt_token: 生成されたJWTトークン
        client_id: LINE WORKS APIのクライアントID
        client_secret: LINE WORKS APIのクライアントシークレット

    Returns:
        トークンリクエスト用のデータ辞書
    """
    return {
        "assertion": jwt_token,
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "bot.message",  # メッセージ送信に必要なスコープ
    }


def _handle_token_response(response: requests.Response) -> Optional[str]:
    """トークンレスポンスを処理する。

    Args:
        response: APIレスポンス

    Returns:
        取得したアクセストークン。エラー時はNone。
    """
    if response.status_code == 200:
        token_info = response.json()
        access_token = token_info.get("access_token")
        expires_in = token_info.get("expires_in", 0)
        print(f"アクセストークン取得成功: {expires_in}秒間有効")
        return access_token
    print(f"アクセストークン取得エラー: {response.status_code}")
    print(response.text)
    return None


def get_access_token(
    client_id: str, client_secret: str, service_account: str, private_key_path: str
) -> Optional[str]:
    """JWT認証を用いてアクセストークンを取得する。

    Args:
        client_id: LINE WORKS APIのクライアントID
        client_secret: LINE WORKS APIのクライアントシークレット
        service_account: サービスアカウント
        private_key_path: 秘密鍵ファイルのパス

    Returns:
        取得したアクセストークン。エラー時はNone。
    """
    print("JWT認証を用いてアクセストークンを取得中...")
    try:
        with open(private_key_path, "r", encoding="utf-8") as key_file:
            private_key = key_file.read()

        payload = _prepare_jwt_payload(client_id, service_account)
        jwt_token = jwt.encode(payload, private_key, algorithm="RS256")
        print("JWTトークン生成に成功")

        token_data = _prepare_token_request_data(jwt_token, client_id, client_secret)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        auth_url = "https://auth.worksmobile.com/oauth2/v2.0/token"

        print(f"{auth_url} にアクセストークンをリクエスト中...")
        response = requests.post(
            auth_url, data=token_data, headers=headers, timeout=30
        )
        return _handle_token_response(response)
    except (IOError, jwt.PyJWTError, requests.RequestException) as exc:
        print(f"アクセストークン取得時の例外: {exc}")
        return None


def send_message(
    access_token: str, bot_id: str, channel_id: str, text: str
) -> bool:
    """LINE WORKS Bot APIを使用してメッセージを送信する。

    Args:
        access_token: アクセストークン
        bot_id: BotのID
        channel_id: 送信先チャンネルID
        text: 送信するテキストメッセージ

    Returns:
        送信に成功した場合はTrue、失敗した場合はFalse
    """
    url = f"https://www.worksapis.com/v1.0/bots/{bot_id}/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    message_data = {"content": {"type": "text", "text": text}}
    print(f"\nAPIリクエスト: POST {url}")
    print("リクエストボディ:")
    print(json.dumps(message_data, indent=2, ensure_ascii=False))
    try:
        response = requests.post(
            url, headers=headers, json=message_data, timeout=30
        )
        if response.status_code in (200, 201):
            print("メッセージ送信に成功")
            return True
        print(f"メッセージ送信エラー: {response.status_code}")
        print(response.text)
        return False
    except requests.RequestException as exc:
        print(f"メッセージ送信時の例外: {exc}")
        return False


def main() -> None:
    """メイン実行関数。

    環境変数から設定を読み込み、テストメッセージを送信します。
    """
    # 環境変数から必要な情報を取得
    client_id = os.getenv("LINE_WORKS_CLIENT_ID")
    client_secret = os.getenv("LINE_WORKS_CLIENT_SECRET")
    service_account = os.getenv("LINE_WORKS_SERVICE_ACCOUNT")
    bot_id = os.getenv("LINE_WORKS_BOT_NO")
    private_key_path = os.getenv("PRIVATE_KEY_PATH")
    test_channel_id = os.getenv("TEST_CHANNEL_ID")

    if not (
        client_id
        and client_secret
        and service_account
        and bot_id
        and private_key_path
        and test_channel_id
    ):
        print("必要な環境変数が設定されていません。")
        return

    print("LINE WORKS Bot メッセージ送信テスト開始")
    access_token = get_access_token(
        client_id, client_secret, service_account, private_key_path
    )
    if not access_token:
        print("アクセストークンの取得に失敗しました。")
        return

    test_message = "こんにちは！これはテストメッセージです。"
    if send_message(access_token, bot_id, test_channel_id, test_message):
        print("テストメッセージの送信に成功しました。")
    else:
        print("テストメッセージの送信に失敗しました。")


if __name__ == "__main__":
    main()
