import requests
import smtplib
import time
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

GMAIL_ADDRESS = "shima091824@gmail.com"
GMAIL_APP_PASSWORD = "qpti mzvd mklk kenp"
NOTIFY_TO = "shima091824@gmail.com"
POKOTA_SELLER_ID = "p67580797"
CHECK_INTERVAL = 90

MONITOR_ITEMS = [
    {
        "name": "スリモアコーヒー",
        "url": "https://paypayfleamarket.yahoo.co.jp/search/%E3%82%B9%E3%83%AA%E3%83%A2%E3%82%A2%E3%82%B3%E3%83%BC%E3%83%92%E3%83%BC?sort=openTime&order=desc",
    },
    {
        "name": "ロートV5",
        "url": "https://paypayfleamarket.yahoo.co.jp/search/%E3%83%AD%E3%83%BC%E3%83%88V5?sort=openTime&order=desc",
    },
]

last_status = {item["name"]: None for item in MONITOR_ITEMS}

def get_search_results(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Referer": "https://paypayfleamarket.yahoo.co.jp/",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        html = resp.text
        start = html.find('<script id="__NEXT_DATA__"')
        start = html.find('>', start) + 1
        end = html.find('</script>', start)
        if start <= 0 or end <= 0:
            return []
        data = json.loads(html[start:end])
        return (
            data.get("props", {})
                .get("initialState", {})
                .get("searchState", {})
                .get("search", {})
                .get("result", {})
                .get("items", [])
        )
    except Exception as e:
        print("[ERROR] データ取得失敗: {}".format(e))
        return []

def send_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = NOTIFY_TO
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        print("[OK] メール送信: {}".format(subject))
    except Exception as e:
        print("[ERROR] メール送信失敗: {}".format(e))

def check_item(item):
    name = item["name"]
    url = item["url"]
    results = get_search_results(url)
    if not results:
        print("[{}] 結果取得失敗 - スキップ".format(name))
        return

    top = results[0]
    top_seller_id = top.get("sellerId", "")
    top_price = top.get("price", "?")
    top_title = (top.get("name") or top.get("title") or "")[:40]

    pokota_rank = None
    pokota_price = None
    for i, r in enumerate(results[:20]):
        if r.get("sellerId") == POKOTA_SELLER_ID:
            pokota_rank = i + 1
            pokota_price = r.get("price")
            break

    now = datetime.now().strftime("%H:%M:%S")
    pokota_is_first = (top_seller_id == POKOTA_SELLER_ID)
    rank_str = "1位" if pokota_is_first else ("{}位".format(pokota_rank) if pokota_rank else "圏外")

    print("[{}] {} | 1位:{} ¥{} | ポコタ:{} ¥{}".format(
        now, name, top_seller_id, top_price, rank_str, pokota_price))

    prev = last_status[name]

    if prev is None:
        last_status[name] = pokota_is_first
        if not pokota_is_first:
            send_email(
                "【{}】1位以外です！".format(name),
                "【{}】ポコタが1位ではありません\n\n現在: {}\n1位: {}\n価格: ¥{}\n商品: {}\n\n確認時刻: {}".format(
                    name, rank_str, top_seller_id, top_price, top_title, now))
        return

    if prev and not pokota_is_first:
        send_email(
            "【{}】抜かれました！".format(name),
            "【{}】ポコタが1位から落ちました\n\n現在: {}\n1位: {}\n価格: ¥{}\n商品: {}\n\n確認時刻: {}".format(
                name, rank_str, top_seller_id, top_price, top_title, now))

    elif not prev and pokota_is_first:
        send_email(
            "【{}】1位復帰！".format(name),
            "【{}】ポコタが1位に復帰しました\n\nポコタ価格: ¥{}\n\n確認時刻: {}".format(
                name, pokota_price, now))

    else:
        print("         -> ポコタ {} (変化なし)".format(rank_str))

    last_status[name] = pokota_is_first

def main():
    print("=" * 60)
    print("Yahoo!フリマ 新着順監視ツール 起動 (v4.1)")
    print("条件: 新着1位から落ちたら即通知")
    print("チェック間隔: {}秒".format(CHECK_INTERVAL))
    print("=" * 60)
    send_email(
        "監視ツール起動 (v4.1)",
        "Yahoo!フリマ監視ツールが起動しました\n\n"
        "監視対象: スリモアコーヒー、ロートV5\n"
        "監視方式: 新着順（sort=openTime&order=desc）\n"
        "チェック間隔: {}秒\n"
        "起動時刻: {}".format(CHECK_INTERVAL, datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
    )
    while True:
        for item in MONITOR_ITEMS:
            check_item(item)
            time.sleep(3)
        print("  次回チェックまで {}秒待機...\n".format(CHECK_INTERVAL))
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
