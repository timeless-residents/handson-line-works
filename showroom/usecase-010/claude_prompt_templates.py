"""Claude用プロンプトテンプレート。

Claude 3.7への指示を生成するためのテンプレートを提供します。
"""
import os
from typing import Dict, List, Any, Optional


def load_system_prompt(file_path: str) -> str:
    """システムプロンプトをファイルから読み込む。

    Args:
        file_path: システムプロンプトファイルのパス

    Returns:
        読み込んだシステムプロンプト
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"システムプロンプトの読み込みに失敗しました: {e}")
        # 基本的なシステムプロンプトをフォールバックとして返す
        return """あなたはテックイノベーション株式会社のカスタマーサポートボットです。顧客からの問い合わせに丁寧かつ簡潔に回答してください。製品情報や会社情報に基づいて正確な情報を提供し、不明な点については正直に認めてください。"""


def create_greetings_prompt() -> str:
    """初回挨拶用のプロンプトを生成する。

    Returns:
        初回挨拶用プロンプト
    """
    return """
これは新しいユーザーとの最初の会話です。以下の内容を含む挨拶メッセージを生成してください：

1. 丁寧な挨拶
2. ボットの自己紹介（テックイノベーション株式会社のカスタマーサポートボット）
3. どのようなことを質問できるかの簡単な説明（製品情報、サポート情報など）
4. 質問を促す一言

挨拶は簡潔かつ親しみやすいトーンで作成してください。
"""


def create_escalation_prompt(escalation_keywords: List[str], message: str) -> str:
    """エスカレーション判定用のプロンプトを生成する。

    Args:
        escalation_keywords: エスカレーションキーワードリスト
        message: ユーザーメッセージ

    Returns:
        エスカレーション判定用プロンプト
    """
    return f"""
以下のユーザーメッセージを分析し、人間のオペレーターへのエスカレーションが必要かどうかを判断してください：

ユーザーメッセージ: "{message}"

エスカレーションが必要と判断される特徴：
1. ユーザーが直接オペレーターへの転送を要求している（例: "オペレーターに繋いでください"）
2. 複雑な問題で、自動応答では十分に対応できない
3. 契約や支払いに関する詳細情報が必要
4. ユーザーが明らかに不満を示している
5. 複数回の質問に適切に回答できていない状況

エスカレーションを示唆するキーワード: {", ".join(escalation_keywords)}

回答は "ESCALATE" または "CONTINUE" のみとしてください。理由や説明は不要です。
"""


def create_short_summary_prompt(conversation_history: List[Dict[str, Any]]) -> str:
    """会話の要約プロンプトを生成する。

    Args:
        conversation_history: 会話履歴

    Returns:
        会話要約用プロンプト
    """
    conversation_text = ""
    for msg in conversation_history:
        role = "ユーザー" if msg["role"] == "user" else "ボット"
        conversation_text += f"{role}: {msg['content']}\n\n"
    
    return f"""
以下の会話履歴を50語以内で簡潔に要約してください。主な話題とユーザーの主要な関心事に焦点を当ててください。

会話履歴:
{conversation_text}

会話の要約を箇条書きで3点以内にまとめてください。
"""


def create_topic_detection_prompt(message: str) -> str:
    """トピック検出用のプロンプトを生成する。

    Args:
        message: ユーザーメッセージ

    Returns:
        トピック検出用プロンプト
    """
    return f"""
以下のユーザーメッセージを分析し、どのトピックについての質問か判断してください：

ユーザーメッセージ: "{message}"

以下のトピックから最も関連性の高いものを1つだけ選択してください：
- PRODUCT_INFO（製品情報）
- PRICING（価格・料金）
- SUPPORT（技術サポート・トラブルシューティング）
- RETURN_POLICY（返品・交換）
- WARRANTY（保証）
- COMPANY_INFO（会社情報）
- GENERAL_INQUIRY（一般的な問い合わせ）
- OTHER（その他）

回答はトピック名のみとしてください。理由や説明は不要です。
"""