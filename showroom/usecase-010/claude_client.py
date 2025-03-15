"""Claude 3.7 API クライアント。

Anthropic社のClaude 3.7 APIを使用するためのクライアントを提供します。
"""
import os
import json
from typing import List, Dict, Any, Optional, Tuple
import anthropic


class ClaudeClient:
    """Claude 3.7 API クライアント。

    Anthropic社のClaude 3.7 APIを使用するためのクライアントです。
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ):
        """初期化。

        Args:
            api_key: Anthropic API キー
            model: 使用するClaudeモデル名
            max_tokens: 最大トークン数（デフォルト: 1024）
            temperature: 生成時の温度パラメータ（デフォルト: 0.7）
        """
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.client = anthropic.Anthropic(api_key=api_key)

    def load_system_prompt(self, file_path: str) -> str:
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
            return "あなたはカスタマーサポートボットです。丁寧かつ簡潔に回答してください。"

    def complete(
        self, system_prompt: str, messages: List[Dict[str, str]]
    ) -> Tuple[str, Dict[str, Any]]:
        """Claude 3.7を使用してテキスト生成を行う。

        Args:
            system_prompt: システム指示
            messages: 会話履歴（形式: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]）

        Returns:
            生成されたテキストとメタデータのタプル
        """
        try:
            # メッセージリストを構築 - システムプロンプトはトップレベルのパラメータとして渡す
            formatted_messages = []
            for msg in messages:
                if msg["role"] in ["user", "assistant"]:
                    formatted_messages.append(msg)

            # Claude APIリクエスト
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,  # システムプロンプトはトップレベルのパラメータ
                messages=formatted_messages,
            )

            # レスポンスから回答を取得
            generated_text = response.content[0].text
            
            # メタデータを準備
            metadata = {
                "model": self.model,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                "stop_reason": response.stop_reason,
            }
            
            return generated_text, metadata
            
        except Exception as e:
            print(f"Claude API呼び出し中にエラーが発生しました: {e}")
            error_message = f"申し訳ありません、回答の生成中にエラーが発生しました。しばらく経ってからもう一度お試しください。"
            return error_message, {"error": str(e)}

    def handle_special_commands(self, message: str) -> Optional[str]:
        """特殊コマンドを処理する。

        一部の特殊なコマンドに対しては、Claude APIを介さずに直接応答を返します。

        Args:
            message: ユーザーのメッセージ

        Returns:
            特殊コマンド応答。特殊コマンドでない場合はNone。
        """
        message_lower = message.lower()
        
        # ヘルプコマンド
        if message_lower in ["/help", "ヘルプ", "help", "使い方"]:
            return """
【ヘルプ】テックイノベーション カスタマーサポートボット

以下のような質問にお答えできます：
・製品情報（スマートホームプロ、タスクマスター、センサーエッジ）
・価格や料金プラン
・返品・交換ポリシー
・保証とサポート情報
・会社情報（営業時間、連絡先など）

特殊コマンド：
・/help または「ヘルプ」: このヘルプメッセージを表示
・/reset または「リセット」: 会話履歴をクリア
・「オペレーターに繋いでください」: 人間のオペレーターへの転送をリクエスト

お気軽に質問してください！
"""

        # リセットコマンド
        elif message_lower in ["/reset", "リセット", "reset", "履歴削除"]:
            return "会話履歴をリセットしました。新しい会話を開始します。"

        # 特殊コマンドではない場合
        return None