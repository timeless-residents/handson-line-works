"""オペレーターへのエスカレーション機能。

人間のオペレーターへの転送をシミュレートします。
実際の実装では、顧客管理システムやチケット管理システムとの連携が必要です。
"""
import os
import time
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Tuple


class EscalationManager:
    """エスカレーション管理クラス。

    ユーザーからのエスカレーションリクエストを管理します。
    実際の環境では、この機能を顧客管理システムと連携させることが推奨されます。
    """

    def __init__(self, storage_dir: str = "escalations"):
        """初期化。

        Args:
            storage_dir: エスカレーション情報保存ディレクトリ（デフォルト: escalations）
        """
        self.storage_dir = storage_dir
        
        # エスカレーション情報の保存ディレクトリを作成
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)

    def create_escalation_ticket(
        self, user_id: str, conversation_history: list, reason: str = "ユーザーリクエスト"
    ) -> Tuple[str, str]:
        """エスカレーションチケットを作成する。

        Args:
            user_id: ユーザーID
            conversation_history: 会話履歴
            reason: エスカレーション理由

        Returns:
            (チケットID, オペレーター応答メッセージ)のタプル
        """
        # チケットIDを生成（例: ESC-20240315-XXXX）
        current_date = datetime.now().strftime("%Y%m%d")
        ticket_id = f"ESC-{current_date}-{str(uuid.uuid4())[:4].upper()}"
        
        # エスカレーション情報
        escalation_info = {
            "ticket_id": ticket_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "status": "pending",  # pending, assigned, resolved
            "reason": reason,
            "assigned_to": None,
            "conversation_history": conversation_history,
            "notes": []
        }
        
        # エスカレーション情報を保存
        try:
            file_path = os.path.join(self.storage_dir, f"{ticket_id}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(escalation_info, f, ensure_ascii=False, indent=2)
            print(f"エスカレーションチケット {ticket_id} を作成しました。")
        except Exception as e:
            print(f"エスカレーションチケットの保存中にエラーが発生しました: {e}")
        
        # オペレーター応答メッセージ
        operator_message = f"""
かしこまりました。人間のオペレーターへのエスカレーションをリクエストしました。営業時間（平日9:00-18:00）内であれば、通常30分以内に担当者からご連絡いたします。

[エスカレーションチケット: {ticket_id}]

それまでの間、FAQをご覧いただくか、他のご質問がございましたらお気軽にお知らせください。お待たせして申し訳ありませんが、よろしくお願いいたします。
"""
        
        return ticket_id, operator_message

    def check_escalation_status(self, ticket_id: str) -> Dict[str, Any]:
        """エスカレーションチケットのステータスを確認する。

        Args:
            ticket_id: チケットID

        Returns:
            チケット情報。見つからない場合は空の辞書。
        """
        try:
            file_path = os.path.join(self.storage_dir, f"{ticket_id}.json")
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                print(f"チケット {ticket_id} が見つかりません。")
                return {}
        except Exception as e:
            print(f"チケット情報の読み込み中にエラーが発生しました: {e}")
            return {}

    def update_escalation_status(
        self, ticket_id: str, status: str, assigned_to: Optional[str] = None, notes: Optional[str] = None
    ) -> bool:
        """エスカレーションチケットのステータスを更新する。

        Args:
            ticket_id: チケットID
            status: 新しいステータス（pending, assigned, resolved）
            assigned_to: 担当者名（オプション）
            notes: メモ（オプション）

        Returns:
            更新に成功した場合はTrue、失敗した場合はFalse
        """
        try:
            ticket = self.check_escalation_status(ticket_id)
            if not ticket:
                return False
            
            ticket["status"] = status
            if assigned_to:
                ticket["assigned_to"] = assigned_to
            
            if notes:
                note_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "content": notes
                }
                ticket["notes"].append(note_entry)
            
            file_path = os.path.join(self.storage_dir, f"{ticket_id}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(ticket, f, ensure_ascii=False, indent=2)
            
            print(f"チケット {ticket_id} のステータスを '{status}' に更新しました。")
            return True
        except Exception as e:
            print(f"チケットステータスの更新中にエラーが発生しました: {e}")
            return False

    def is_escalation_request(self, message: str) -> bool:
        """メッセージがエスカレーションリクエストかどうかを判定する。

        Args:
            message: ユーザーメッセージ

        Returns:
            エスカレーションリクエストの場合はTrue、そうでない場合はFalse
        """
        escalation_keywords = [
            "オペレーター", "オペレータ", "operator", "人間", "human", 
            "担当者", "対応者", "話したい", "代わって", "電話", "直接話"
        ]
        message_lower = message.lower()
        
        # エスカレーションキーワードを含むか確認
        for keyword in escalation_keywords:
            if keyword in message_lower:
                return True
                
        return False