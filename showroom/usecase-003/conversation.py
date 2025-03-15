"""会話管理モジュール。

ユーザーとの会話状態を管理し、コンテキストを保持します。
"""
import random
import re
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from dateutil import parser as date_parser

from response_templates import (
    VACATION_FORM,
    VACATION_TYPE_MAP,
    INQUIRY_FORM,
    INQUIRY_CATEGORY_MAP,
)


class ConversationManager:
    """会話管理クラス。

    ユーザーごとの会話状態やコンテキスト情報を管理します。
    状態遷移に基づいた対話フローを実現します。
    """

    def __init__(self):
        """初期化。"""
        # ユーザーID -> 状態情報のマッピング
        self.user_states: Dict[str, Dict[str, Any]] = {}
        # 会話履歴（最大10件）
        self.conversation_history: Dict[str, list] = {}

    def get_user_state(self, user_id: str) -> Dict[str, Any]:
        """ユーザーの現在の状態を取得する。

        Args:
            user_id: ユーザーID

        Returns:
            ユーザーの状態情報
        """
        if user_id not in self.user_states:
            # 新規ユーザーの場合は初期状態を設定
            self.user_states[user_id] = {
                "state": "INITIAL",
                "data": {},
                "last_interaction": datetime.now(),
                "conversation_count": 0,
            }
        
        # 会話カウントを増やす
        self.user_states[user_id]["conversation_count"] += 1
        # 最終対話時間を更新
        self.user_states[user_id]["last_interaction"] = datetime.now()
        
        return self.user_states[user_id]

    def add_to_history(self, user_id: str, message: str, is_bot: bool = False) -> None:
        """会話履歴にメッセージを追加する。

        Args:
            user_id: ユーザーID
            message: メッセージ内容
            is_bot: Botからのメッセージかどうか
        """
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        # メッセージを履歴に追加
        self.conversation_history[user_id].append({
            "timestamp": datetime.now(),
            "is_bot": is_bot,
            "message": message
        })
        
        # 履歴が10件を超えたら古いものから削除
        if len(self.conversation_history[user_id]) > 10:
            self.conversation_history[user_id].pop(0)

    def get_history(self, user_id: str) -> list:
        """ユーザーの会話履歴を取得する。

        Args:
            user_id: ユーザーID

        Returns:
            会話履歴のリスト
        """
        return self.conversation_history.get(user_id, [])

    def reset_state(self, user_id: str) -> None:
        """ユーザーの状態を初期状態にリセットする。

        Args:
            user_id: ユーザーID
        """
        if user_id in self.user_states:
            self.user_states[user_id]["state"] = "INITIAL"
            self.user_states[user_id]["data"] = {}

    def handle_vacation_flow(self, user_id: str, message: str) -> str:
        """休暇申請フローを処理する。

        Args:
            user_id: ユーザーID
            message: ユーザーのメッセージ

        Returns:
            応答メッセージ
        """
        state_data = self.get_user_state(user_id)
        current_state = state_data["state"]
        data = state_data["data"]
        
        # 初期状態または休暇申請コマンドの場合
        if current_state == "INITIAL" and "休暇申請" in message:
            state_data["state"] = "VACATION_DATE"
            return VACATION_FORM["VACATION_DATE"]
        
        # 日付入力待ち状態
        elif current_state == "VACATION_DATE":
            # 日付のバリデーション
            try:
                # dateutil.parserを使用して柔軟に日付を解析
                parsed_date = date_parser.parse(message, fuzzy=True)
                # 2025年以降の日付のみ許可（例）
                if parsed_date.year < 2025:
                    return "2025年以降の日付を入力してください。"
                
                # 日付をYYYY-MM-DD形式で保存
                data["date"] = parsed_date.strftime("%Y-%m-%d")
                state_data["state"] = "VACATION_TYPE"
                return VACATION_FORM["VACATION_TYPE"]
            
            except (ValueError, OverflowError):
                return "正しい日付形式で入力してください（例：2025-04-01）"
        
        # 休暇種類の入力待ち状態
        elif current_state == "VACATION_TYPE":
            # 入力された休暇種類を変換
            vacation_type = VACATION_TYPE_MAP.get(message)
            if not vacation_type:
                return "1、2、3のいずれか、または「有給」「代休」「特別」と入力してください。"
            
            data["type"] = vacation_type
            state_data["state"] = "VACATION_REASON"
            return VACATION_FORM["VACATION_REASON"]
        
        # 理由の入力待ち状態
        elif current_state == "VACATION_REASON":
            data["reason"] = message
            state_data["state"] = "VACATION_CONFIRM"
            
            # 確認メッセージの生成（テンプレート内の変数を置換）
            confirm_msg = VACATION_FORM["VACATION_CONFIRM"].format(
                date=data["date"],
                type=data["type"],
                reason=data["reason"]
            )
            return confirm_msg
        
        # 確認待ち状態
        elif current_state == "VACATION_CONFIRM":
            if message.lower() in ["はい", "yes", "ok", "確認", "承認"]:
                # 申請IDを生成（実際はデータベースに保存する）
                application_id = str(uuid.uuid4())[:8]
                data["id"] = application_id
                
                # 完了メッセージの生成
                complete_msg = VACATION_FORM["VACATION_COMPLETE"].format(
                    id=application_id
                )
                
                # 状態をリセット
                self.reset_state(user_id)
                return complete_msg
            else:
                # キャンセルメッセージ
                self.reset_state(user_id)
                return VACATION_FORM["VACATION_CANCEL"]
        
        return "休暇申請処理中にエラーが発生しました。「休暇申請」と入力して最初からやり直してください。"

    def handle_inquiry_flow(self, user_id: str, message: str) -> str:
        """問い合わせフローを処理する。

        Args:
            user_id: ユーザーID
            message: ユーザーのメッセージ

        Returns:
            応答メッセージ
        """
        state_data = self.get_user_state(user_id)
        current_state = state_data["state"]
        data = state_data["data"]
        
        # 初期状態または問い合わせコマンドの場合
        if current_state == "INITIAL" and "問い合わせ" in message:
            state_data["state"] = "INQUIRY_CATEGORY"
            return INQUIRY_FORM["INQUIRY_CATEGORY"]
        
        # カテゴリ入力待ち状態
        elif current_state == "INQUIRY_CATEGORY":
            # 入力されたカテゴリを変換
            category = INQUIRY_CATEGORY_MAP.get(message)
            if not category:
                return "1、2、3のいずれか、または「製品」「サービス」「その他」と入力してください。"
            
            data["category"] = category
            state_data["state"] = "INQUIRY_DETAIL"
            return INQUIRY_FORM["INQUIRY_DETAIL"]
        
        # 詳細入力待ち状態
        elif current_state == "INQUIRY_DETAIL":
            data["detail"] = message
            state_data["state"] = "INQUIRY_CONTACT"
            return INQUIRY_FORM["INQUIRY_CONTACT"]
        
        # 連絡先入力待ち状態
        elif current_state == "INQUIRY_CONTACT":
            # 簡易的な連絡先バリデーション
            if not re.match(r'.+@.+\..+', message) and not re.match(r'[\d\-\+]+', message):
                return "有効なメールアドレスまたは電話番号を入力してください。"
            
            data["contact"] = message
            state_data["state"] = "INQUIRY_CONFIRM"
            
            # 確認メッセージの生成
            confirm_msg = INQUIRY_FORM["INQUIRY_CONFIRM"].format(
                category=data["category"],
                detail=data["detail"],
                contact=data["contact"]
            )
            return confirm_msg
        
        # 確認待ち状態
        elif current_state == "INQUIRY_CONFIRM":
            if message.lower() in ["はい", "yes", "ok", "確認", "送信"]:
                # 問い合わせIDを生成
                inquiry_id = str(uuid.uuid4())[:8]
                data["id"] = inquiry_id
                
                # 完了メッセージの生成
                complete_msg = INQUIRY_FORM["INQUIRY_COMPLETE"].format(
                    id=inquiry_id
                )
                
                # 状態をリセット
                self.reset_state(user_id)
                return complete_msg
            else:
                # キャンセルメッセージ
                self.reset_state(user_id)
                return INQUIRY_FORM["INQUIRY_CANCEL"]
        
        return "問い合わせ処理中にエラーが発生しました。「問い合わせ」と入力して最初からやり直してください。"

    def is_in_flow(self, user_id: str) -> bool:
        """ユーザーが特定のフロー中かどうかを判定する。

        Args:
            user_id: ユーザーID

        Returns:
            フロー中の場合はTrue、そうでない場合はFalse
        """
        if user_id not in self.user_states:
            return False
        
        state = self.user_states[user_id]["state"]
        return state != "INITIAL"

    def get_flow_type(self, user_id: str) -> Optional[str]:
        """ユーザーの現在のフロータイプを取得する。

        Args:
            user_id: ユーザーID

        Returns:
            フロータイプ（"VACATION"または"INQUIRY"）。フロー中でない場合はNone。
        """
        if not self.is_in_flow(user_id):
            return None
        
        state = self.user_states[user_id]["state"]
        if state.startswith("VACATION"):
            return "VACATION"
        elif state.startswith("INQUIRY"):
            return "INQUIRY"
        
        return None

    def handle_flow(self, user_id: str, message: str) -> Tuple[bool, Optional[str]]:
        """ユーザーメッセージをフローに基づいて処理する。

        Args:
            user_id: ユーザーID
            message: ユーザーのメッセージ

        Returns:
            (処理されたかどうか, 応答メッセージ)のタプル
        """
        # 「キャンセル」または「中止」コマンドの場合はフローをリセット
        if message.lower() in ["キャンセル", "中止", "cancel", "やめる", "終了"]:
            flow_type = self.get_flow_type(user_id)
            self.reset_state(user_id)
            
            if flow_type == "VACATION":
                return True, VACATION_FORM["VACATION_CANCEL"]
            elif flow_type == "INQUIRY":
                return True, INQUIRY_FORM["INQUIRY_CANCEL"]
            else:
                return True, "操作をキャンセルしました。"
        
        # 初期状態でコマンドを受け取った場合
        if not self.is_in_flow(user_id):
            if "休暇申請" in message:
                return True, self.handle_vacation_flow(user_id, message)
            elif "問い合わせ" in message:
                return True, self.handle_inquiry_flow(user_id, message)
            return False, None
        
        # 現在のフロータイプに基づいて処理
        flow_type = self.get_flow_type(user_id)
        if flow_type == "VACATION":
            return True, self.handle_vacation_flow(user_id, message)
        elif flow_type == "INQUIRY":
            return True, self.handle_inquiry_flow(user_id, message)
        
        # フロータイプが不明の場合はリセット
        self.reset_state(user_id)
        return False, None