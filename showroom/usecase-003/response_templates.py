"""応答テンプレート定義モジュール。

LINE WORKS Botの応答メッセージのテンプレートを定義します。
"""
import re
from typing import Dict, List, Tuple, Pattern, Callable, Any

# キーワードベースの応答テンプレート
KEYWORD_RESPONSES: Dict[str, str] = {
    "こんにちは": "こんにちは！何かお手伝いできることはありますか？",
    "hello": "こんにちは！何かお手伝いできることはありますか？",
    "おはよう": "おはようございます！今日も良い一日をお過ごしください。",
    "こんばんは": "こんばんは！お疲れ様です。",
    "さようなら": "さようなら！またいつでもご連絡ください。",
    "ありがとう": "どういたしまして！他にご質問があればいつでもどうぞ。",
    "thanks": "どういたしまして！他にご質問があればいつでもどうぞ。",
    "ヘルプ": "以下のコマンドが利用可能です：\n- 予定確認\n- 休暇申請\n- 問い合わせ\n- 営業時間",
    "help": "以下のコマンドが利用可能です：\n- 予定確認\n- 休暇申請\n- 問い合わせ\n- 営業時間",
    "予定確認": "本日の予定は次の通りです：\n10:00 朝会\n14:00 プロジェクトミーティング\n16:00 1on1",
    "休暇申請": "休暇申請を開始します。休暇を取得したい日付を教えてください（例：2025-04-01）",
    "問い合わせ": "お問い合わせ方法は以下の通りです：\n- メール: support@example.com\n- 電話: 03-1234-5678（平日9:00-18:00）",
    "営業時間": "営業時間は平日9:00-18:00です。土日祝日はお休みです。",
}

# 正規表現ベースの応答パターン
REGEX_PATTERNS: List[Tuple[Pattern, str]] = [
    (re.compile(r'予定.*(明日|あした)'), "明日の予定は次の通りです：\n11:00 チームMTG\n15:00 クライアントミーティング"),
    (re.compile(r'予定.*(今週|こんしゅう)'), "今週の主な予定は次の通りです：\n水曜日 四半期報告会\n金曜日 プロジェクト締め切り"),
    (re.compile(r'休暇.*(取得方法|とりかた|申請方法)'), "休暇の申請方法は以下の通りです：\n1. 「休暇申請」と入力\n2. 日付を入力\n3. 理由を入力\n4. 確認して承認"),
    (re.compile(r'電話.*(番号|ばんごう)'), "お問い合わせ窓口の電話番号：03-1234-5678（平日9:00-18:00）"),
    (re.compile(r'メール.*(アドレス|あどれす)'), "お問い合わせ用メールアドレス：support@example.com"),
    (re.compile(r'営業.*時間'), "営業時間は平日9:00-18:00です。土日祝日はお休みです。"),
    (re.compile(r'住所|所在地|どこ'), "本社所在地：〒100-0001 東京都千代田区千代田1-1-1"),
    (re.compile(r'(新型コロナ|コロナ|covid).*(対策|対応)'), "新型コロナウイルス対策として、以下の取り組みを行っています：\n・リモートワークの推奨\n・オフィスでの検温と消毒\n・オンライン会議の活用"),
]

# フォールバック応答（他に一致するものがない場合）
FALLBACK_RESPONSES: List[str] = [
    "申し訳ありません、よく理解できませんでした。「ヘルプ」と入力すると利用可能なコマンドが表示されます。",
    "すみません、その内容にはお応えできませんでした。他の質問がありましたらどうぞ。",
    "もう少し詳しく教えていただけますか？「ヘルプ」と入力すると、利用可能なコマンド一覧が表示されます。",
    "ご質問の意図が理解できませんでした。別の言い方で試していただけますか？",
]

# ボットの自己紹介
BOT_INTRODUCTION = """
こんにちは！私はLINE WORKS自動応答ボットです。

以下のことについてお答えできます：
- 予定確認（今日/明日/今週の予定）
- 休暇申請のサポート
- お問い合わせ先の案内
- 営業時間や住所の案内

「ヘルプ」と入力すると、いつでもコマンド一覧を表示します。
何かお手伝いできることはありますか？
"""

# 休暇申請フォームの質問
VACATION_FORM = {
    "VACATION_DATE": "休暇を取得したい日付を教えてください（例：2025-04-01）",
    "VACATION_TYPE": "休暇の種類を選択してください：\n1. 有給休暇\n2. 代休\n3. 特別休暇",
    "VACATION_REASON": "休暇の理由を簡単に教えてください",
    "VACATION_CONFIRM": "以下の内容で申請しますか？\n日付：{date}\n種類：{type}\n理由：{reason}\n（はい/いいえ）",
    "VACATION_COMPLETE": "休暇申請が完了しました。申請IDは{id}です。承認状況は「予定確認」コマンドで確認できます。",
    "VACATION_CANCEL": "申請をキャンセルしました。最初からやり直す場合は「休暇申請」と入力してください。"
}

# 休暇種類の変換マップ
VACATION_TYPE_MAP = {
    "1": "有給休暇",
    "2": "代休",
    "3": "特別休暇",
    "有給": "有給休暇",
    "代休": "代休", 
    "特別": "特別休暇",
}

# 問い合わせフォームの質問
INQUIRY_FORM = {
    "INQUIRY_CATEGORY": "お問い合わせの種類を選択してください：\n1. 製品について\n2. サービスについて\n3. その他",
    "INQUIRY_DETAIL": "お問い合わせ内容を詳しく教えてください",
    "INQUIRY_CONTACT": "ご連絡先（メールアドレスまたは電話番号）を教えてください",
    "INQUIRY_CONFIRM": "以下の内容で問い合わせを送信しますか？\n種類：{category}\n内容：{detail}\n連絡先：{contact}\n（はい/いいえ）",
    "INQUIRY_COMPLETE": "お問い合わせを受け付けました。問い合わせ番号は{id}です。担当者からご連絡いたします。",
    "INQUIRY_CANCEL": "問い合わせをキャンセルしました。最初からやり直す場合は「問い合わせ」と入力してください。"
}

# 問い合わせ種類の変換マップ
INQUIRY_CATEGORY_MAP = {
    "1": "製品について",
    "2": "サービスについて",
    "3": "その他",
    "製品": "製品について",
    "サービス": "サービスについて",
    "その他": "その他",
}