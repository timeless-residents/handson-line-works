# usecase-003: Webhook処理の実装

LINE WORKS Bot APIを使用して、ユーザーからのメッセージに自動応答するWebhookシステムを実装するサンプルコードです。

## 概要

このユースケースでは、LINE WORKS Bot APIのWebhook機能を活用して、以下の機能を実装する方法を示します：

1. ユーザーからのメッセージを受信するWebhookサーバーの実装
2. 受信したメッセージの内容に基づいた自動応答処理
3. 複数の応答パターンとシナリオの実装：
   - キーワードベースの応答
   - 正規表現を用いたパターンマッチング
   - コンテキスト認識（会話の文脈を保持）
   - 状態管理を用いた対話フロー

## 前提条件

- Python 3.9以上
- LINE WORKS アカウント（開発者向け）
- 有効なLINE WORKS Bot
- JWT認証用の秘密鍵
- ngrok（ローカル開発環境でのWebhookテスト用）

## セットアップ

1. `.env.example` ファイルをコピーして `.env` ファイルを作成します：

```bash
cp .env.example .env
```

2. `.env` ファイルを編集して、必要な環境変数を設定します：

```
LINE_WORKS_CLIENT_ID=your_client_id
LINE_WORKS_CLIENT_SECRET=your_client_secret
LINE_WORKS_SERVICE_ACCOUNT=your_service_account
LINE_WORKS_BOT_NO=your_bot_id
PRIVATE_KEY_PATH=your_private_key_path
TEST_CHANNEL_ID=your_test_channel_id
CALLBACK_URL=your_webhook_url_for_callback
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
3. サーバーがメッセージを受信し、自動応答を返します

## 主な機能

### 1. キーワードベースの応答

特定のキーワードを含むメッセージに対して、事前に定義した応答を返します。

```python
# キーワードマッピングの例
keyword_responses = {
    "こんにちは": "こんにちは！何かお手伝いできることはありますか？",
    "ヘルプ": "以下のコマンドが利用可能です：\n- 予定確認\n- 休暇申請\n- お問い合わせ",
    "ありがとう": "どういたしまして！他にご質問があればいつでもどうぞ。"
}
```

### 2. 正規表現を用いたパターンマッチング

メッセージの内容が特定のパターンに一致する場合に、対応する応答を返します。

```python
# 正規表現パターンの例
import re

pattern_responses = [
    (re.compile(r'予定.*(確認|表示|教えて)'), "本日の予定は次の通りです：\n10:00 朝会\n14:00 プロジェクトミーティング\n16:00 1on1"),
    (re.compile(r'休暇.*(申請|取得|取る|希望)'), "休暇申請フォームはこちらです：\nhttps://example.com/vacation-form"),
    (re.compile(r'問い合わせ.*電話'), "お問い合わせ窓口の電話番号：03-1234-5678（平日9:00-18:00）")
]
```

### 3. コンテキスト認識

会話の履歴を保持し、前後の文脈を考慮した応答を可能にします。

```python
# ユーザーごとのコンテキストを管理
user_contexts = {}

def handle_with_context(user_id, message):
    # ユーザーのコンテキストを取得または初期化
    if user_id not in user_contexts:
        user_contexts[user_id] = {"last_topic": None, "conversation_count": 0}
    
    context = user_contexts[user_id]
    context["conversation_count"] += 1
    
    # 前回の話題に基づいた応答
    if context["last_topic"] == "休暇申請" and "いつ" in message:
        return "休暇は希望日の3営業日前までに申請してください。"
    
    # 新しい話題を記録
    if "休暇" in message:
        context["last_topic"] = "休暇申請"
    
    # 継続的な会話の場合
    if context["conversation_count"] > 3:
        return "他にご質問がありますか？もしなければ「終了」と入力してください。"
```

### 4. 状態管理を用いた対話フロー

フォーム入力やマルチステップの対話など、状態を持つ会話フローを実装します。

```python
# ユーザーごとの状態を管理
user_states = {}

def handle_conversation_flow(user_id, message):
    # ユーザーの状態を取得または初期化
    if user_id not in user_states:
        user_states[user_id] = {"state": "INITIAL", "data": {}}
    
    state_data = user_states[user_id]
    
    # 状態に応じた処理
    if state_data["state"] == "INITIAL":
        if "休暇申請" in message:
            state_data["state"] = "VACATION_DATE"
            return "休暇を取得したい日付を教えてください（例：2025-04-01）"
    
    elif state_data["state"] == "VACATION_DATE":
        # 日付の形式チェックなどの処理
        state_data["data"]["date"] = message
        state_data["state"] = "VACATION_REASON"
        return "休暇の理由を教えてください"
    
    elif state_data["state"] == "VACATION_REASON":
        state_data["data"]["reason"] = message
        state_data["state"] = "CONFIRM"
        date = state_data["data"]["date"]
        reason = state_data["data"]["reason"]
        return f"以下の内容で申請しますか？\n日付：{date}\n理由：{reason}\n（はい/いいえ）"
    
    elif state_data["state"] == "CONFIRM":
        if message.lower() in ["はい", "yes"]:
            # 申請処理の実行
            state_data["state"] = "INITIAL"
            return "休暇申請が完了しました。申請IDは12345です。"
        else:
            state_data["state"] = "INITIAL"
            return "申請をキャンセルしました。最初からやり直してください。"
```

## ディレクトリ構成

```
usecase-003/
├── README.md
├── .env.example
├── requirements.txt
├── webhook_server.py       # Webhookサーバーの実装
├── auth.py                 # LINE WORKS API認証
├── message_handler.py      # メッセージ処理ロジック
├── conversation.py         # 会話管理とコンテキスト
└── response_templates.py   # 応答テンプレート定義
```

## 拡張アイデア

このユースケースは以下の方向に拡張できます：

1. データベースを用いたユーザーコンテキストの永続化
2. 自然言語処理（NLP）ライブラリの導入による高度な意図検出
3. 外部APIとの連携（天気情報取得、スケジュール連携など）
4. 生成AIを活用した自動応答（usecase-010以降で実装）

## トラブルシューティング

- **Webhookからの応答がない場合:**
  - ngrokが正常に起動しているか確認
  - Developer ConsoleでWebhook URLが正しく設定されているか確認
  - webhook_server.pyのログを確認

- **認証エラーが発生する場合:**
  - .envファイルの認証情報が正しいか確認
  - 秘密鍵ファイルが正しいパスにあるか確認
  - アクセストークンの有効期限が切れていないか確認

## リファレンス

- [LINE WORKS API - Webhooks](https://developers.worksmobile.com/jp/reference/bot-webhook)
- [LINE WORKS API - メッセージ送信](https://developers.worksmobile.com/jp/reference/bot-send-message)