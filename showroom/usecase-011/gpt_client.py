"""OpenAI GPT-4 API クライアント。

OpenAIのGPT-4 APIを使用するためのクライアントを提供します。
"""
import os
import json
import time
from typing import List, Dict, Any, Optional, Tuple, Union
from tenacity import retry, stop_after_attempt, wait_exponential
import openai
from openai import OpenAI


class GPTClient:
    """GPT-4 API クライアント。

    OpenAIのGPT-4 APIを使用するためのクライアントです。
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ):
        """初期化。

        Args:
            api_key: OpenAI API キー
            model: 使用するGPTモデル名（デフォルト: "gpt-4"）
            max_tokens: 最大トークン数（デフォルト: 1024）
            temperature: 生成時の温度パラメータ（デフォルト: 0.2）
        """
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.client = OpenAI(api_key=api_key)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_completion(
        self, 
        system_prompt: str, 
        messages: List[Dict[str, str]]
    ) -> Tuple[str, Dict[str, Any]]:
        """GPT-4を使用してテキスト生成を行う。

        Args:
            system_prompt: システム指示
            messages: 会話履歴（形式: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]）

        Returns:
            生成されたテキストとメタデータのタプル
        """
        try:
            # リクエストを構築
            request_messages = [{"role": "system", "content": system_prompt}]
            request_messages.extend(messages)
            
            # GPT-4 APIリクエスト
            response = self.client.chat.completions.create(
                model=self.model,
                messages=request_messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # レスポンスから回答を取得
            generated_text = response.choices[0].message.content
            
            # メタデータを構築
            metadata = {
                "model": self.model,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
                "finish_reason": response.choices[0].finish_reason
            }
            
            return generated_text, metadata
            
        except openai.APIError as e:
            print(f"OpenAI API呼び出し中にエラーが発生しました: {e}")
            error_message = f"申し訳ありません、回答の生成中にエラーが発生しました。しばらく経ってからもう一度お試しください。"
            return error_message, {"error": str(e)}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_embedding(self, text: str) -> List[float]:
        """テキストのエンベディングを取得する。

        Args:
            text: エンベディングを取得するテキスト

        Returns:
            テキストのエンベディングベクトル
        """
        try:
            # テキストを前処理
            text = text.replace("\n", " ").strip()
            
            # エンベディングリクエスト
            embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
            response = self.client.embeddings.create(
                model=embedding_model,
                input=text
            )
            
            # レスポンスからエンベディングを取得
            embedding = response.data[0].embedding
            return embedding
            
        except openai.APIError as e:
            print(f"エンベディング取得中にエラーが発生しました: {e}")
            raise e

    def handle_special_commands(self, message: str) -> Optional[str]:
        """特殊コマンドを処理する。

        一部の特殊なコマンドに対しては、GPT APIを介さずに直接応答を返します。

        Args:
            message: ユーザーのメッセージ

        Returns:
            特殊コマンド応答。特殊コマンドでない場合はNone。
        """
        message_lower = message.lower()
        
        # ヘルプコマンド
        if message_lower in ["/help", "ヘルプ", "help", "使い方"]:
            return """
【ヘルプ】社内規定Q&Aボット

このボットは、社内の規定や文書に関する質問に回答します。
以下のような質問ができます：

- 就業規則について（勤務時間、休憩、休日、有給休暇など）
- 経費精算について（交通費、出張費、接待費など）
- 情報セキュリティポリシーについて
- 有給休暇制度について（申請方法、計算方法、特別休暇など）

特殊コマンド：
- /help または「ヘルプ」: このヘルプメッセージを表示
- /reset または「リセット」: 会話履歴をクリア
- /search または「検索」: 単語で文書を直接検索
- /feedback または「フィードバック」: 回答品質についてフィードバックを送信

質問はなるべく具体的にしていただくと、より正確な回答が得られます。
お気軽に質問してください！
"""

        # リセットコマンド
        elif message_lower in ["/reset", "リセット", "reset", "履歴削除"]:
            return "会話履歴をリセットしました。新しい会話を開始します。"

        # 特殊コマンドではない場合
        return None