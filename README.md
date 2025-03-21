# LINE WORKS API × 生成AI ハンズオン

[![LINE WORKS API](https://img.shields.io/badge/LINE%20WORKS-API-00C300)](https://developers.worksmobile.com/jp/)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![Claude API](https://img.shields.io/badge/Claude-3.7-7D36EB)](https://www.anthropic.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

このリポジトリは、LINE WORKS APIと最新の生成AI技術（Claude 3.7、OpenAI GPT-4など）を連携させた実践的なユースケース集です。企業・組織のコミュニケーション改善とタスク自動化のための具体的な実装例を提供します。

## 概要

LINE WORKS は企業向けコミュニケーションプラットフォームであり、そのAPIを活用することで社内連携の効率化やサービス自動化が可能になります。本リポジトリでは、基本的な機能実装から高度なAI連携まで、段階的に学べる構成になっています：

- **基本機能実装**: LINE WORKS Bot APIの基本的な使い方（認証、メッセージ送受信、Webhook）
- **生成AI活用**: Claude 3.7やGPT-4などの大規模言語モデルを活用した実用的なソリューション
- **高度なAI連携**: マルチモーダル機能、RAG（検索拡張生成）、外部システムとの連携

各ユースケースには、詳細な説明、実行手順、カスタマイズのヒントが含まれており、すぐに実際のビジネスに応用できます。

## ユースケース一覧

本リポジトリでは、以下のユースケースを順次実装していく予定です。

### 基本機能実装（基盤構築）

| ID | ユースケース | 概要 | 対象領域 |
|----|--------------|----|----------|
| [000](showroom/usecase-000/) | LINE WORKS Bot 基本実装 | JWTを用いた認証と、LINE WORKS Bot APIを使ってメッセージを送信する基本実装 | 企業、教育機関 |
| [001](showroom/usecase-001/) | マルチモーダルメッセージ送信 | テキスト、画像、ファイル、リンク、スタンプ、カルーセルなど複数の形式でメッセージを送信 | 企業、教育機関 |
| [002](showroom/usecase-002/) | インタラクティブなボタン/アクション | ボタン付きメッセージやアクションの実装、コールバック処理、ngrokによるWebhook構成 | 企業、顧客サポート |
| [003](showroom/usecase-003/) | Webhook処理の実装 | ユーザーからのメッセージに自動応答する、会話状態管理と対話フローの実装 | 企業、カスタマーサービス |

### 生成AI活用（基本活用）

| ID | ユースケース | 概要 | 対象領域 |
|----|--------------|----|----------|
| [010](showroom/usecase-010/) | Claude 3.7による問い合わせ対応ボット | Claude 3.7を活用した高度な自然言語理解による問い合わせ対応 | 企業、カスタマーサポート |
| [011](showroom/usecase-011/) | GPT-4による社内規定Q&A | 社内規定や文書をベースにしたRAG（検索拡張生成）による質問応答 | 企業、人事、法務 |
| 012 | 多言語コミュニケーション支援 | 生成AIによる高品質な翻訳と多言語対応 | グローバル企業、国際交流 |
| 013 | 議事録自動作成 | 会議の会話を受け取り、要約と行動項目を抽出 | 企業、プロジェクト管理 |

### 高度なAI連携（発展的活用）

| ID | ユースケース | 概要 | 対象領域 |
|----|--------------|----|----------|
| 020 | Agents SDKによる複雑なタスク実行 | 複数のツールを連携させた高度なタスク実行 | 企業、開発部門 |
| 021 | RAG+Agentic AIによる知識ベース活用 | 社内文書を検索し、実行アクションを提案 | 企業、知識管理 |
| 022 | マルチモーダル入力解析と実行 | 画像・テキスト・ファイルなど複合的な入力を解析し処理 | 建設、医療、製造業 |
| 023 | ワークフロー自動化エージェント | 複数システムを連携した業務フロー自動化 | 事務、バックオフィス |

### 特定業種・業務向け（業種別活用）

| ID | ユースケース | 概要 | 対象領域 |
|----|--------------|----|----------|
| 030 | 製造業向け障害対応支援 | 設備トラブル時の原因診断と対応手順提供 | 製造業、保守部門 |
| 031 | 医療機関向け問診前確認 | 来院前の基本情報収集と整理 | 医療機関、受付業務 |
| 032 | 教育機関向け学習サポート | 学生の質問に対する教材ベースの回答提供 | 教育機関、学習支援 |
| 033 | 金融機関向け手続きガイド | 各種手続きの案内と必要書類の説明 | 金融機関、窓口業務 |

### 公共・公益向け（公共サービス活用）

| ID | ユースケース | 概要 | 対象領域 |
|----|--------------|----|----------|
| 040 | 自治体向け住民サービス案内 | 住民からの問い合わせに対する行政サービス情報提供 | 地方自治体、住民窓口 |
| 041 | 災害時情報提供支援 | 災害状況に応じた避難情報や支援情報の提供 | 自治体、防災部門 |
| 042 | 高齢者デジタル活用支援 | デジタルサービス利用に関する簡易な説明提供 | 福祉施設、地域支援 |
| 043 | 多言語住民サポート | 外国人住民への行政サービス案内の多言語対応 | 国際交流協会、窓口 |

### 発展的連携（拡張と統合）

| ID | ユースケース | 概要 | 対象領域 |
|----|--------------|----|----------|
| 050 | LINE WORKS + 社内システム連携 | 基幹システム、CRMなど社内システムとの連携 | 企業、IT部門 |
| 051 | 外部APIとLINE WORKSの統合 | 天気予報、交通情報など外部APIの情報をLINE WORKSに統合 | 企業、情報共有 |
| 052 | IoTデバイスとの連携 | 各種センサーからのデータ収集と通知 | スマートオフィス、工場 |
| 053 | データ分析とダッシュボード | 会話データの分析と可視化 | マーケティング、経営層 |

## 始め方

### 前提条件

- Python 3.9以上
- LINE WORKS アカウント（開発者向け）
- LINE WORKS Bot の設定（Bot ID、チャンネル ID、サービスアカウント、JWT 認証用の秘密鍵）
- 必要に応じて各種生成AIのAPIキー

### インストール

```bash
# リポジトリのクローン
git clone https://github.com/timeless-residents/handson-line-works.git
cd handson-line-works

# 仮想環境の作成と有効化
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate

# 必要なパッケージのインストール
pip install -r requirements.txt

# .envファイルの作成
cp .env.example .env
# .envファイルを編集して必要な環境変数を設定

# 各ユースケースのディレクトリ内にある.env.exampleも、必要に応じてコピーして設定してください
# 例: cd showroom/usecase-001 && cp .env.example .env
```

### 環境変数の設定

`.env`ファイルに以下の項目を設定します：

```
# LINE WORKS Bot API 認証情報
LINE_WORKS_CLIENT_ID=your_client_id            # Developer Consoleで発行されたクライアントID
LINE_WORKS_CLIENT_SECRET=your_client_secret    # Developer Consoleで発行されたクライアントシークレット
LINE_WORKS_SERVICE_ACCOUNT=your_service_account # サービスアカウント (例: mybot@mycompany.com)
LINE_WORKS_BOT_NO=your_bot_id                  # Bot番号 (数字のみ)
PRIVATE_KEY_PATH=path_to_your_private_key      # 秘密鍵ファイルのパス
TEST_CHANNEL_ID=your_test_channel_id           # テスト用チャンネルID

# アセット関連の設定（必要に応じて）
SAMPLE_IMAGE_PATH=path_to_sample_image.jpg     # サンプル画像のパス

# 生成AI関連のAPI設定（必要に応じて）
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
```

各ユースケースに固有の環境変数については、それぞれのディレクトリ内の`.env.example`を参照してください。

## ユースケース実行方法

各ユースケースは`showroom/usecaseXXX`ディレクトリにあります。以下のように実行します：

```bash
# 例: usecase-000の実行
cd showroom/usecase-000
python main.py

# 例: usecase-001の実行
cd showroom/usecase-001
python main.py
```

各ユースケースには独自のREADME.mdファイルがあり、詳細な説明と実行方法が記載されています。

## 開発方針

- 実用性：実際のビジネスシーンですぐに活用できるサンプル
- 学習容易性：ステップバイステップで理解しやすいコード構成
- 拡張性：自社環境に合わせてカスタマイズしやすい設計
- 持続可能性：保守しやすく長期的に活用できる実装

## トピック

このリポジトリは以下のトピックに関連しています：

- LINE WORKS API
- チャットボット開発
- 生成AI活用
- 自然言語処理
- カスタマーサポート自動化
- ビジネスプロセス自動化
- ワークフロー効率化
- Python
- Claude API
- OpenAI API

## 貢献方法

1. このリポジトリをフォーク
2. 新しいブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを開く

## ライセンス

このプロジェクトは[MITライセンス](LICENSE)の下で公開されています。

## 謝辞

- LINE WORKS API ドキュメント
- 各種生成AI提供企業（Anthropic、OpenAIなど）
- コントリビューターの皆様

## 参考リンク

- [LINE WORKS Developer Console](https://developers.worksmobile.com/jp/console/)
- [LINE WORKS API Reference](https://developers.worksmobile.com/jp/reference/)
- [LINE WORKS Bot API Guide](https://developers.worksmobile.com/jp/document/)
- [Anthropic Claude API](https://docs.anthropic.com/claude/reference/)
- [OpenAI API](https://platform.openai.com/docs/api-reference)

---

本リポジトリは教育・学習目的で提供されています。実際のビジネス利用には、LINE WORKSおよび各AIサービスの利用規約に従ってください。
