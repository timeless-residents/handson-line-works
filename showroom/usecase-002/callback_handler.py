"""LINE WORKS Bot API コールバック処理モジュール。

Webhookを通じて受信したユーザーアクションのコールバックを処理します。
"""
from typing import Dict, Any, Union, List, Optional
import json


class CallbackHandler:
    """LINE WORKS Bot APIコールバック処理クラス。
    
    Webhookを通じて受信したユーザーアクションを処理し、適切な応答を生成します。
    実際のサーバー実装はFlaskやFastAPIなどのWebフレームワークで行う必要があります。
    """
    
    def __init__(self, bot_id: str):
        """初期化。
        
        Args:
            bot_id: BotのID
        """
        self.bot_id = bot_id
        # アクションタイプに対応するハンドラーを登録
        self.handlers = {
            "message": self._handle_message_action,
            "postback": self._handle_postback_action,
        }
    
    def handle_callback(self, callback_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """コールバックデータを処理する。
        
        Args:
            callback_data: Webhookから受け取ったコールバックデータ
            
        Returns:
            応答メッセージデータ。処理できない場合はNone。
        """
        try:
            print("コールバックデータを受信しました:")
            print(json.dumps(callback_data, indent=2, ensure_ascii=False))
            
            # 必要なデータの抽出
            content = callback_data.get("content", {})
            message_type = content.get("type")
            
            # ポストバックデータがあるかチェック
            postback = content.get("postback")
            
            if message_type == "text":
                # ポストバックデータが含まれている場合は特別に処理
                if postback:
                    print(f"ポストバックデータ付きのテキストメッセージを処理: {postback}")
                    return self._handle_template_action(callback_data, postback)
                # 通常のテキストメッセージを処理
                return self._handle_text_message(callback_data)
            elif message_type == "action":
                # アクションを処理
                action_type = content.get("action", {}).get("type")
                if action_type in self.handlers:
                    return self.handlers[action_type](callback_data)
                else:
                    print(f"未対応のアクションタイプ: {action_type}")
            else:
                print(f"未対応のメッセージタイプ: {message_type}")
            
            return None
        except Exception as e:
            print(f"コールバック処理中にエラーが発生しました: {e}")
            return None
    
    def _handle_text_message(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """テキストメッセージを処理する。
        
        Args:
            callback_data: コールバックデータ
            
        Returns:
            応答メッセージデータ
        """
        text = callback_data.get("content", {}).get("text", "")
        channel_id = callback_data.get("source", {}).get("channelId")
        
        # テキストに応じた応答を生成
        if "こんにちは" in text or "hello" in text.lower():
            return {
                "content": {
                    "type": "text",
                    "text": "こんにちは！何かお手伝いできることはありますか？"
                }
            }
        elif "ヘルプ" in text or "help" in text.lower():
            return {
                "content": {
                    "type": "button_template",
                    "contentText": "以下から選択してください：",
                    "actions": [
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
                }
            }
        else:
            return {
                "content": {
                    "type": "text",
                    "text": f"「{text}」というメッセージを受け取りました。"
                }
            }
    
    def _handle_message_action(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """messageタイプのアクションを処理する。
        
        Args:
            callback_data: コールバックデータ
            
        Returns:
            応答メッセージデータ
        """
        action = callback_data.get("content", {}).get("action", {})
        label = action.get("label", "")
        postback = action.get("postback", "")
        
        # postbackの値に応じた応答を生成
        if postback == "ButtonTemplate_FAQ":
            return {
                "content": {
                    "type": "text",
                    "text": "FAQ:\n1. Q: サービスの利用時間は？\n   A: 24時間ご利用いただけます。\n2. Q: パスワードを忘れた場合は？\n   A: ログイン画面の「パスワードを忘れた方」からリセットできます。"
                }
            }
        elif postback == "ButtonTemplate_Contact":
            return {
                "content": {
                    "type": "text",
                    "text": "お問い合わせはカスタマーサポート(support@example.com)までご連絡ください。"
                }
            }
        else:
            return {
                "content": {
                    "type": "text",
                    "text": f"「{label}」ボタンがクリックされました。postback={postback}"
                }
            }
    
    def _handle_postback_action(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """postbackタイプのアクションを処理する。
        
        Args:
            callback_data: コールバックデータ
            
        Returns:
            応答メッセージデータ
        """
        action = callback_data.get("content", {}).get("action", {})
        data = action.get("data", "")
        
        # dataの値に応じた応答を生成
        if "product_" in data:
            product_id = data.replace("product_", "")
            return {
                "content": {
                    "type": "text",
                    "text": f"製品ID {product_id} の詳細情報を表示します。"
                }
            }
        elif "category_" in data:
            category = data.replace("category_", "")
            return {
                "content": {
                    "type": "text",
                    "text": f"{category}カテゴリの製品一覧を表示します。"
                }
            }
        else:
            return {
                "content": {
                    "type": "text",
                    "text": f"postbackデータ「{data}」を受け取りました。"
                }
            }
            
    def _handle_template_action(self, callback_data: Dict[str, Any], postback: str) -> Dict[str, Any]:
        """テンプレートメッセージのボタン押下時のポストバックを処理する。
        
        Args:
            callback_data: コールバックデータ
            postback: ポストバックデータ
            
        Returns:
            応答メッセージデータ
        """
        text = callback_data.get("content", {}).get("text", "")
        
        # ポストバックの値に応じた応答を生成
        if postback == "ButtonTemplate_FAQ":
            return {
                "content": {
                    "type": "text",
                    "text": "FAQ:\n1. Q: サービスの利用時間は？\n   A: 24時間ご利用いただけます。\n2. Q: パスワードを忘れた場合は？\n   A: ログイン画面の「パスワードを忘れた方」からリセットできます。"
                }
            }
        elif postback == "ButtonTemplate_Contact":
            return {
                "content": {
                    "type": "text",
                    "text": "お問い合わせはカスタマーサポート(support@example.com)までご連絡ください。"
                }
            }
        elif postback == "ListTemplate_More":
            return {
                "content": {
                    "type": "text",
                    "text": "さらに多くの情報を提供します。LINE WORKSの開発者ポータルについては https://developers.worksmobile.com/jp/ をご覧ください。"
                }
            }
        else:
            return {
                "content": {
                    "type": "text",
                    "text": f"「{text}」メッセージを受け取りました。postback={postback}"
                }
            }


def create_webhook_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """Webhook応答データを作成する。
    
    Args:
        response_data: 応答メッセージデータ
        
    Returns:
        Webhook応答データ
    """
    return response_data