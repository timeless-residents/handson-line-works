# usecase-001: マルチモーダルメッセージ送信

LINE WORKS Bot APIを使用して、テキスト、画像、ファイル、リンク、スタンプ、カルーセルなど複数の形式でメッセージを送信するサンプルコードです。

## 概要

このユースケースでは、LINE WORKS Bot APIを使用して以下の種類のメッセージを送信する方法を示します：

1. テキストメッセージ - 単純なテキストメッセージ
2. 画像メッセージ - 画像ファイルを送信
3. ファイルメッセージ - 任意のファイルを送信
4. リンクメッセージ - サムネイル付きのリンク
5. スタンプメッセージ - LINE WORKSスタンプ
6. カルーセルメッセージ - 複数の項目を横スクロールで表示

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
SAMPLE_IMAGE_PATH=path_to_sample_image.jpg
```

* `SAMPLE_IMAGE_PATH`には、送信したいサンプル画像のパスを設定します。
* サンプルファイルは自動的に生成されるため、特別な設定は不要です。

## 実行方法

以下のコマンドを実行します：

```bash
python main.py
```

成功すると、指定したチャンネルに各種タイプのメッセージが送信されます。

## 機能説明

### テキストメッセージ送信
`send_text_message` 関数を使用して、単純なテキストメッセージを送信します。

```python
send_text_message(access_token, bot_id, channel_id, "こんにちは！")
```

### 画像メッセージ送信
`send_image_message` 関数を使用して、画像ファイルをメッセージとして送信します。

```python
send_image_message(access_token, bot_id, channel_id, "path/to/image.jpg")
```

### ファイルメッセージ送信
`send_file_message` 関数を使用して、任意のファイルを送信します。

```python
send_file_message(access_token, bot_id, channel_id, "path/to/file.pdf")
```

### リンクメッセージ送信
`send_link_message` 関数を使用して、サムネイル付きのリンクメッセージを送信します。

```python
send_link_message(
    access_token, 
    bot_id, 
    channel_id, 
    "タイトル", 
    "説明文", 
    "https://example.com",
    "https://example.com/thumbnail.jpg"  # サムネイル画像URL（オプション）
)
```

### スタンプメッセージ送信
`send_stamp_message` 関数を使用して、LINE WORKSのスタンプを送信します。

```python
send_stamp_message(access_token, bot_id, channel_id, "1", "1")
```

### カルーセルメッセージ送信
`send_carousel_message` 関数を使用して、複数の項目を含むカルーセルメッセージを送信します。

```python
carousel_columns = [
    {
        "title": "項目1",
        "text": "説明文1",
        "thumbnailImageUrl": "https://example.com/image1.jpg",
        "actions": [
            {
                "type": "uri",
                "label": "詳細を見る",
                "uri": "https://example.com/page1"
            }
        ]
    },
    {
        "title": "項目2",
        "text": "説明文2",
        "thumbnailImageUrl": "https://example.com/image2.jpg",
        "actions": [
            {
                "type": "uri",
                "label": "ウェブサイトへ",
                "uri": "https://example.com/page2"
            }
        ]
    }
]

send_carousel_message(access_token, bot_id, channel_id, carousel_columns)
```

## 注意事項

1. 大きなファイルや画像を送信する場合は、APIのサイズ制限に注意してください。
2. スタンプIDは事前にLINE WORKSで確認する必要があります。
3. カルーセルメッセージはモバイルデバイスでの表示に最適化されています。

## リファレンス

- [LINE WORKS API - Bot メッセージ送信](https://developers.worksmobile.com/jp/reference/bot-send-message-v3)
- [LINE WORKS API - メッセージタイプ](https://developers.worksmobile.com/jp/reference/bot-send-content)