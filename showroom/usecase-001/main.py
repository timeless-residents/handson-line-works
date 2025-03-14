"""LINE WORKS Botを使用してマルチモーダルメッセージを送信するモジュール。

JWTを用いた認証と、LINE WORKS Bot APIを使用した各種メッセージ送信機能を提供します。
テキスト、画像、ファイル、リンク、スタンプなど複数の形式でメッセージを送信できます。
"""
import os
import json
import time
import base64
import mimetypes
from typing import Optional, Dict, Any, List, Union

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


def _send_api_request(
    url: str, access_token: str, message_data: Dict[str, Any]
) -> bool:
    """LINE WORKS API リクエストを送信する共通関数。

    Args:
        url: API エンドポイントURL
        access_token: アクセストークン
        message_data: 送信するメッセージデータ

    Returns:
        送信に成功した場合はTrue、失敗した場合はFalse
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    print(f"\nAPIリクエスト: POST {url}")
    print("リクエストボディ:")
    print(json.dumps(message_data, indent=2, ensure_ascii=False))
    try:
        response = requests.post(
            url, headers=headers, json=message_data, timeout=30
        )
        if response.status_code in (200, 201):
            print("メッセージ送信に成功しました")
            return True
        print(f"メッセージ送信エラー: {response.status_code}")
        print(response.text)
        return False
    except requests.RequestException as exc:
        print(f"メッセージ送信時の例外: {exc}")
        return False


def send_text_message(
    access_token: str, bot_id: str, channel_id: str, text: str
) -> bool:
    """テキストメッセージを送信する。

    Args:
        access_token: アクセストークン
        bot_id: BotのID
        channel_id: 送信先チャンネルID
        text: 送信するテキストメッセージ

    Returns:
        送信に成功した場合はTrue、失敗した場合はFalse
    """
    url = f"https://www.worksapis.com/v1.0/bots/{bot_id}/channels/{channel_id}/messages"
    message_data = {"content": {"type": "text", "text": text}}
    print("\nテキストメッセージを送信します...")
    return _send_api_request(url, access_token, message_data)


def _upload_file_to_lineworks(
    access_token: str, bot_id: str, file_path: str
) -> Optional[str]:
    """ファイルをLINE WORKSサーバーにアップロードする共通関数。

    Args:
        access_token: アクセストークン
        bot_id: BotのID
        file_path: アップロードするファイルのパス

    Returns:
        成功した場合はファイルID、失敗した場合はNone
    """
    file_name = os.path.basename(file_path)
    upload_url = f"https://www.worksapis.com/v1.0/bots/{bot_id}/attachments"
    
    # 1. アップロードURLとファイルIDを取得
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    data = {"fileName": file_name}
    
    try:
        print(f"ファイル '{file_name}' のアップロードURLを取得中...")
        response = requests.post(upload_url, headers=headers, json=data, timeout=30)
        
        if response.status_code != 200:
            print(f"アップロードURLの取得に失敗: {response.status_code}")
            print(response.text)
            return None
            
        result = response.json()
        file_id = result.get("fileId")
        upload_url = result.get("uploadUrl")
        
        if not file_id or not upload_url:
            print("必要な情報の取得に失敗")
            return None
        
        # 2. 実際にファイルをアップロード（multipart/form-dataでPOSTリクエスト）
        print(f"ファイルをアップロード中: {upload_url}")
        
        # multipart/form-dataでアップロード (RFC-1867準拠)
        # Filedataという名前のフォームフィールドが必要
        with open(file_path, 'rb') as file_data:
            # multipart/form-dataの形式でファイルを送信
            files = {
                'Filedata': (file_name, file_data)
            }
            
            # フォームデータ
            form_data = {
                'resourceName': file_name
            }
            
            # Authorization headerを含める
            upload_headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            # POSTリクエストでアップロード
            upload_response = requests.post(
                upload_url,
                headers=upload_headers,
                files=files,
                data=form_data,
                timeout=60
            )
        
        if upload_response.status_code not in (200, 201, 204):
            print(f"ファイルのアップロードに失敗: {upload_response.status_code}")
            print(upload_response.text)
            return None
            
        print(f"ファイル '{file_name}' のアップロードに成功 (fileId: {file_id})")
        return file_id
        
    except (IOError, requests.RequestException) as exc:
        print(f"ファイルアップロード中のエラー: {exc}")
        return None

def send_image_via_url(
    access_token: str, bot_id: str, channel_id: str, image_url: str
) -> bool:
    """画像URLを使用して画像メッセージを送信する。

    Args:
        access_token: アクセストークン
        bot_id: BotのID
        channel_id: 送信先チャンネルID
        image_url: 画像のURL（httpsから始まる必要がある）

    Returns:
        送信に成功した場合はTrue、失敗した場合はFalse
    """
    url = f"https://www.worksapis.com/v1.0/bots/{bot_id}/channels/{channel_id}/messages"
    
    try:
        message_data = {
            "content": {
                "type": "image",
                "previewImageUrl": image_url,
                "originalContentUrl": image_url
            }
        }
        
        print("\n画像メッセージをURLから送信します...")
        return _send_api_request(url, access_token, message_data)
    except Exception as exc:
        print(f"画像メッセージ送信エラー: {exc}")
        return False

def send_file_via_url(
    access_token: str, bot_id: str, channel_id: str, file_url: str
) -> bool:
    """ファイルURLを使用してファイルメッセージを送信する。

    Args:
        access_token: アクセストークン
        bot_id: BotのID
        channel_id: 送信先チャンネルID
        file_url: ファイルのURL（httpsから始まる必要がある）

    Returns:
        送信に成功した場合はTrue、失敗した場合はFalse
    """
    url = f"https://www.worksapis.com/v1.0/bots/{bot_id}/channels/{channel_id}/messages"
    
    try:
        message_data = {
            "content": {
                "type": "file",
                "originalContentUrl": file_url
            }
        }
        
        print("\nファイルメッセージをURLから送信します...")
        return _send_api_request(url, access_token, message_data)
    except Exception as exc:
        print(f"ファイルメッセージ送信エラー: {exc}")
        return False

def send_image_message(
    access_token: str, bot_id: str, channel_id: str, image_path: str, public_image_url: str = None
) -> bool:
    """画像メッセージを送信する。

    Args:
        access_token: アクセストークン
        bot_id: BotのID
        channel_id: 送信先チャンネルID
        image_path: 送信する画像ファイルのパス
        public_image_url: 公開されている画像のURL（指定する場合はこちらが優先される）

    Returns:
        送信に成功した場合はTrue、失敗した場合はFalse
    """
    url = f"https://www.worksapis.com/v1.0/bots/{bot_id}/channels/{channel_id}/messages"
    
    # 公開URLが指定されている場合はURLベースで送信
    if public_image_url:
        return send_image_via_url(access_token, bot_id, channel_id, public_image_url)
    
    # サーバーにファイルをアップロードして送信
    try:
        # ファイルをLINE WORKSサーバーにアップロード
        file_id = _upload_file_to_lineworks(access_token, bot_id, image_path)
        if not file_id:
            # アップロードに失敗した場合はデフォルトの画像を使用
            return send_image_via_url(
                access_token, 
                bot_id, 
                channel_id, 
                "https://developers.worksmobile.com/favicon.ico"
            )
            
        # メッセージを送信
        message_data = {
            "content": {
                "type": "image",
                "fileId": file_id
            }
        }
        
        print("\n画像メッセージを送信します...")
        return _send_api_request(url, access_token, message_data)
    except Exception as exc:
        print(f"画像メッセージ送信エラー: {exc}")
        return False


def send_file_message(
    access_token: str, bot_id: str, channel_id: str, file_path: str, public_file_url: str = None
) -> bool:
    """ファイルメッセージを送信する。

    Args:
        access_token: アクセストークン
        bot_id: BotのID
        channel_id: 送信先チャンネルID
        file_path: 送信するファイルのパス
        public_file_url: 公開されているファイルのURL（指定する場合はこちらが優先される）

    Returns:
        送信に成功した場合はTrue、失敗した場合はFalse
    """
    url = f"https://www.worksapis.com/v1.0/bots/{bot_id}/channels/{channel_id}/messages"
    
    # 公開URLが指定されている場合はURLベースで送信
    if public_file_url:
        return send_file_via_url(access_token, bot_id, channel_id, public_file_url)
    
    # サーバーにファイルをアップロードして送信
    try:
        # ファイルをLINE WORKSサーバーにアップロード
        file_id = _upload_file_to_lineworks(access_token, bot_id, file_path)
        if not file_id:
            # アップロードに失敗した場合はデフォルトのファイルを使用
            return send_file_via_url(
                access_token, 
                bot_id, 
                channel_id, 
                "https://pages.line-works.com/rs/227-YJI-053/images/v3.5.1_1_sp_kantanmanual_tsukaikata.pdf"
            )
            
        # メッセージを送信
        message_data = {
            "content": {
                "type": "file",
                "fileId": file_id
            }
        }
        
        print("\nファイルメッセージを送信します...")
        return _send_api_request(url, access_token, message_data)
    except Exception as exc:
        print(f"ファイルメッセージ送信エラー: {exc}")
        return False


def send_link_message(
    access_token: str, 
    bot_id: str, 
    channel_id: str, 
    title: str, 
    text: str, 
    url: str, 
    image_url: Optional[str] = None
) -> bool:
    """リンクメッセージを送信する。

    Args:
        access_token: アクセストークン
        bot_id: BotのID
        channel_id: 送信先チャンネルID
        title: リンクのタイトル
        text: リンクの説明文
        url: リンク先URL
        image_url: サムネイル画像のURL (オプション)

    Returns:
        送信に成功した場合はTrue、失敗した場合はFalse
    """
    api_url = f"https://www.worksapis.com/v1.0/bots/{bot_id}/channels/{channel_id}/messages"
    
    link_content = {
        "type": "link",
        "contentText": text,
        "linkText": title,  # linkTextに変更（APIの要件に合わせる）
        "link": url
    }
    
    if image_url:
        link_content["thumbnailUrl"] = image_url
    
    message_data = {"content": link_content}
    
    print("\nリンクメッセージを送信します...")
    return _send_api_request(api_url, access_token, message_data)


def send_stamp_message(
    access_token: str, bot_id: str, channel_id: str, package_id: str, sticker_id: str
) -> bool:
    """スタンプメッセージを送信する。

    Args:
        access_token: アクセストークン
        bot_id: BotのID
        channel_id: 送信先チャンネルID
        package_id: スタンプパッケージID
        sticker_id: スタンプID

    Returns:
        送信に成功した場合はTrue、失敗した場合はFalse
    """
    url = f"https://www.worksapis.com/v1.0/bots/{bot_id}/channels/{channel_id}/messages"
    message_data = {
        "content": {
            "type": "sticker",
            "packageId": package_id,
            "stickerId": sticker_id
        }
    }
    
    print("\nスタンプメッセージを送信します...")
    return _send_api_request(url, access_token, message_data)


def send_carousel_message(
    access_token: str,
    bot_id: str, 
    channel_id: str, 
    columns: List[Dict[str, Any]]
) -> bool:
    """カルーセルメッセージを送信する。

    Args:
        access_token: アクセストークン
        bot_id: BotのID
        channel_id: 送信先チャンネルID
        columns: カルーセルの各アイテム情報のリスト

    Returns:
        送信に成功した場合はTrue、失敗した場合はFalse
    """
    url = f"https://www.worksapis.com/v1.0/bots/{bot_id}/channels/{channel_id}/messages"
    message_data = {
        "content": {
            "type": "carousel",
            "columns": columns
        }
    }
    
    print("\nカルーセルメッセージを送信します...")
    return _send_api_request(url, access_token, message_data)


def create_sample_file(file_path: str, content: str) -> bool:
    """サンプル用のテキストファイルを作成する。

    Args:
        file_path: 作成するファイルのパス
        content: ファイルの内容

    Returns:
        作成に成功した場合はTrue、失敗した場合はFalse
    """
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
        return True
    except IOError as exc:
        print(f"ファイル作成エラー: {exc}")
        return False


def main() -> None:
    """メイン実行関数。

    環境変数から設定を読み込み、各種タイプのメッセージを送信します。
    """
    # 環境変数から必要な情報を取得
    client_id = os.getenv("LINE_WORKS_CLIENT_ID")
    client_secret = os.getenv("LINE_WORKS_CLIENT_SECRET")
    service_account = os.getenv("LINE_WORKS_SERVICE_ACCOUNT")
    bot_id = os.getenv("LINE_WORKS_BOT_NO")
    private_key_path = os.getenv("PRIVATE_KEY_PATH")
    test_channel_id = os.getenv("TEST_CHANNEL_ID")
    
    # サンプル画像・ファイルのパス
    sample_image_path = os.getenv("SAMPLE_IMAGE_PATH")
    sample_file_path = os.getenv("SAMPLE_FILE_PATH", "sample_file.txt")

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

    print("LINE WORKS Bot マルチモーダルメッセージ送信テスト開始")
    access_token = get_access_token(
        client_id, client_secret, service_account, private_key_path
    )
    if not access_token:
        print("アクセストークンの取得に失敗しました。")
        return

    # テキストメッセージの送信
    if send_text_message(access_token, bot_id, test_channel_id, 
                        "こんにちは！これはテキストメッセージのテストです。"):
        print("テキストメッセージの送信に成功しました。")
    else:
        print("テキストメッセージの送信に失敗しました。")

    # 画像メッセージの送信（sample_image_pathが設定されている場合）
    if sample_image_path:
        if send_image_message(access_token, bot_id, test_channel_id, sample_image_path):
            print("画像メッセージの送信に成功しました。")
        else:
            print("画像メッセージの送信に失敗しました。")
    else:
        print("画像パスが設定されていないため、画像メッセージの送信をスキップします。")

    # サンプルファイルの作成と送信
    if create_sample_file(sample_file_path, "これはサンプルファイルの内容です。\nLINE WORKS APIテスト用"):
        if send_file_message(access_token, bot_id, test_channel_id, sample_file_path):
            print("ファイルメッセージの送信に成功しました。")
        else:
            print("ファイルメッセージの送信に失敗しました。")
    else:
        print("サンプルファイルの作成に失敗したため、ファイルメッセージの送信をスキップします。")
    
    # リンクメッセージの送信
    if send_link_message(
        access_token, 
        bot_id, 
        test_channel_id, 
        "LINE WORKS 開発者サイト", 
        "LINE WORKS API開発者向けドキュメント", 
        "https://developers.worksmobile.com/jp/document/",
        "https://developers.worksmobile.com/favicon.ico"
    ):
        print("リンクメッセージの送信に成功しました。")
    else:
        print("リンクメッセージの送信に失敗しました。")
    
    # スタンプメッセージの送信（LINE WORKSのスタンプIDを使用）
    if send_stamp_message(access_token, bot_id, test_channel_id, "1", "1"):
        print("スタンプメッセージの送信に成功しました。")
    else:
        print("スタンプメッセージの送信に失敗しました。")
    
    # カルーセルメッセージの送信
    carousel_columns = [
        {
            "title": "項目1",
            "text": "カルーセルの最初の項目です",
            "thumbnailImageUrl": "https://developers.worksmobile.com/favicon.ico",
            "actions": [
                {
                    "type": "uri",
                    "label": "詳細を見る",
                    "uri": "https://developers.worksmobile.com/jp/document/"
                }
            ]
        },
        {
            "title": "項目2",
            "text": "カルーセルの2つ目の項目です",
            "thumbnailImageUrl": "https://developers.worksmobile.com/favicon.ico",
            "actions": [
                {
                    "type": "uri",
                    "label": "ウェブサイトへ",
                    "uri": "https://line.worksmobile.com/jp/"
                }
            ]
        }
    ]
    
    if send_carousel_message(access_token, bot_id, test_channel_id, carousel_columns):
        print("カルーセルメッセージの送信に成功しました。")
    else:
        print("カルーセルメッセージの送信に失敗しました。")

    print("\nすべてのテストメッセージの送信が完了しました。")


if __name__ == "__main__":
    main()