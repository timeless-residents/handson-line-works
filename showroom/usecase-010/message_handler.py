"""メッセージ処理モジュール。

LINE WORKS Botが受信したメッセージを処理し、Claude 3.7で応答を生成します。
"""
import os
import json
import time
from typing import Dict, Any, Optional, Tuple, List

import requests
from conversation_manager import ConversationManager
from claude_client import ClaudeClient
from escalation import EscalationManager
import claude_prompt_templates


class MessageHandler:
    """メッセージ処理クラス。

    ユーザーからのメッセージを処理し、Claude 3.7で応答を生成します。
    """

    def __init__(
        self,
        bot_id: str,
        access_token: str,
        claude_client: ClaudeClient,
        system_prompt_path: str,
    ):
        """初期化。

        Args:
            bot_id: BotのID
            access_token: アクセストークン
            claude_client: Claude 3.7クライアント
            system_prompt_path: システムプロンプトファイルのパス
        """
        self.bot_id = bot_id
        self.access_token = access_token
        self.claude_client = claude_client
        self.system_prompt_path = system_prompt_path
        
        # 会話管理
        max_turns = int(os.getenv("MAX_CONVERSATION_TURNS", "10"))
        timeout_minutes = int(os.getenv("CONVERSATION_TIMEOUT_MINUTES", "60"))
        self.conversation_manager = ConversationManager(
            max_turns=max_turns,
            timeout_minutes=timeout_minutes
        )
        
        # エスカレーション管理
        self.escalation_manager = EscalationManager()
        
        # システムプロンプトを読み込み
        self.system_prompt = claude_prompt_templates.load_system_prompt(system_prompt_path)

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
                
                # 特殊コマンドを処理
                special_command_response = self._handle_special_commands(user_id, text)
                if special_command_response:
                    return {
                        "content": {
                            "type": "text",
                            "text": special_command_response
                        }
                    }
                
                # エスカレーションリクエストを処理
                if self.escalation_manager.is_escalation_request(text):
                    return self._handle_escalation_request(user_id, text)
                
                # 通常のメッセージ処理
                return self._process_normal_message(user_id, text)
            
            # 画像メッセージを処理
            elif message_type == "image":
                print(f"画像を受信しました (from: {user_id})")
                return {
                    "content": {
                        "type": "text",
                        "text": "申し訳ありませんが、現在テキストメッセージのみ対応しています。サポートが必要でしたら、テキストでご質問ください。"
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

    def _handle_special_commands(self, user_id: str, message: str) -> Optional[str]:
        """特殊コマンドを処理する。

        Args:
            user_id: ユーザーID
            message: ユーザーメッセージ

        Returns:
            特殊コマンド応答。特殊コマンドでない場合はNone。
        """
        # Claude API特殊コマンド処理
        special_response = self.claude_client.handle_special_commands(message)
        if special_response:
            if message.lower() in ["/reset", "リセット", "reset", "履歴削除"]:
                # 会話をリセット
                self.conversation_manager.reset_conversation(user_id)
            return special_response
        
        return None

    def _handle_escalation_request(self, user_id: str, message: str) -> Dict[str, Any]:
        """エスカレーションリクエストを処理する。

        Args:
            user_id: ユーザーID
            message: ユーザーメッセージ

        Returns:
            応答メッセージデータ
        """
        # 会話履歴を取得
        conversation_history = self.conversation_manager.get_formatted_messages(user_id)
        
        # ユーザーメッセージを会話履歴に追加
        self.conversation_manager.add_message(user_id, "user", message)
        
        # エスカレーションチケットを作成
        ticket_id, operator_message = self.escalation_manager.create_escalation_ticket(
            user_id, conversation_history, reason="ユーザーリクエスト"
        )
        
        # ボット応答を会話履歴に追加
        self.conversation_manager.add_message(user_id, "assistant", operator_message)
        
        return {
            "content": {
                "type": "text",
                "text": operator_message
            }
        }

    def _process_normal_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """通常のメッセージを処理する。

        Args:
            user_id: ユーザーID
            message: ユーザーメッセージ

        Returns:
            応答メッセージデータ
        """
        # 会話が新規かどうかをチェック
        is_new_conversation = self.conversation_manager.is_new_conversation(user_id)
        
        # ユーザーメッセージを会話履歴に追加
        self.conversation_manager.add_message(user_id, "user", message)
        
        # 会話履歴を取得
        conversation_history = self.conversation_manager.get_formatted_messages(user_id)
        
        # 新規会話の場合は挨拶を生成
        if is_new_conversation:
            # Claude用のシステムプロンプトに挨拶指示を追加
            greeting_prompt = self.system_prompt + "\n\n" + claude_prompt_templates.create_greetings_prompt()
            claude_response, metadata = self.claude_client.complete(greeting_prompt, conversation_history)
        else:
            # 通常の応答を生成
            claude_response, metadata = self.claude_client.complete(self.system_prompt, conversation_history)
        
        # ボット応答を会話履歴に追加
        self.conversation_manager.add_message(user_id, "assistant", claude_response)
        
        # メタデータをログに記録
        print(f"Claude API メタデータ: {json.dumps(metadata, indent=2)}")
        
        return {
            "content": {
                "type": "text",
                "text": claude_response
            }
        }

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