"""メッセージ処理モジュール。

LINE WORKS Botが受信したメッセージを処理し、RAGを使用して応答を生成します。
"""
import os
import json
import time
from typing import Dict, Any, Optional, Tuple, List

import requests
from conversation_manager import ConversationManager
from gpt_client import GPTClient
from rag_engine import RAGEngine
from vector_store import VectorStore


class MessageHandler:
    """メッセージ処理クラス。

    ユーザーからのメッセージを処理し、RAG機能を使用して応答を生成します。
    """

    def __init__(
        self,
        bot_id: str,
        access_token: str,
        gpt_client: GPTClient,
        rag_engine: RAGEngine,
    ):
        """初期化。

        Args:
            bot_id: BotのID
            access_token: アクセストークン
            gpt_client: GPTクライアント
            rag_engine: RAGエンジン
        """
        self.bot_id = bot_id
        self.access_token = access_token
        self.gpt_client = gpt_client
        self.rag_engine = rag_engine
        
        # 会話管理
        max_turns = int(os.getenv("MAX_CONVERSATION_TURNS", "10"))
        timeout_minutes = int(os.getenv("CONVERSATION_TIMEOUT_MINUTES", "60"))
        self.conversation_manager = ConversationManager(
            max_turns=max_turns,
            timeout_minutes=timeout_minutes
        )

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
                
                # 検索クエリを処理
                if text.startswith("/search ") or text.startswith("検索 "):
                    query = text.replace("/search ", "").replace("検索 ", "").strip()
                    if query:
                        return self._handle_search_query(user_id, query)
                
                # 通常のRAG検索・回答生成
                return self._process_rag_message(user_id, text)
            
            # 画像メッセージを処理
            elif message_type == "image":
                print(f"画像を受信しました (from: {user_id})")
                return {
                    "content": {
                        "type": "text",
                        "text": "申し訳ありませんが、現在テキストメッセージのみ対応しています。社内規定についての質問をテキストでお送りください。"
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
        # GPT特殊コマンド処理
        special_response = self.gpt_client.handle_special_commands(message)
        if special_response:
            if message.lower() in ["/reset", "リセット", "reset", "履歴削除"]:
                # 会話をリセット
                self.conversation_manager.reset_conversation(user_id)
            return special_response
        
        # フィードバックコマンド
        if message.startswith("/feedback") or message.startswith("フィードバック"):
            feedback_text = message.replace("/feedback", "").replace("フィードバック", "").strip()
            if feedback_text:
                self._save_feedback(user_id, feedback_text)
                return "フィードバックをありがとうございます。今後のサービス改善に役立てます。"
            else:
                return "フィードバックを入力してください。例: /feedback 回答が不正確でした"
        
        return None

    def _handle_search_query(self, user_id: str, query: str) -> Dict[str, Any]:
        """検索クエリを処理する。

        Args:
            user_id: ユーザーID
            query: 検索クエリ

        Returns:
            応答メッセージデータ
        """
        # RAGエンジンで検索
        search_results = self.rag_engine.search_relevant_documents(query, top_k=5)
        
        if not search_results:
            return {
                "content": {
                    "type": "text",
                    "text": f"「{query}」に関連する文書は見つかりませんでした。別のキーワードでお試しください。"
                }
            }
        
        # 検索結果をフォーマット
        result_text = f"「{query}」の検索結果:\n\n"
        for i, result in enumerate(search_results):
            doc = result.document
            file_name = doc.metadata.get("file_name", "不明")
            preview = doc.page_content[:100].replace("\n", " ")
            score = result.score
            
            result_text += f"{i+1}. {file_name} (関連度: {score:.2f})\n"
            result_text += f"   {preview}...\n\n"
        
        result_text += "詳細を知りたい場合は、質問を具体的にお尋ねください。"
        
        return {
            "content": {
                "type": "text",
                "text": result_text
            }
        }

    def _process_rag_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """通常のRAG処理を実行する。

        Args:
            user_id: ユーザーID
            message: ユーザーメッセージ

        Returns:
            応答メッセージデータ
        """
        # ユーザーメッセージを会話履歴に追加
        self.conversation_manager.add_message(user_id, "user", message)
        
        # 会話履歴を取得
        conversation_history = self.conversation_manager.get_conversation_history(user_id)
        
        # RAGを使用して回答を生成
        answer, used_documents, metadata = self.rag_engine.generate_answer_with_rag(
            message, conversation_history
        )
        
        # 使用した文書情報を保存
        self.conversation_manager.set_last_documents(user_id, used_documents)
        
        # 応答を会話履歴に追加
        self.conversation_manager.add_message(user_id, "assistant", answer)
        
        # メタデータをログに記録
        print(f"GPT API メタデータ: {json.dumps(metadata, indent=2)}")
        
        return {
            "content": {
                "type": "text",
                "text": answer
            }
        }

    def _save_feedback(self, user_id: str, feedback: str) -> None:
        """ユーザーからのフィードバックを保存する。

        Args:
            user_id: ユーザーID
            feedback: フィードバックテキスト
        """
        try:
            feedback_dir = "feedback"
            os.makedirs(feedback_dir, exist_ok=True)
            
            # フィードバック情報を構築
            feedback_data = {
                "user_id": user_id,
                "feedback": feedback,
                "timestamp": time.time(),
                "conversation_history": self.conversation_manager.get_conversation_history(user_id),
                "last_documents": self.conversation_manager.get_last_documents(user_id)
            }
            
            # フィードバックを保存
            file_path = os.path.join(feedback_dir, f"feedback_{int(time.time())}_{user_id}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(feedback_data, f, ensure_ascii=False, indent=2)
            
            print(f"フィードバックを保存しました: {file_path}")
        except Exception as e:
            print(f"フィードバックの保存中にエラーが発生しました: {e}")

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