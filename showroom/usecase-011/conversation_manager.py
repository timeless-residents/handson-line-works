"""会話管理モジュール。

ユーザーごとの会話履歴を管理し、文脈を保持します。
"""
import os
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class ConversationManager:
    """会話管理クラス。

    ユーザーごとの会話履歴を管理し、会話の文脈を保持します。
    """

    def __init__(
        self,
        max_turns: int = 10,
        timeout_minutes: int = 60,
        storage_dir: str = "conversations",
    ):
        """初期化。

        Args:
            max_turns: 保持する最大会話ターン数（デフォルト: 10）
            timeout_minutes: 会話タイムアウト時間（分）（デフォルト: 60）
            storage_dir: 会話履歴保存ディレクトリ（デフォルト: conversations）
        """
        self.max_turns = max_turns
        self.timeout_minutes = timeout_minutes
        self.storage_dir = storage_dir
        
        # 会話履歴の保存ディレクトリを作成
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
        
        # インメモリの会話履歴キャッシュ
        self.conversations: Dict[str, Dict[str, Any]] = {}
        
        # 起動時に既存の会話履歴をロード
        self._load_conversations()

    def _load_conversations(self) -> None:
        """保存されている会話履歴をロードする。"""
        try:
            files = [f for f in os.listdir(self.storage_dir) if f.endswith(".json")]
            for file in files:
                try:
                    with open(os.path.join(self.storage_dir, file), "r", encoding="utf-8") as f:
                        conversation = json.load(f)
                        user_id = file.split(".")[0]
                        self.conversations[user_id] = conversation
                except Exception as e:
                    print(f"会話履歴ファイル {file} の読み込みに失敗しました: {e}")
            
            print(f"{len(files)} 件の会話履歴をロードしました。")
        except Exception as e:
            print(f"会話履歴のロード中にエラーが発生しました: {e}")

    def _save_conversation(self, user_id: str) -> None:
        """会話履歴を保存する。

        Args:
            user_id: ユーザーID
        """
        try:
            if user_id in self.conversations:
                file_path = os.path.join(self.storage_dir, f"{user_id}.json")
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(self.conversations[user_id], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"会話履歴の保存中にエラーが発生しました: {e}")

    def get_or_create_conversation(self, user_id: str) -> Dict[str, Any]:
        """ユーザーの会話情報を取得または作成する。

        Args:
            user_id: ユーザーID

        Returns:
            会話情報
        """
        current_time = datetime.now()
        
        # 既存の会話がある場合
        if user_id in self.conversations:
            conversation = self.conversations[user_id]
            
            # タイムアウトチェック
            last_interaction = datetime.fromisoformat(conversation["last_interaction"])
            timeout_delta = timedelta(minutes=self.timeout_minutes)
            
            if current_time - last_interaction > timeout_delta:
                # タイムアウトした場合は新しい会話を開始
                print(f"ユーザー {user_id} の会話がタイムアウトしました。新しい会話を開始します。")
                conversation["messages"] = []
                conversation["metadata"]["is_new_conversation"] = True
            else:
                conversation["metadata"]["is_new_conversation"] = False
            
            # 最終対話時間を更新
            conversation["last_interaction"] = current_time.isoformat()
            return conversation
        
        # 新しい会話を作成
        conversation = {
            "user_id": user_id,
            "created_at": current_time.isoformat(),
            "last_interaction": current_time.isoformat(),
            "messages": [],
            "metadata": {
                "is_new_conversation": True,
                "source": "line_works",
                "language": "ja",
                "topic": None,
                "last_documents": [],
            }
        }
        
        self.conversations[user_id] = conversation
        return conversation

    def add_message(self, user_id: str, role: str, content: str) -> None:
        """会話に新しいメッセージを追加する。

        Args:
            user_id: ユーザーID
            role: メッセージの役割（"user" または "assistant"）
            content: メッセージの内容
        """
        if role not in ["user", "assistant"]:
            print(f"無効なメッセージロール: {role}")
            return
        
        conversation = self.get_or_create_conversation(user_id)
        
        # メッセージを追加
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        conversation["messages"].append(message)
        
        # 最大ターン数を超えた場合、古いメッセージを削除
        if len(conversation["messages"]) > self.max_turns * 2:
            conversation["messages"] = conversation["messages"][-self.max_turns * 2:]
        
        # 会話を保存
        self._save_conversation(user_id)

    def update_metadata(self, user_id: str, key: str, value: Any) -> None:
        """会話メタデータを更新する。

        Args:
            user_id: ユーザーID
            key: メタデータキー
            value: メタデータ値
        """
        conversation = self.get_or_create_conversation(user_id)
        conversation["metadata"][key] = value
        self._save_conversation(user_id)

    def get_conversation_history(self, user_id: str) -> List[Dict[str, str]]:
        """GPTに送信する形式で会話履歴を取得する。

        Args:
            user_id: ユーザーID

        Returns:
            GPT API形式の会話履歴
        """
        conversation = self.get_or_create_conversation(user_id)
        formatted_messages = []
        
        for message in conversation["messages"]:
            if message["role"] in ["user", "assistant"]:
                formatted_messages.append({
                    "role": message["role"],
                    "content": message["content"]
                })
        
        return formatted_messages

    def get_user_last_question(self, user_id: str) -> Optional[str]:
        """ユーザーの最後の質問を取得する。

        Args:
            user_id: ユーザーID

        Returns:
            最後の質問。質問がない場合はNone。
        """
        conversation = self.get_or_create_conversation(user_id)
        
        # 最新のユーザーメッセージを探す
        for message in reversed(conversation["messages"]):
            if message["role"] == "user":
                return message["content"]
        
        return None
    
    def get_last_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """前回の応答で使用したドキュメントを取得する。

        Args:
            user_id: ユーザーID

        Returns:
            前回使用したドキュメントのリスト
        """
        conversation = self.get_or_create_conversation(user_id)
        return conversation["metadata"].get("last_documents", [])
    
    def set_last_documents(self, user_id: str, documents: List[Dict[str, Any]]) -> None:
        """使用したドキュメント情報を保存する。

        Args:
            user_id: ユーザーID
            documents: 使用したドキュメント情報
        """
        self.update_metadata(user_id, "last_documents", documents)

    def reset_conversation(self, user_id: str) -> None:
        """ユーザーの会話をリセットする。

        Args:
            user_id: ユーザーID
        """
        if user_id in self.conversations:
            current_time = datetime.now()
            self.conversations[user_id]["messages"] = []
            self.conversations[user_id]["last_interaction"] = current_time.isoformat()
            self.conversations[user_id]["metadata"]["is_new_conversation"] = True
            self.conversations[user_id]["metadata"]["topic"] = None
            self.conversations[user_id]["metadata"]["last_documents"] = []
            self._save_conversation(user_id)
    
    def is_new_conversation(self, user_id: str) -> bool:
        """会話が新規かどうかを確認する。

        Args:
            user_id: ユーザーID

        Returns:
            新規会話の場合はTrue、そうでない場合はFalse
        """
        conversation = self.get_or_create_conversation(user_id)
        return conversation["metadata"].get("is_new_conversation", True)

    def set_topic(self, user_id: str, topic: str) -> None:
        """会話のトピックを設定する。

        Args:
            user_id: ユーザーID
            topic: トピック
        """
        self.update_metadata(user_id, "topic", topic)
    
    def get_topic(self, user_id: str) -> Optional[str]:
        """会話のトピックを取得する。

        Args:
            user_id: ユーザーID

        Returns:
            トピック。設定されていない場合はNone。
        """
        conversation = self.get_or_create_conversation(user_id)
        return conversation["metadata"].get("topic")

    def cleanup_old_conversations(self, days: int = 30) -> int:
        """古い会話履歴をクリーンアップする。

        Args:
            days: 保持する日数（デフォルト: 30）

        Returns:
            削除された会話の数
        """
        deleted_count = 0
        current_time = datetime.now()
        retention_delta = timedelta(days=days)
        
        try:
            files = [f for f in os.listdir(self.storage_dir) if f.endswith(".json")]
            for file in files:
                try:
                    file_path = os.path.join(self.storage_dir, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        conversation = json.load(f)
                    
                    last_interaction = datetime.fromisoformat(conversation["last_interaction"])
                    if current_time - last_interaction > retention_delta:
                        # 古い会話を削除
                        os.remove(file_path)
                        user_id = file.split(".")[0]
                        if user_id in self.conversations:
                            del self.conversations[user_id]
                        deleted_count += 1
                        
                except Exception as e:
                    print(f"会話履歴ファイル {file} の処理中にエラーが発生しました: {e}")
            
            print(f"{deleted_count} 件の古い会話履歴を削除しました。")
        except Exception as e:
            print(f"古い会話履歴のクリーンアップ中にエラーが発生しました: {e}")
        
        return deleted_count