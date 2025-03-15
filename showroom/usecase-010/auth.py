"""LINE WORKS Bot API認証モジュール。

JWTを用いた認証と、アクセストークンの取得を行います。
"""
import time
import jwt
import requests
from typing import Optional, Dict, Any


def prepare_jwt_payload(client_id: str, service_account: str) -> dict:
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


def prepare_token_request_data(
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


def handle_token_response(response: requests.Response) -> Optional[str]:
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

        payload = prepare_jwt_payload(client_id, service_account)
        jwt_token = jwt.encode(payload, private_key, algorithm="RS256")
        print("JWTトークン生成に成功")

        token_data = prepare_token_request_data(jwt_token, client_id, client_secret)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        auth_url = "https://auth.worksmobile.com/oauth2/v2.0/token"

        print(f"{auth_url} にアクセストークンをリクエスト中...")
        response = requests.post(
            auth_url, data=token_data, headers=headers, timeout=30
        )
        return handle_token_response(response)
    except (IOError, jwt.PyJWTError, requests.RequestException) as exc:
        print(f"アクセストークン取得時の例外: {exc}")
        return None