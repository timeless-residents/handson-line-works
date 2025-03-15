# usecase-002: インタラクティブなボタン/アクション

LINE WORKS Bot APIを使用して、ボタン付きメッセージやアクションを実装するサンプルコードです。ユーザーが操作できるインタラクティブなメッセージを送信します。

## 概要

このユースケースでは、LINE WORKS Bot APIを使用して以下の種類のインタラクティブなメッセージを送信する方法を示します：

1. ボタンテンプレート - 複数のアクションボタンを含むメッセージ
2. リストテンプレート - 画像やタイトル、アクションボタンを含む複数のカラムがリスト形式で表示
3. クイックリプライ - メッセージ下部に表示される返信ボタン
4. アクションの処理 - ユーザーからのアクション応答の受信と処理

## 前提条件

- Python 3.9以上
- LINE WORKS アカウント（開発者向け）
- 有効なLINE WORKS Bot
- JWT認証用の秘密鍵

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

### インタラクティブメッセージの送信

以下のコマンドを実行して、インタラクティブメッセージを送信します：

```bash
python main.py
```

成功すると、指定したチャンネルに各種タイプのインタラクティブメッセージが送信されます。

### Webhookサーバーの起動（ngrokによる公開）

ユーザーからのアクション（ボタンクリックなど）に応答するには、Webhookサーバーを起動する必要があります。
Webhookサーバーをインターネットに公開するために、このサンプルでは「ngrok」というツールを使用します。

#### ngrokのセットアップ（初めての方向け）

1. **ngrokのインストール**

   **Macの場合:**
   ```bash
   # Homebrewを使用する場合
   brew install ngrok

   # または直接ダウンロードする場合
   # 公式サイト(https://ngrok.com/download)からダウンロードして解凍し、
   # パスの通った場所に移動します
   ```

   **Windowsの場合:**
   ```bash
   # Chocolateyを使用する場合
   choco install ngrok

   # または公式サイト(https://ngrok.com/download)からインストーラーをダウンロードして実行
   ```

   **Linux (Ubuntu/Debian)の場合:**
   ```bash
   sudo snap install ngrok
   ```

2. **ngrokアカウントの作成と認証**

   a. [ngrok.com](https://ngrok.com/)にアクセスして無料アカウントを作成します
   
   b. ログイン後、ダッシュボードにアクセスして認証トークンを取得します
   
   c. 認証トークンを使用して、ターミナルで以下のコマンドを実行します:

   ```bash
   ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE
   ```

#### Webhookサーバーの実行

以下のコマンドを実行して、ローカルにWebhookサーバーを起動し、ngrokで公開します：

```bash
# 必要なパッケージをインストール
pip install -r requirements.txt

# Webhookサーバーを起動（ngrokも自動で起動します）
python webhook_server.py
```

サーバーが起動すると、ngrokによって生成された公開URLが表示されます：

```
ngrokを起動しています（ポート 5000）...
ngrokが起動しました。公開URL: https://abcd1234.ngrok-free.app
このURLをLINE WORKS Developer ConsoleのBot WebhookURLに設定してください。
フルパス: https://abcd1234.ngrok-free.app/webhook
.envファイルにCALLBACK_URL=https://abcd1234.ngrok-free.app/webhookを保存しました。
```

#### LINE WORKS Developer ConsoleでWebhook URLを設定

1. [LINE WORKS Developer Console](https://developers.worksmobile.com/jp/console/)にログインします
2. 該当するBotの設定ページに移動します
3. 「Bot設定」タブを選択します
4. 「Webhook URL」の欄に、サーバー起動時に表示されたURLを入力します  
   （例: `https://abcd1234.ngrok-free.app/webhook`）
5. 「検証」ボタンをクリックして接続をテストします
6. 検証に成功したら「保存」ボタンをクリックします

#### 動作確認方法

1. Webhookサーバーが起動している状態で、別のターミナルを開いてメインスクリプトを実行：
   ```bash
   python main.py
   ```

2. LINE WORKS アプリでメッセージを受信し、ボタンをクリックします

3. webhook_serverを実行しているターミナルにコールバック情報が表示され、自動的に応答メッセージが送信されます

#### トラブルシューティング

- **「ngrokのURLを取得できませんでした」というエラーが表示される場合:**
  - ngrokが正しくインストールされているか確認してください
  - 認証トークンが設定されているか確認してください
  - ポート5000が他のアプリケーションで使用されていないか確認してください

- **「Webhook処理中にエラーが発生しました」というエラーが表示される場合:**
  - .envファイルの設定が正しいか確認してください
  - LINE WORKS APIの認証情報が有効か確認してください

- **Developer Consoleの「検証」ボタンでエラーになる場合:**
  - webhook_server.pyが実行中であることを確認してください
  - ngrokのURLが正しく入力されているか確認してください（末尾の/webhookを忘れないように）

- **HTTP 405エラー「Method Not Allowed」が表示される場合:**
  - Webhookサーバーが正しく設定されているか確認してください
  - 最新版のコードでは、`/webhook`エンドポイントがPOST/GET/HEADリクエストを処理できるように修正されています
  - ルートパス(`/`)へのPOSTリクエストも`/webhook`と同様に処理されるように修正されています

- **「チャンネルIDが取得できませんでした」というメッセージが表示される場合:**
  - 最新版のコードでは、チャンネルIDが取得できない場合、代わりにユーザーIDを使用して応答を送信するように修正されています
  - これにより、1:1チャット（個人チャット）での利用や、一部のポストバック処理でも正しく応答できます

> **注意**: ngrokの無料プランでは、サーバーを再起動するたびにURLが変更されます。
> その場合は、LINE WORKS Developer ConsoleのWebhook URL設定も更新する必要があります。

## 機能説明

### ボタンテンプレート送信
`send_button_template` 関数を使用して、複数のアクションボタンを含むメッセージを送信します。

```python
send_button_template(
    access_token, 
    bot_id, 
    channel_id, 
    "どのアクションを実行しますか？", 
    [
        {
            "type": "uri",
            "label": "ウェブサイトへ",
            "uri": "https://line-works.com"
        },
        {
            "type": "message",
            "label": "FAQ",
            "postback": "ButtonTemplate_FAQ"
        }
    ]
)
```

### リストテンプレート送信
`send_list_template` 関数を使用して、複数のカラムを持つリスト形式のメッセージを送信します。

```python
send_list_template(
    access_token,
    bot_id,
    channel_id,
    "https://example.com/cover.png",  # カバー画像URL
    "メインタイトル",
    "サブタイトル",
    [
        {
            "title": "アイテム1",
            "subtitle": "説明1",
            "imageUrl": "https://example.com/item1.png",
            "action": {
                "type": "uri",
                "label": "詳細",
                "uri": "https://example.com/item1"
            }
        },
        # 他のアイテム...
    ]
)
```

### クイックリプライ送信
`send_message_with_quick_reply` 関数を使用して、メッセージ下部に表示される返信ボタンを含むメッセージを送信します。

```python
send_message_with_quick_reply(
    access_token,
    bot_id,
    channel_id,
    "どのオプションを選びますか？",
    [
        {
            "imageUrl": "https://example.com/option1.png",
            "action": {
                "type": "message",
                "label": "オプション1",
                "text": "オプション1を選択"
            }
        },
        # 他のクイックリプライオプション...
    ]
)
```

### Webhookコールバック処理
`callback_handler.py` モジュールでは、ユーザーがボタンやクイックリプライを押したときのコールバック処理を実装しています。

## 注意事項

1. リストテンプレートのカラムは最大4個まで登録可能です。
2. ボタンテンプレートのボタンは最大10個まで登録可能です。
3. クイックリプライのボタンは最大13個まで登録可能です。
4. Webhook URLを設定するには、公開されたエンドポイントが必要です（例：ngrok等を使用）。

## リファレンス

- [LINE WORKS API - ボタンテンプレート](https://developers.worksmobile.com/jp/reference/bot-send-button-template)
- [LINE WORKS API - リストテンプレート](https://developers.worksmobile.com/jp/reference/bot-send-list-template)
- [LINE WORKS API - クイックリプライ](https://developers.worksmobile.com/jp/reference/bot-send-quick-reply)
- [LINE WORKS API - コールバック](https://developers.worksmobile.com/jp/reference/bot-callback)