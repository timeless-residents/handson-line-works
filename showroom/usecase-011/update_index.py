#!/usr/bin/env python
"""インデックス更新スクリプト。

追加または変更された文書をベクトルデータベースに追加します。
"""
import os
import argparse
import time
from typing import List, Dict, Any
from dotenv import load_dotenv

from langchain.docstore.document import Document
from document_processor import process_document, process_directory
from vector_store import load_or_create_vector_store, VectorStore
from gpt_client import GPTClient


def update_specific_document(
    file_path: str,
    vector_store: VectorStore,
    gpt_client: GPTClient,
    chunk_size: int,
    chunk_overlap: int,
    vector_db_path: str
) -> None:
    """特定の文書をインデックスに更新/追加する。

    Args:
        file_path: 文書ファイルのパス
        vector_store: ベクトルストア
        gpt_client: GPTクライアント
        chunk_size: チャンクサイズ
        chunk_overlap: チャンクオーバーラップ
        vector_db_path: ベクトルDBのパス
    """
    print(f"文書を処理中: {file_path}")
    
    # 文書を処理
    documents = process_document(file_path, chunk_size, chunk_overlap)
    if not documents:
        print("文書の処理中にエラーが発生しました。")
        return
    
    # エンベディングを生成
    document_embeddings = []
    for i, doc in enumerate(documents):
        print(f"エンベディング生成中... {i+1}/{len(documents)}", end="\r")
        embedding = gpt_client.get_embedding(doc.page_content)
        document_embeddings.append(embedding)
    
    print(f"\nエンベディング生成完了。合計: {len(document_embeddings)}")
    
    # 同じファイルのドキュメントを削除（既存の場合）
    filtered_docs = []
    filtered_embeddings = []
    for i, doc in enumerate(vector_store.documents):
        if doc.metadata.get("source") != file_path:
            filtered_docs.append(doc)
            filtered_embeddings.append(vector_store.document_embeddings[i])
    
    # 新しい文書とエンベディングを追加
    filtered_docs.extend(documents)
    filtered_embeddings.extend(document_embeddings)
    
    # ベクトルストアを再作成
    updated_vector_store = VectorStore(vector_dimension=vector_store.dimension)
    updated_vector_store.add_documents(filtered_docs, filtered_embeddings)
    
    # 更新したベクトルストアを保存
    updated_vector_store.save(vector_db_path)
    
    print(f"インデックスに文書を更新しました: {file_path}")
    print(f"更新後のドキュメント数: {len(filtered_docs)}")


def main():
    """メイン実行関数。"""
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description="インデックス更新スクリプト")
    parser.add_argument("--file", help="更新する特定の文書ファイルのパス")
    parser.add_argument("--all", action="store_true", help="すべての文書を再インデックス化")
    parser.add_argument("--document_dir", help="文書ディレクトリのパス")
    parser.add_argument("--vector_db", help="ベクトルデータベースのパス")
    parser.add_argument("--chunk_size", type=int, default=None, help="チャンクサイズ")
    parser.add_argument("--chunk_overlap", type=int, default=None, help="チャンクオーバーラップ")
    args = parser.parse_args()
    
    # .env ファイルから環境変数を読み込む
    load_dotenv()
    
    # 引数の取得（コマンドライン引数 > 環境変数 > デフォルト値）
    document_dir = args.document_dir or os.getenv("DOCUMENT_DIR") or "./documents"
    vector_db_path = args.vector_db or os.getenv("VECTOR_DB_PATH") or "./vector_db"
    chunk_size = args.chunk_size or int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap = args.chunk_overlap or int(os.getenv("CHUNK_OVERLAP", "200"))
    
    # OpenAI API キーを取得
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("ERROR: OPENAI_API_KEY環境変数が設定されていません")
        return
    
    # GPTクライアントの初期化
    gpt_client = GPTClient(api_key=openai_api_key)
    
    # 開始時間を記録
    start_time = time.time()
    
    # すべての文書を再インデックス化する場合
    if args.all:
        print("すべての文書を再インデックス化します...")
        # 完全に新しいインデックスを作成
        documents = process_directory(document_dir, chunk_size, chunk_overlap)
        
        if not documents:
            print("処理する文書がありませんでした。")
            return
        
        # エンベディングを生成
        document_embeddings = []
        for i, doc in enumerate(documents):
            print(f"エンベディング生成中... {i+1}/{len(documents)}", end="\r")
            embedding = gpt_client.get_embedding(doc.page_content)
            document_embeddings.append(embedding)
        
        print(f"\nエンベディング生成完了。合計: {len(document_embeddings)}")
        
        # 新しいベクトルストアを作成
        vector_store = VectorStore()
        vector_store.add_documents(documents, document_embeddings)
        vector_store.save(vector_db_path)
        
        print(f"すべての文書を再インデックス化しました。ドキュメント数: {len(documents)}")
    
    # 特定の文書のみを更新する場合
    elif args.file:
        file_path = os.path.abspath(args.file)
        if not os.path.exists(file_path):
            print(f"エラー: ファイル {file_path} が見つかりません")
            return
        
        try:
            # 既存のベクトルストアをロード
            vector_store = VectorStore.load(vector_db_path)
            
            # ファイルを更新
            update_specific_document(
                file_path, vector_store, gpt_client, chunk_size, chunk_overlap, vector_db_path
            )
            
        except FileNotFoundError:
            print(f"ベクトルストアが見つかりません。まずindex_documents.pyを実行してください。")
            return
    
    else:
        print("エラー: --file または --all オプションを指定してください")
        return
    
    # 完了時間と処理時間を表示
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"\n更新完了! 処理時間: {elapsed_time:.2f}秒")


if __name__ == "__main__":
    main()