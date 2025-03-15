"""メッセージ処理モジュール。

LINE WORKS Botが受信したメッセージを処理し、適切な応答を生成します。
"""
import json
import random
import re
from typing import Dict, Any, Optional, List

import requests
from response_templates import (
    KEYWORD_RESPONSES,
    REGEX_PATTERNS,
    FALLBACK_RESPONSES,
    BOT_INTRODUCTION,
)
from conversation import ConversationManager


class MessageHandler:
    """メッセージ処理クラス。

    ユーザーからのメッセージを処理し、適切な応答を生成します。
    """

    def __init__(self, bot_id: str, access_token: str):
        """初期化。

        Args:
            bot_id: BotのID
            access_token: アクセストークン
        """
        self.bot_id = bot_id
        self.access_token = access_token
        self.conversation_manager = ConversationManager()

    def handle_message(self, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """メッセージを処理する。

        Args:
            message_data: 受信したメッセージデータ

        Returns:
            応答メッセージデータ。処理できない場合はNone。
        """
        try:
            # メッセージのタイプを取得
            content = message_data.get("content", {})
            message_type = content.get("type")
            
            # ユーザーID取得
            user_id = message_data.get("source", {}).get("userId")
            
            if not user_id:
                print("ユーザーIDが取得できませんでした")
                return None
            
            # テキストメッセージを処理
            if message_type == "text":
                text = content.get("text", "").strip()
                print(f"テキストメッセージを受信: '{text}' (from: {user_id})")
                
                # 会話履歴に追加
                self.conversation_manager.add_to_history(user_id, text)
                
                # 応答を生成
                response = self.generate_response(user_id, text)
                
                # 応答を履歴に追加
                self.conversation_manager.add_to_history(user_id, response, is_bot=True)
                
                return {
                    "content": {
                        "type": "text",
                        "text": response
                    }
                }
            
            # 画像メッセージを処理
            elif message_type == "image":
                print(f"画像を受信しました (from: {user_id})")
                return {
                    "content": {
                        "type": "text",
                        "text": "画像を受け取りました。ただし、現在テキストメッセージのみ対応しています。"
                    }
                }
            
            # ビデオメッセージを処理
            elif message_type == "video":
                print(f"ビデオを受信しました (from: {user_id})")
                return {
                    "content": {
                        "type": "text",
                        "text": "ビデオを受け取りました。ただし、現在テキストメッセージのみ対応しています。"
                    }
                }
            
            # その他のメッセージタイプを処理
            else:
                print(f"未対応のメッセージタイプ: {message_type}")
                return {
                    "content": {
                        "type": "text",
                        "text": "申し訳ありません、このタイプのメッセージには対応していません。テキストでお問い合わせください。"
                    }
                }
            
        except Exception as e:
            print(f"メッセージ処理中にエラーが発生しました: {e}")
            return {
                "content": {
                    "type": "text",
                    "text": "メッセージ処理中にエラーが発生しました。しばらく経ってからもう一度お試しください。"
                }
            }

    def generate_response(self, user_id: str, message: str) -> str:
        """ユーザーメッセージに対する応答を生成する。

        Args:
            user_id: ユーザーID
            message: ユーザーのメッセージ

        Returns:
            応答テキスト
        """
        # 会話フロー中の場合はそのフローを処理
        processed, flow_response = self.conversation_manager.handle_flow(user_id, message)
        if processed and flow_response:
            return flow_response
        
        # ボットの紹介を要求する特殊コマンド
        if message.lower() in ["自己紹介", "ボット", "bot", "intro", "introduction"]:
            return BOT_INTRODUCTION
        
        # キーワードベースの応答
        for keyword, response in KEYWORD_RESPONSES.items():
            if keyword in message.lower():
                return response
        
        # 正規表現ベースの応答
        for pattern, response in REGEX_PATTERNS:
            if pattern.search(message):
                return response
        
        # ランダムなフォールバック応答を返す
        return random.choice(FALLBACK_RESPONSES)

    def send_message(self, target_id: str, message: Dict[str, Any], is_user: bool = True) -> bool:
        """メッセージを送信する。

        Args:
            target_id: 送信先のIDまたはチャンネルID
            message: 送信するメッセージデータ
            is_user: ユーザーへの送信か（Falseの場合はチャンネルへの送信）

        Returns:
            送信に成功した場合はTrue、失敗した場合はFalse
        """
        try:
            # 送信先に応じてエンドポイントを構築
            if is_user:
                url = f"https://www.worksapis.com/v1.0/bots/{self.bot_id}/users/{target_id}/messages"
            else:
                url = f"https://www.worksapis.com/v1.0/bots/{self.bot_id}/channels/{target_id}/messages"
            
            # ヘッダー設定
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
            
            # リクエスト送信
            response = requests.post(url, headers=headers, json=message, timeout=30)
            
            # レスポンス確認
            if response.status_code in (200, 201):
                print(f"メッセージ送信成功: {url}")
                return True
            else:
                print(f"メッセージ送信エラー: {response.status_code}")
                print(response.text)
                return False
                
        except Exception as e:
            print(f"メッセージ送信中にエラーが発生しました: {e}")
            return False