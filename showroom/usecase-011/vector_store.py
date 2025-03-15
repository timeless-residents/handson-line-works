"""ベクトルストア管理モジュール。

文書のエンベディングを格納し、類似度検索を行うベクトルストアを管理します。
"""
import os
import pickle
import time
import json
import numpy as np
import faiss
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from langchain.docstore.document import Document


@dataclass
class SearchResult:
    """検索結果を表すデータクラス。"""
    document: Document
    score: float


class VectorStore:
    """文書ベクトルを格納し、類似度検索を行うクラス。"""
    
    def __init__(self, vector_dimension: int = 1536):
        """初期化。

        Args:
            vector_dimension: ベクトルの次元数（デフォルト: 1536）
        """
        self.index = faiss.IndexFlatL2(vector_dimension)  # L2距離に基づくインデックス
        self.documents: List[Document] = []
        self.document_embeddings: List[List[float]] = []
        self.dimension = vector_dimension
    
    def add_documents(self, documents: List[Document], document_embeddings: List[List[float]]) -> None:
        """文書とそのエンベディングをストアに追加する。

        Args:
            documents: 追加する文書のリスト
            document_embeddings: 文書のエンベディングのリスト
        """
        if len(documents) != len(document_embeddings):
            raise ValueError("文書数とエンベディング数が一致しません")
        
        # 既存のドキュメントとエンベディングを保存
        existing_docs = self.documents.copy()
        existing_embeddings = self.document_embeddings.copy()
        
        # 新しいドキュメントとエンベディングを追加
        self.documents.extend(documents)
        self.document_embeddings.extend(document_embeddings)
        
        # FAISSインデックスを再構築
        self.index = faiss.IndexFlatL2(self.dimension)
        if self.document_embeddings:
            self.index.add(np.array(self.document_embeddings, dtype=np.float32))
    
    def similarity_search(self, query_embedding: List[float], k: int = 5) -> List[SearchResult]:
        """クエリエンベディングに類似したドキュメントを検索する。

        Args:
            query_embedding: 検索クエリのエンベディング
            k: 返すドキュメント数（デフォルト: 5）

        Returns:
            検索結果（ドキュメントとスコア）のリスト
        """
        if not self.documents:
            return []
        
        # クエリエンベディングをNumPy配列に変換
        query_np = np.array([query_embedding], dtype=np.float32)
        
        # k個の最も近いベクトルを検索
        k = min(k, len(self.documents))
        distances, indices = self.index.search(query_np, k)
        
        # 検索結果をSearchResultとして返す
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.documents):  # インデックスが有効範囲内か確認
                result = SearchResult(
                    document=self.documents[idx],
                    score=float(1.0 / (1.0 + dist))  # スコアを正規化（距離が小さいほどスコアは大きい）
                )
                results.append(result)
        
        # スコアの降順でソート
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    def save(self, file_path: str) -> None:
        """ベクトルストアをファイルに保存する。

        Args:
            file_path: 保存先ファイルパス
        """
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # インデックス、ドキュメント、エンベディングを保存
        data = {
            "documents": self.documents,
            "document_embeddings": self.document_embeddings,
            "dimension": self.dimension,
            "timestamp": time.time()
        }
        
        # 辞書をpickleで保存
        with open(file_path, "wb") as f:
            pickle.dump(data, f)
        
        # FAISSインデックスを別ファイルに保存
        faiss.write_index(self.index, f"{file_path}.faiss")
        
        print(f"ベクトルストアを {file_path} に保存しました")
    
    @classmethod
    def load(cls, file_path: str) -> 'VectorStore':
        """ファイルからベクトルストアをロードする。

        Args:
            file_path: ロードするファイルパス

        Returns:
            ロードされたVectorStoreオブジェクト
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"ベクトルストアファイル {file_path} が見つかりません")
        
        # 辞書をロード
        with open(file_path, "rb") as f:
            data = pickle.load(f)
        
        # FAISSインデックスをロード
        index_path = f"{file_path}.faiss"
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"FAISSインデックスファイル {index_path} が見つかりません")
        
        index = faiss.read_index(index_path)
        
        # VectorStoreオブジェクトを作成
        vector_store = cls(vector_dimension=data["dimension"])
        vector_store.documents = data["documents"]
        vector_store.document_embeddings = data["document_embeddings"]
        vector_store.index = index
        
        print(f"ベクトルストアを {file_path} からロードしました（ドキュメント数: {len(vector_store.documents)}）")
        return vector_store
    
    def get_stats(self) -> Dict[str, Any]:
        """ベクトルストアの統計情報を取得する。

        Returns:
            統計情報を含む辞書
        """
        doc_types = {}
        for doc in self.documents:
            file_type = doc.metadata.get("file_type")
            if file_type:
                doc_types[file_type] = doc_types.get(file_type, 0) + 1
        
        return {
            "document_count": len(self.documents),
            "document_types": doc_types,
            "vector_dimension": self.dimension,
            "index_type": type(self.index).__name__
        }


def create_vector_store_from_documents(
    documents: List[Document], 
    document_embeddings: List[List[float]],
    vector_db_path: str
) -> VectorStore:
    """文書とエンベディングからベクトルストアを作成し保存する。

    Args:
        documents: 文書のリスト
        document_embeddings: 文書のエンベディングのリスト
        vector_db_path: ベクトルストアの保存パス

    Returns:
        作成されたVectorStoreオブジェクト
    """
    # ベクトルの次元数を取得
    dimension = len(document_embeddings[0]) if document_embeddings else 1536
    
    # ベクトルストアを作成
    vector_store = VectorStore(vector_dimension=dimension)
    vector_store.add_documents(documents, document_embeddings)
    
    # ベクトルストアを保存
    vector_store.save(vector_db_path)
    
    return vector_store


def load_or_create_vector_store(
    vector_db_path: str, 
    documents: Optional[List[Document]] = None,
    document_embeddings: Optional[List[List[float]]] = None
) -> VectorStore:
    """ベクトルストアをロードまたは作成する。

    Args:
        vector_db_path: ベクトルストアのパス
        documents: 文書のリスト（新規作成時に必要）
        document_embeddings: 文書のエンベディング（新規作成時に必要）

    Returns:
        ロードまたは作成されたVectorStoreオブジェクト
    """
    try:
        # 既存のベクトルストアをロード
        return VectorStore.load(vector_db_path)
    except (FileNotFoundError, pickle.UnpicklingError) as e:
        print(f"既存のベクトルストアをロードできませんでした: {e}")
        
        # ドキュメントとエンベディングが提供されている場合は新規作成
        if documents and document_embeddings:
            print("新しいベクトルストアを作成します")
            return create_vector_store_from_documents(documents, document_embeddings, vector_db_path)
        else:
            raise ValueError("ベクトルストアが存在せず、新規作成に必要なドキュメントとエンベディングも提供されていません")