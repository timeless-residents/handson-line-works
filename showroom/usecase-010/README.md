# usecase-010: Claude 3.7による問い合わせ対応ボット

LINE WORKS Bot APIとAnthropic社のClaude 3.7 AIを組み合わせて、高度な自然言語理解による問い合わせ対応ボットを実装するサンプルコードです。

## 概要

このユースケースでは、LINE WORKS Bot APIとClaude 3.7 APIを連携させ、以下の機能を持つ問い合わせ対応ボットを実装します：

1. ユーザーからの自然言語による質問に対する自動応答
2. 企業情報、製品情報、よくある質問などに基づいた適切な回答の生成
3. 会話の文脈を考慮した継続的な対話
4. 複雑な問い合わせや要求の理解と対応
5. 必要に応じた人間のオペレーターへのエスカレーション

Claude 3.7は高度な自然言語理解能力を持ち、人間のような対話が可能なAIモデルです。このサンプルでは、Claude 3.7の強みを活かして、シンプルなルールベースの応答システムを超えた、より柔軟で知的な顧客対応を実現します。

## 前提条件

- Python 3.9以上
- LINE WORKS アカウント（開発者向け）
- 有効なLINE WORKS Bot
- JWT認証用の秘密鍵
- Anthropic API キー（Claude 3.7にアクセスするため）
- ngrok（ローカル開発環境でのWebhookテスト用）

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

# Claude API設定
ANTHROPIC_API_KEY=your_anthropic_api_key
CLAUDE_MODEL=claude-3-7-sonnet-20240229
MAX_TOKENS=1024
TEMPERATURE=0.7

# 会話設定
CONVERSATION_TIMEOUT_MINUTES=60
MAX_CONVERSATION_TURNS=10
```

## 実行方法

### Webhookサーバーの起動

以下のコマンドを実行して、Webhookサーバーを起動します：

```bash
# 必要なパッケージをインストール
pip install -r requirements.txt

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

### 動作確認

1. LINE WORKS Developer Consoleで、BotのWebhook URLを設定します（例：`https://your-ngrok-url.ngrok-free.app/webhook`）
2. LINE WORKS アプリでBotにメッセージを送信します
3. サーバーがメッセージを受信し、Claude 3.7による応答を返します

## 主な機能

### 1. 自然言語による問い合わせ対応

Claude 3.7の強力な自然言語理解能力を活用して、ユーザーからの多様な質問や問い合わせに対応します。シンプルなキーワードマッチングではなく、質問の意図を理解し、適切な回答を生成します。

例えば、以下のような質問に自然に回答できます：
- 「返品ポリシーについて教えてください」
- 「支払い方法は何がありますか？」
- 「製品Xと製品Yの違いは何ですか？」
- 「注文した商品がまだ届きません。どうすればいいですか？」

### 2. 企業情報に基づいた回答生成

システム指示（プロンプト）に企業情報や製品情報を含めることで、Claude 3.7がその情報に基づいた正確な回答を生成します。プロンプトは `claude_prompt_templates.py` で定義され、以下の情報を含めることができます：

- 会社概要
- 製品・サービス情報
- よくある質問とその回答
- 対応ポリシーやガイドライン

### 3. 会話の文脈管理

`conversation_manager.py` モジュールが会話の履歴を管理し、Claude 3.7に過去のやり取りを含めたプロンプトを提供します。これにより、会話の文脈を考慮した自然な応答が可能になります。

```python
# 会話履歴を含めたプロンプトの例
conversation_history = conversation_manager.get_conversation_history(user_id)
prompt = create_prompt_with_history(system_prompt, conversation_history, current_message)
response = claude_client.complete(prompt)
```

### 4. 特殊コマンドと機能

一部の特殊なコマンドや要求は、事前に定義された処理で対応します：

- `/help` または「ヘルプ」: 利用可能なコマンドと機能の一覧を表示
- `/reset` または「リセット」: 会話履歴をクリアして新しい会話を開始
- 「オペレーターに繋いでください」: 人間のオペレーターへのエスカレーションをシミュレート
- 「営業時間」や「連絡先」: 基本的な企業情報を直接提供

### 5. プロアクティブな情報提供

ユーザーの質問に単に回答するだけでなく、関連する追加情報や次のステップを提案することで、より価値のある対話を実現します。

例：
```
ユーザー: 商品の返品方法を教えてください。

Bot: 商品の返品は以下の手順で行えます：
1. 注文履歴ページから該当の注文を選択
2. 「返品リクエスト」ボタンをクリック
3. 返品理由を選択して送信
4. 返送用ラベルを印刷して商品に添付
5. 指定の配送業者で返送

なお、返品は商品到着後14日以内に限り承っております。
また、返品に関連して、交換をご希望の場合は「交換」を選択いただくとよりスムーズに対応できます。
他にご質問はありますか？
```

## ディレクトリ構成

```
usecase-010/
├── README.md
├── .env.example
├── requirements.txt
├── webhook_server.py       # Webhookサーバーの実装
├── auth.py                 # LINE WORKS API認証
├── claude_client.py        # Claude 3.7 APIクライアント
├── message_handler.py      # メッセージ処理ロジック
├── conversation_manager.py # 会話管理と文脈保持
├── claude_prompt_templates.py # Claude用プロンプトテンプレート
└── escalation.py           # オペレーターへのエスカレーション機能
```

## 会話シナリオ例

### シナリオ1: 基本的な製品情報の問い合わせ

```
ユーザー: こんにちは、御社の最新製品について教えてください。

Bot: こんにちは！弊社の最新製品「スマートホームプロ」についてご案内いたします。

スマートホームプロは、家全体のIoTデバイスを一元管理できる統合システムで、以下の特徴があります：
・音声コントロール対応
・消費電力モニタリング機能
・セキュリティカメラとの連携
・スマートフォンアプリからのリモート操作

価格は標準パッケージが¥49,800（税抜）からとなっております。
詳細なカタログをご希望の場合はお送りすることも可能です。
他に何かご質問はありますか？
```

### シナリオ2: トラブルシューティング

```
ユーザー: アプリが突然クラッシュするようになりました。どうすればいいでしょうか？

Bot: アプリのクラッシュについてご不便をおかけして申し訳ありません。以下の手順をお試しいただけますか？

1. アプリを完全に終了する（タスクマネージャー/アプリ切り替え画面から強制終了）
2. デバイスを再起動する
3. アプリの最新バージョンがインストールされているか確認する
4. アプリを再インストールする

これらの手順で解決しない場合は、以下の情報をお知らせいただければ、より詳細なサポートを提供できます：
- お使いのデバイスの機種名
- OSのバージョン
- アプリのバージョン
- クラッシュが発生した状況

技術サポートチームに直接お問い合わせいただくこともできます：support@example.com
```

### シナリオ3: 複雑な質問と人間へのエスカレーション

```
ユーザー: カスタム開発について相談したいのですが、対応可能でしょうか？

Bot: カスタム開発についてのご相談ありがとうございます。弊社では企業様向けにカスタマイズされたソリューションを提供しております。

具体的なご要望やプロジェクトの規模によって対応方法が異なりますので、以下の情報をお聞かせいただけますと幸いです：
1. どのような機能やシステムが必要か
2. おおよその予算感
3. 導入希望時期
4. 現在お使いのシステムについて

より詳細なご相談は、営業担当者が直接対応させていただくのが最適かと思います。営業担当者におつなぎしますがよろしいでしょうか？

ユーザー: はい、お願いします。

Bot: かしこまりました。営業担当者へのエスカレーションをリクエストしました。営業時間（平日9:00-18:00）内であれば、通常30分以内に担当者からご連絡いたします。

[担当者への引き継ぎID: ESC-20240315-0042]

それまでの間、弊社のカスタム開発事例をご覧いただけます：
https://example.com/case-studies

お待たせして申し訳ありませんが、よろしくお願いいたします。
```

## 拡張アイデア

このユースケースは以下の方向に拡張できます：

1. ユーザー情報の統合：既存の顧客データベースと連携し、個人に合わせたより正確な回答を提供
2. マルチモーダル対応：画像認識と連携し、ユーザーが送信した画像に基づいたサポートを提供
3. 対応言語の拡張：多言語対応を追加（usecase-012との連携）
4. メトリクス収集：回答品質や対応満足度の分析機能を追加
5. ナレッジベース自動更新：会話データから新しいFAQエントリを自動生成

## トラブルシューティング

- **Claude API接続エラーの場合:**
  - API KEYが正しく設定されているか確認
  - インターネット接続を確認
  - クォータ制限に達していないか確認

- **応答が遅い場合:**
  - MAX_TOKENSパラメータを小さくしてみる
  - 会話履歴を短くする（MAX_CONVERSATION_TURNSを調整）
  - システムプロンプトを最適化

- **不適切な応答が返る場合:**
  - claude_prompt_templates.py内のシステムプロンプトを見直し、より明確なガイドラインを追加
  - 特定のトピックに関する詳細情報をシステムプロンプトに追加

## リファレンス

- [LINE WORKS API - Webhooks](https://developers.worksmobile.com/jp/reference/bot-webhook)
- [Anthropic Claude API Documentation](https://docs.anthropic.com/claude/reference/getting-started-with-the-claude-api)
- [Claude 3.7 Model Cards](https://www.anthropic.com/models)