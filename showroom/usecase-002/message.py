"""LINE WORKS Bot APIを使用したインタラクティブメッセージ送信モジュール。

ボタンテンプレート、リストテンプレート、クイックリプライなどの
インタラクティブなメッセージを送信するための関数を提供します。
"""
import json
from typing import Dict, Any, List, Optional
import requests


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


def send_button_template(
    access_token: str, 
    bot_id: str, 
    channel_id: str, 
    content_text: str, 
    actions: List[Dict[str, Any]]
) -> bool:
    """ボタンテンプレートメッセージを送信する。

    Args:
        access_token: アクセストークン
        bot_id: BotのID
        channel_id: 送信先チャンネルID
        content_text: ボタンテンプレートの本文テキスト
        actions: ボタンのアクション定義リスト（最大10個）

    Returns:
        送信に成功した場合はTrue、失敗した場合はFalse
    """
    url = f"https://www.worksapis.com/v1.0/bots/{bot_id}/channels/{channel_id}/messages"
    
    message_data = {
        "content": {
            "type": "button_template",
            "contentText": content_text,
            "actions": actions
        }
    }
    
    print("\nボタンテンプレートメッセージを送信します...")
    return _send_api_request(url, access_token, message_data)


def send_list_template(
    access_token: str,
    bot_id: str,
    channel_id: str,
    background_image_url: Optional[str] = None,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    elements: List[Dict[str, Any]] = None,
    actions: Optional[List[List[Dict[str, Any]]]] = None
) -> bool:
    """リストテンプレートメッセージを送信する。

    Args:
        access_token: アクセストークン
        bot_id: BotのID
        channel_id: 送信先チャンネルID
        background_image_url: カバーデータ背景画像のURL (オプション)
        title: カバーデータのタイトル (オプション)
        subtitle: カバーデータのサブタイトル (オプション)
        elements: リストの要素（最大4個）
        actions: 下部のボタンアクション（最大2列、2行まで）

    Returns:
        送信に成功した場合はTrue、失敗した場合はFalse
    """
    url = f"https://www.worksapis.com/v1.0/bots/{bot_id}/channels/{channel_id}/messages"
    
    # 必須のコンポーネントを定義
    message_data = {
        "content": {
            "type": "list_template",
            "elements": elements or []
        }
    }
    
    # オプションのカバーデータを設定
    cover_data = {}
    
    if background_image_url:
        cover_data["backgroundImageUrl"] = background_image_url
        
    if title:
        cover_data["title"] = title
        
    if subtitle:
        cover_data["subtitle"] = subtitle
    
    # カバーデータが定義されていれば追加
    if cover_data:
        message_data["content"]["coverData"] = cover_data
    
    # 下部ボタンが定義されていれば追加
    if actions:
        message_data["content"]["actions"] = actions
    
    print("\nリストテンプレートメッセージを送信します...")
    return _send_api_request(url, access_token, message_data)


def send_message_with_quick_reply(
    access_token: str,
    bot_id: str,
    channel_id: str,
    text: str,
    quick_reply_items: List[Dict[str, Any]]
) -> bool:
    """クイックリプライ付きメッセージを送信する。

    Args:
        access_token: アクセストークン
        bot_id: BotのID
        channel_id: 送信先チャンネルID
        text: メッセージテキスト
        quick_reply_items: クイックリプライアイテムのリスト（最大13個）

    Returns:
        送信に成功した場合はTrue、失敗した場合はFalse
    """
    url = f"https://www.worksapis.com/v1.0/bots/{bot_id}/channels/{channel_id}/messages"
    
    message_data = {
        "content": {
            "type": "text",
            "text": text,
            "quickReply": {
                "items": quick_reply_items
            }
        }
    }
    
    print("\nクイックリプライ付きメッセージを送信します...")
    return _send_api_request(url, access_token, message_data)