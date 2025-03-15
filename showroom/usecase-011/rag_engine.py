"""RAG（検索拡張生成）エンジン。

検索と生成を組み合わせて、文書に基づく高精度な回答を生成します。
"""
import os
import re
from typing import List, Dict, Any, Optional, Tuple

from langchain.docstore.document import Document
from gpt_client import GPTClient
from vector_store import VectorStore, SearchResult
from document_processor import format_citation


class RAGEngine:
    """RAG（検索拡張生成）エンジン。

    ユーザーの質問に対して、ベクトル検索で関連文書を見つけ、
    それを参考にGPT-4で回答を生成します。
    """

    def __init__(
        self,
        gpt_client: GPTClient,
        vector_store: VectorStore,
        top_k: int = 5
    ):
        """初期化。

        Args:
            gpt_client: GPTクライアント
            vector_store: ベクトルストア
            top_k: 検索結果の上位件数（デフォルト: 5）
        """
        self.gpt_client = gpt_client
        self.vector_store = vector_store
        self.top_k = top_k
    
    def search_relevant_documents(
        self, 
        query: str, 
        top_k: Optional[int] = None
    ) -> List[SearchResult]:
        """質問に関連する文書を検索する。

        Args:
            query: 検索クエリ
            top_k: 検索結果の上位件数（指定しない場合はクラス変数を使用）

        Returns:
            検索結果のリスト
        """
        top_k = top_k or self.top_k
        
        # クエリのエンベディングを取得
        query_embedding = self.gpt_client.get_embedding(query)
        
        # ベクトルストアで類似検索
        search_results = self.vector_store.similarity_search(query_embedding, k=top_k)
        
        return search_results
    
    def build_prompt_with_context(
        self, 
        query: str, 
        search_results: List[SearchResult]
    ) -> str:
        """検索結果のコンテキストを含むプロンプトを構築する。

        Args:
            query: ユーザーの質問
            search_results: 検索結果

        Returns:
            コンテキスト付きプロンプト
        """
        # システムプロンプトの基本部分
        system_prompt = """あなたは社内規定や文書に関する質問に回答するアシスタントです。
以下のコンテキスト情報を元に、ユーザーの質問に正確に回答してください。

コンテキスト情報に含まれている内容のみに基づいて回答し、含まれていない情報については「その情報はコンテキストに含まれていません」と正直に伝えてください。
回答の最後には、情報源となった文書の参照情報を含めてください。

回答の形式：
1. 質問に直接回答する
2. 必要に応じて箇条書きなどで情報を整理する
3. 回答の最後に情報源の参照情報を記載する（例: [出典: 就業規則.pdf, 最終更新: 2023年4月1日]）

以下がコンテキスト情報です：
"""
        
        # 検索結果からコンテキスト情報を構築
        context_parts = []
        for i, result in enumerate(search_results):
            doc_text = result.document.page_content.strip()
            doc_source = format_citation(result.document)
            context_parts.append(f"--- ドキュメント {i+1} ---\n{doc_text}\n{doc_source}\n")
        
        context = "\n".join(context_parts)
        
        # プロンプト全体を構築
        full_prompt = f"{system_prompt}\n\n{context}\n\n質問者からの質問に回答してください。回答は日本語でお願いします。"
        
        return full_prompt
    
    def generate_answer_with_rag(
        self, 
        query: str, 
        conversation_history: List[Dict[str, str]] = None,
        top_k: Optional[int] = None
    ) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
        """RAGを使用して質問に対する回答を生成する。

        Args:
            query: ユーザーの質問
            conversation_history: 会話履歴（デフォルト: None）
            top_k: 検索結果の上位件数（指定しない場合はクラス変数を使用）

        Returns:
            (生成された回答, 使用した文書情報のリスト, 生成メタデータ)のタプル
        """
        # 会話履歴がない場合は空リストを設定
        if conversation_history is None:
            conversation_history = []
        
        # 関連文書を検索
        search_results = self.search_relevant_documents(query, top_k)
        
        # 検索結果がない場合
        if not search_results:
            generic_answer = "申し訳ありませんが、その質問に関連する情報が見つかりませんでした。質問を変えていただくか、別のトピックについて質問してください。"
            return generic_answer, [], {"error": "No relevant documents found"}
        
        # コンテキスト情報を含むプロンプトを構築
        system_prompt = self.build_prompt_with_context(query, search_results)
        
        # 一時的な会話履歴を作成（最後の質問を追加）
        current_conversation = conversation_history.copy()
        current_conversation.append({"role": "user", "content": query})
        
        # GPT-4を使用して回答を生成
        answer, metadata = self.gpt_client.generate_completion(system_prompt, current_conversation)
        
        # 使用した文書の情報を収集
        used_documents = []
        for result in search_results:
            doc_info = result.document.metadata.copy()
            doc_info["score"] = result.score
            doc_info["content_preview"] = result.document.page_content[:100] + "..."
            used_documents.append(doc_info)
        
        return answer, used_documents, metadata
    
    def format_answer_with_citations(
        self, 
        answer: str, 
        used_documents: List[Dict[str, Any]]
    ) -> str:
        """引用情報を含む形式に回答をフォーマットする。

        Args:
            answer: 生成された回答
            used_documents: 使用した文書情報

        Returns:
            引用情報を含む形式の回答
        """
        # すでに引用が含まれている場合はそのまま返す
        if re.search(r'\[出典:', answer):
            return answer
        
        # ドキュメントの引用情報を作成
        citations = []
        for doc in used_documents[:3]:  # 上位3件まで
            file_name = doc.get("file_name", "不明なファイル")
            updated_at = doc.get("updated_at", "不明な日付")
            citations.append(f"[出典: {file_name}, 最終更新: {updated_at}]")
        
        citation_text = "\n".join(citations)
        
        # 回答に引用情報を追加
        formatted_answer = f"{answer}\n\n{citation_text}"
        
        return formatted_answer