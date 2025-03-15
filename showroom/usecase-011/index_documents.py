#!/usr/bin/env python
"""文書インデックス化スクリプト。

社内規定や文書を読み込み、ベクトルデータベースにインデックス化します。
"""
import os
import argparse
import time
from typing import List, Dict, Any
from dotenv import load_dotenv

from langchain.docstore.document import Document
from document_processor import process_directory
from vector_store import create_vector_store_from_documents
from gpt_client import GPTClient


def main():
    """メイン実行関数。"""
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description="社内文書をインデックス化します")
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
    
    # ドキュメントディレクトリが存在するか確認
    if not os.path.exists(document_dir):
        print(f"ドキュメントディレクトリ {document_dir} が見つかりません。ディレクトリを作成します。")
        os.makedirs(document_dir)
        print("サンプル文書をダウンロードするか、文書を手動で配置してください。")
        return
    
    print(f"文書ディレクトリ: {document_dir}")
    print(f"ベクトルDB保存先: {vector_db_path}")
    print(f"チャンクサイズ: {chunk_size}")
    print(f"チャンクオーバーラップ: {chunk_overlap}")
    
    # GPTクライアントの初期化
    gpt_client = GPTClient(api_key=openai_api_key)
    
    # 開始時間を記録
    start_time = time.time()
    
    # 文書の処理とチャンク分割
    print("\n=== 文書の処理とチャンク分割 ===")
    documents = process_directory(document_dir, chunk_size, chunk_overlap)
    
    if not documents:
        print("処理する文書がありませんでした。")
        return
    
    # ドキュメント数を表示
    print(f"処理されたドキュメント数: {len(documents)}")
    
    # エンベディングの生成
    print("\n=== エンベディングの生成 ===")
    print(f"エンベディングモデル: {os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')}")
    
    document_embeddings = []
    for i, doc in enumerate(documents):
        print(f"エンベディング生成中... {i+1}/{len(documents)}", end="\r")
        embedding = gpt_client.get_embedding(doc.page_content)
        document_embeddings.append(embedding)
    
    print(f"\nエンベディング生成完了。合計: {len(document_embeddings)}")
    
    # ベクトルストアの作成と保存
    print("\n=== ベクトルストアの作成 ===")
    vector_store = create_vector_store_from_documents(documents, document_embeddings, vector_db_path)
    
    # 完了時間と処理時間を表示
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"\nインデックス化完了! 処理時間: {elapsed_time:.2f}秒")
    
    # ベクトルストアの統計を表示
    stats = vector_store.get_stats()
    print("\n=== ベクトルストア統計 ===")
    print(f"ドキュメント数: {stats['document_count']}")
    print(f"ドキュメントタイプ: {stats['document_types']}")
    print(f"ベクトル次元数: {stats['vector_dimension']}")
    
    print("\nこれでRAG機能が使えるようになりました！")
    print("webhook_server.pyを実行して、質問応答機能をテストしてください。")


if __name__ == "__main__":
    main()