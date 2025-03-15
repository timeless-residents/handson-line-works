"""LINE WORKS Bot APIを使用してインタラクティブなボタン/アクションを実装するメインモジュール。

ボタンテンプレート、リストテンプレート、クイックリプライなどの
インタラクティブなメッセージ送信と、その応答処理の実装例を提供します。
"""
import os
from dotenv import load_dotenv
from auth import get_access_token
from message import (
    send_text_message,
    send_button_template,
    send_list_template,
    send_message_with_quick_reply
)
from callback_handler import CallbackHandler

# .env ファイルから環境変数を読み込む
load_dotenv()


def send_interactive_messages(access_token: str, bot_id: str, channel_id: str) -> None:
    """各種インタラクティブメッセージを送信する。
    
    Args:
        access_token: アクセストークン
        bot_id: BotのID
        channel_id: 送信先チャンネルID
    """
    # 1. ボタンテンプレートを送信
    button_actions = [
        {
            "type": "uri",
            "label": "LINE WORKS公式サイト",
            "uri": "https://line-works.com"
        },
        {
            "type": "message",
            "label": "FAQ",
            "postback": "ButtonTemplate_FAQ"
        },
        {
            "type": "message",
            "label": "お問い合わせ",
            "postback": "ButtonTemplate_Contact"
        }
    ]
    
    if send_button_template(access_token, bot_id, channel_id, 
                            "どのアクションを実行しますか？", button_actions):
        print("ボタンテンプレートの送信に成功しました。")
    else:
        print("ボタンテンプレートの送信に失敗しました。")
    
    # 2. リストテンプレートを送信
    elements = [
        {
            "title": "LINE WORKS",
            "subtitle": "企業向けコミュニケーションプラットフォーム",
            "originalContentUrl": "https://developers.worksmobile.com/favicon.ico",
            "action": {
                "type": "uri",
                "label": "詳細を見る",
                "uri": "https://line-works.com"
            }
        },
        {
            "title": "開発者向けドキュメント",
            "subtitle": "LINE WORKS APIの詳細情報",
            "originalContentUrl": "https://developers.worksmobile.com/favicon.ico",
            "action": {
                "type": "uri",
                "label": "ドキュメントへ",
                "uri": "https://developers.worksmobile.com/jp/document/"
            }
        }
    ]
    
    list_actions = [[
        {
            "type": "message",
            "label": "もっと見る",
            "postback": "ListTemplate_More"
        }
    ]]
    
    if send_list_template(
        access_token, 
        bot_id, 
        channel_id,
        background_image_url="https://developers.worksmobile.com/favicon.ico",
        title="LINE WORKS情報",
        subtitle="LINE WORKSに関する情報",
        elements=elements,
        actions=list_actions
    ):
        print("リストテンプレートの送信に成功しました。")
    else:
        print("リストテンプレートの送信に失敗しました。")
    
    # 3. クイックリプライ付きメッセージを送信
    quick_reply_items = [
        {
            "imageUrl": "https://developers.worksmobile.com/favicon.ico",
            "action": {
                "type": "message",
                "label": "はい",
                "text": "はい"
            }
        },
        {
            "imageUrl": "https://developers.worksmobile.com/favicon.ico",
            "action": {
                "type": "message",
                "label": "いいえ",
                "text": "いいえ"
            }
        },
        {
            "action": {
                "type": "camera",
                "label": "カメラを開く"
            }
        },
        {
            "action": {
                "type": "location",
                "label": "位置情報を送信"
            }
        }
    ]
    
    if send_message_with_quick_reply(
        access_token, 
        bot_id, 
        channel_id,
        "どのオプションを選びますか？",
        quick_reply_items
    ):
        print("クイックリプライ付きメッセージの送信に成功しました。")
    else:
        print("クイックリプライ付きメッセージの送信に失敗しました。")


def main() -> None:
    """メイン実行関数。
    
    環境変数から設定を読み込み、インタラクティブメッセージを送信します。
    実際のサービスではWebhookを設定して応答を処理する必要があります。
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
    
    print("LINE WORKS Bot インタラクティブメッセージ送信テスト開始")
    
    # アクセストークンを取得
    access_token = get_access_token(
        client_id, client_secret, service_account, private_key_path
    )
    if not access_token:
        print("アクセストークンの取得に失敗しました。")
        return
    
    # コールバックハンドラーの初期化
    callback_handler = CallbackHandler(bot_id)
    
    # はじめのテキストメッセージ
    if send_text_message(access_token, bot_id, test_channel_id, 
                          "インタラクティブメッセージのテストを開始します。"):
        print("開始メッセージの送信に成功しました。")
    else:
        print("開始メッセージの送信に失敗しました。")
    
    # インタラクティブメッセージを送信
    send_interactive_messages(access_token, bot_id, test_channel_id)
    
    # Webhook設定についての説明
    webhook_url = os.getenv("CALLBACK_URL")
    if webhook_url:
        webhook_message = f"""
Webhookは以下のURLに設定されています：
{webhook_url}

LINE WORKS Developer Consoleにてこのエンドポイントを
Bot設定のWebhookに登録してください。
        """
    else:
        webhook_message = """
ユーザーからのアクションを処理するには、Webhookの設定が必要です。
.envファイルのCALLBACK_URLを設定し、LINE WORKS Developer Consoleにて
そのエンドポイントをBot設定のWebhookに登録してください。
        """
    
    if send_text_message(access_token, bot_id, test_channel_id, webhook_message):
        print("Webhook設定に関するメッセージの送信に成功しました。")
    else:
        print("Webhook設定に関するメッセージの送信に失敗しました。")
    
    print("\nすべてのインタラクティブメッセージの送信が完了しました。")


if __name__ == "__main__":
    main()