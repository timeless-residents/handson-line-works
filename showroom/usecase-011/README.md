# usecase-011: GPT-4による社内規定Q&A

LINE WORKS Bot APIとOpenAIのGPT-4を組み合わせて、社内規定や文書に関するQ&Aシステムを実装するサンプルコードです。RAG（検索拡張生成）技術を活用して、組織内の文書に基づく正確な回答を生成します。

## 概要

このユースケースでは、LINE WORKS Bot APIとGPT-4を活用して、以下の機能を持つ社内規定Q&Aシステムを実装します：

1. 社内規定、マニュアル、ポリシー文書などからの情報抽出と索引化
2. 自然言語によるクエリを理解し、最も関連性の高い情報を検索
3. RAG（検索拡張生成）を活用した正確な回答の生成
4. 回答の根拠となる文書へのリンク・引用を含めたレスポンス
5. トピック分類と自動ルーティング機能

RAG（検索拡張生成）は、生成AIのオープンエンドな生成機能と、特定データベースからの正確な情報検索を組み合わせたアプローチです。このサンプルでは、社内文書から抽出した情報をベクトルデータベースに格納し、ユーザーからの質問に対して最も関連性の高い情報を検索・提供することで、幻覚（事実でない情報の生成）を防ぎつつ正確な回答を実現します。

## 前提条件

- Python 3.9以上
- LINE WORKS アカウント（開発者向け）
- 有効なLINE WORKS Bot
- JWT認証用の秘密鍵
- OpenAI API キー（GPT-4にアクセスするため）
- ngrok（ローカル開発環境でのWebhookテスト用）
- サンプル文書（マニュアル、ポリシー文書など）

## セットアップ

1. `.env.example` ファイルをコピーして `.env` ファイルを作成します：

```bash
cp .env.example .env
```

2. `.env` ファイルを編集して、必要な環境変数を設定します：

```
# LINE WORKS API 認証情報
LINE_WORKS_CLIENT_ID=your_client_id
LINE_WORKS_CLIENT_SECRET=your_client_secret
LINE_WORKS_SERVICE_ACCOUNT=your_service_account
LINE_WORKS_BOT_NO=your_bot_id
PRIVATE_KEY_PATH=your_private_key_path
TEST_CHANNEL_ID=your_test_channel_id
CALLBACK_URL=your_webhook_url_for_callback

# サーバー設定
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
DEBUG_MODE=True

# OpenAI API設定
OPENAI_API_KEY=your_openai_api_key
EMBEDDING_MODEL=text-embedding-3-small
COMPLETION_MODEL=gpt-4
MAX_TOKENS=1024
TEMPERATURE=0.2

# RAG設定
DOCUMENT_DIR=./documents
VECTOR_DB_PATH=./vector_db
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K=5

# 会話設定
CONVERSATION_TIMEOUT_MINUTES=60
MAX_CONVERSATION_TURNS=10
```

3. 文書ディレクトリを作成し、サンプル文書を配置します：

```bash
mkdir -p documents
# サンプル文書をdocumentsディレクトリに配置
```

## 実行方法

### 1. 文書のインデックス化

まず、社内規定・文書をインデックス化して、ベクトルデータベースを作成します：

```bash
# 必要なパッケージをインストール
pip install -r requirements.txt

# 文書のインデックス化を実行
python index_documents.py
```

### 2. Webhookサーバーの起動

以下のコマンドを実行して、Webhookサーバーを起動します：

```bash
# Webhookサーバーを起動
python webhook_server.py
```

ngrokを使用してローカルサーバーを公開する場合：

```bash
# 別のターミナルでngrokを起動
ngrok http 5000

# 表示されたngrokのURLを使ってwebhook_server.pyを実行
python webhook_server.py
```

### 3. 動作確認

1. LINE WORKS Developer Consoleで、BotのWebhook URLを設定します（例：`https://your-ngrok-url.ngrok-free.app/webhook`）
2. LINE WORKS アプリでBotにメッセージを送信します（例：「出張旅費の精算方法について教えてください」）
3. サーバーがメッセージを受信し、GPT-4による回答と関連文書の引用を返します

## 主な機能

### 1. 文書のインデックス化とベクトル化

`index_documents.py` モジュールは、様々な形式（PDF、Word、Markdown、テキストなど）の文書を読み込み、前処理を行った後、OpenAIのEmbedding APIを使用してベクトル化します。これらのベクトルは検索可能なデータベースに格納されます。

```python
# 文書の読み込みと処理の例
documents = load_documents(document_dir)
chunks = split_documents(documents, chunk_size=1000, chunk_overlap=200)
embeddings = get_embeddings(chunks)
store_vector_db(embeddings, vector_db_path)
```

### 2. 意味検索とRAG

ユーザーからの質問に対して、最も関連性の高い文書チャンクを検索し、それをコンテキストとしてGPT-4に提供することで、幻覚を防ぎ正確な回答を生成します。

```python
# RAGの実装例
def generate_rag_response(question, vector_db):
    # 質問をベクトル化
    query_embedding = get_embedding(question)
    
    # 最も関連性の高いドキュメントを検索
    relevant_docs = vector_db.similarity_search(query_embedding, k=5)
    
    # コンテキストを構築
    context = "\n\n".join([doc.page_content for doc in relevant_docs])
    
    # GPT-4に質問とコンテキストを提供して回答を生成
    response = generate_response_with_context(question, context)
    
    # 引用情報を追加
    citations = [doc.metadata for doc in relevant_docs]
    response_with_citations = add_citations(response, citations)
    
    return response_with_citations
```

### 3. 引用と根拠の提示

回答には、情報源となった文書への引用が含まれます。これにより、ユーザーは回答の信頼性を確認できます。

例：
```
質問: 出張旅費の精算方法について教えてください。

回答: 出張旅費の精算は以下の手順で行います：

1. 「経費精算システム」にログインします
2. 「新規申請」→「出張費」を選択します
3. 必要情報（日付、目的、訪問先など）を入力します
4. 領収書をスキャンしてアップロードします（5,000円以上の経費には必須）
5. 上長の承認後、経理部による確認を経て精算されます

精算は出張完了後2週間以内に申請する必要があります。海外出張の場合は、為替レートの証明も添付してください。

[出典: 経費精算規程 v2.3, p.12-14, 2023年4月改訂]
```

### 4. マルチターン会話の対応

ユーザーとの会話の文脈を保持し、フォローアップ質問に対しても適切に対応します。例えば、最初の質問で「有給休暇」について尋ね、続けて「申請方法は？」とだけ質問した場合でも、有給休暇の申請方法として適切に回答できます。

### 5. 文書更新と再インデックス化

新しい文書の追加や既存文書の更新があった場合に、ベクトルデータベースを更新する機能も提供します。

```bash
# 特定の文書のみを更新
python update_index.py --file path/to/new_document.pdf

# すべての文書を再インデックス化
python update_index.py --all
```

## ディレクトリ構成

```
usecase-011/
├── README.md
├── .env.example
├── requirements.txt
├── webhook_server.py       # Webhookサーバーの実装
├── auth.py                 # LINE WORKS API認証
├── index_documents.py      # 文書のインデックス化
├── update_index.py         # インデックスの更新
├── document_processor.py   # 文書読み込みと前処理
├── vector_store.py         # ベクトルデータベース操作
├── rag_engine.py           # RAG実装
├── gpt_client.py           # OpenAI API クライアント
├── message_handler.py      # メッセージ処理ロジック
├── conversation_manager.py # 会話管理と文脈保持
├── documents/              # サンプル文書ディレクトリ
│   ├── 就業規則.pdf
│   ├── 経費精算規程.md
│   ├── 情報セキュリティポリシー.docx
│   └── 有給休暇制度.txt
└── vector_db/              # ベクトルデータベース保存先
```

## サンプル文書について

このリポジトリには以下のサンプル社内文書が含まれています：

1. **就業規則.pdf**: 勤務時間、休憩、休日、有給休暇などの基本的な就業ルール
2. **経費精算規程.md**: 交通費、出張費、接待費などの経費精算ルール
3. **情報セキュリティポリシー.docx**: 機密情報の取り扱い、パスワード管理、デバイス管理などのセキュリティポリシー
4. **有給休暇制度.txt**: 有給休暇の取得方法、計算方法、特別休暇などの詳細

これらのサンプル文書はあくまで例示用であり、実際の利用時には組織の実際の文書に置き換えてください。

## 会話シナリオ例

### シナリオ1: 有給休暇の取得方法について

```
ユーザー: 有給休暇の申請方法を教えてください。

Bot: 有給休暇の申請方法は以下の通りです：

1. 人事管理システム「HRPortal」にログインします
2. 「申請」タブから「休暇申請」を選択します
3. 休暇の種類で「年次有給休暇」を選択します
4. 取得希望日と理由（任意）を入力します
5. 申請ボタンをクリックして申請を完了します

申請は原則として取得予定日の5営業日前までに行う必要があります。急な体調不良などやむを得ない場合は、直接上長に連絡の上、事後申請も認められています。

[出典: 有給休暇制度.txt, 第3条「申請手続き」, 最終更新: 2024年1月]

ユーザー: 何日前までに申請すればいいの？

Bot: 有給休暇の申請は、原則として取得予定日の5営業日前までに行う必要があります。

ただし、急な体調不良などやむを得ない事情がある場合は、直接上長に連絡の上、事後申請も認められています。

[出典: 有給休暇制度.txt, 第3条「申請手続き」, 最終更新: 2024年1月]
```

### シナリオ2: セキュリティポリシーについての質問

```
ユーザー: 会社のパソコンで個人的なウェブサイトの閲覧は許可されていますか？

Bot: 会社のパソコンでの個人的なウェブサイト閲覧については、以下のポリシーが適用されます：

1. 業務に関係のないウェブサイトの閲覧は、休憩時間内に限り「適度な範囲」で許可されています
2. 以下のカテゴリのサイトは閲覧禁止です：
   - 成人向けコンテンツ
   - ギャンブル関連
   - 違法コンテンツ
   - マルウェアなどの高リスクサイト
3. すべてのウェブ閲覧はセキュリティ監視システムによって記録されています

また、会社のネットワークリソースを過度に消費するストリーミングサイトの利用は、業務時間内は控えるよう推奨されています。

[出典: 情報セキュリティポリシー.docx, セクション4.3「インターネット利用ポリシー」, 改訂日: 2023年8月15日]
```

## 拡張アイデア

このユースケースは以下の方向に拡張できます：

1. **マルチモーダル対応**: 画像内のテキスト認識、図表の理解能力を追加
2. **ユーザー権限レベル**: 役職や部署に応じた情報アクセス制御
3. **更新通知機能**: 関連規定が更新された場合のプッシュ通知
4. **FAQ自動生成**: よくある質問と回答の自動抽出・構築
5. **ダッシュボード**: 質問傾向分析、未カバー領域の可視化
6. **フィードバックループ**: 回答品質向上のためのフィードバック収集と学習

## トラブルシューティング

- **インデックス化エラー**:
  - 文書形式が対応しているか確認（PDF、DOCX、MD、TXTなど）
  - 文書が破損していないか確認
  - テキスト抽出時のエンコーディング問題の場合はutf-8で保存し直す

- **回答品質が低い場合**:
  - チャンクサイズを調整
  - TOP_Kパラメータを増やして参照文書数を増やす
  - TEMPERATUREを下げる（より確実性の高い回答に）

- **トークン数制限エラー**:
  - チャンクサイズを小さくする
  - TOP_Kパラメータを減らす
  - MAX_TOKENSパラメータを調整

## リファレンス

- [LINE WORKS API - Webhooks](https://developers.worksmobile.com/jp/reference/bot-webhook)
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [Vector Databases for AI Applications](https://www.pinecone.io/learn/vector-database/)
- [Retrieval-Augmented Generation](https://research.ibm.com/blog/retrieval-augmented-generation-RAG)