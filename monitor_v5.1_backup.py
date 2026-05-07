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
TOP_N = 8

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

last_status = {
    item["name"]: {"alerted": False, "out_of_range_alerted": False, "pokota_prices": []}
    for item in MONITOR_ITEMS
}

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

    now = datetime.now().strftime("%H:%M:%S")

    pokota_listings = []
    pokota_rank = None
    for i, r in enumerate(results[:TOP_N]):
        if r.get("sellerId") == POKOTA_SELLER_ID:
            price = r.get("price")
            title = (r.get("name") or r.get("title") or "")[:40]
            if price is not None:
                pokota_listings.append({"price": int(price), "title": title})
            if pokota_rank is None:
                pokota_rank = i + 1

    prev = last_status[name]

    if not pokota_listings:
        print("[{}] {} | ポコタが上位{}件圏外".format(now, name, TOP_N))
        if not prev["out_of_range_alerted"]:
            send_email(
                "【{}】圏外警告！上位{}件から外れました".format(name, TOP_N),
                "【{}】ポコタが上位{}件から外れました\n\n"
                "至急確認・再出品または値下げを検討してください\n\n"
                "確認時刻: {}".format(name, TOP_N, now)
            )
            last_status[name]["out_of_range_alerted"] = True
        return

    if prev["out_of_range_alerted"]:
        send_email(
            "【{}】上位{}件に復帰しました".format(name, TOP_N),
            "【{}】ポコタが上位{}件に戻りました\n\n"
            "現在 {}位\n\n"
            "確認時刻: {}".format(name, TOP_N, pokota_rank, now)
        )
        last_status[name]["out_of_range_alerted"] = False

    pokota_min_price = min(p["price"] for p in pokota_listings)
    pokota_prices_str = ", ".join("¥{:,}".format(p["price"]) for p in pokota_listings)

    rivals_in_top = []
    for i, r in enumerate(results[:TOP_N]):
        if r.get("sellerId") == POKOTA_SELLER_ID:
            continue
        price = r.get("price")
        title = (r.get("name") or r.get("title") or "")[:40]
        seller_id = r.get("sellerId", "不明")
        if price is not None and int(price) <= pokota_min_price:
            rivals_in_top.append({
                "rank": i + 1,
                "price": int(price),
                "title": title,
                "seller_id": seller_id,
            })

    rival_summary = ", ".join(
        "{}位:¥{:,}({})".format(r["rank"], r["price"], r["title"][:15])
        for r in rivals_in_top
    ) if rivals_in_top else "なし"
    print("[{}] {} | ポコタ{}位 最安:{} | 脅威ライバル(上位{}件): {}".format(
        now, name, pokota_rank, pokota_prices_str, TOP_N, rival_summary))

    threat_exists = len(rivals_in_top) > 0

    if not prev["alerted"] and threat_exists:
        rival_lines = "\n".join(
            "  {}位 ¥{:,}「{}」(seller: {})".format(
                r["rank"], r["price"], r["title"], r["seller_id"])
            for r in rivals_in_top
        )
        send_email(
            "【{}】値下げ競合が上位{}件以内に出現！".format(name, TOP_N),
            "【{}】ポコタより安い or 同価格の出品が上位{}件に現れました\n\n"
            "■ ポコタ現在価格\n  {}\n"
            "■ ポコタ順位: {}位\n\n"
            "■ 脅威ライバル\n{}\n\n"
            "確認時刻: {}".format(name, TOP_N, pokota_prices_str, pokota_rank, rival_lines, now)
        )
        last_status[name]["alerted"] = True
    elif prev["alerted"] and not threat_exists:
        send_email(
            "【{}】脅威ライバルが解消しました".format(name),
            "【{}】ポコタより安い競合が上位{}件から消えました\n\n"
            "■ ポコタ現在価格\n  {}\n"
            "■ ポコタ順位: {}位\n\n"
            "確認時刻: {}".format(name, TOP_N, pokota_prices_str, pokota_rank, now)
        )
        last_status[name]["alerted"] = False
    else:
        status_str = "脅威あり（継続中）" if threat_exists else "異常なし"
        print("         -> {} (変化なし)".format(status_str))

    last_status[name]["pokota_prices"] = [p["price"] for p in pokota_listings]

def main():
    print("=" * 60)
    print("Yahoo!フリマ 価格監視ツール 起動 (v5.1)")
    print("監視条件: 上位{}件にポコタより安い or 同価格の出品が出たら通知".format(TOP_N))
    print("圏外警告: ポコタが上位{}件から外れたら即通知".format(TOP_N))
    print("チェック間隔: {}秒".format(CHECK_INTERVAL))
    print("=" * 60)
    send_email(
        "監視ツール起動 (v5.1)",
        "Yahoo!フリマ価格監視ツールが起動しました\n\n"
        "監視対象: スリモアコーヒー、ロートV5\n"
        "監視方式: 上位{}件に自分以下の価格が出たら通知\n"
        "圏外警告: 上位{}件から外れたら即通知\n"
        "チェック間隔: {}秒\n"
        "起動時刻: {}".format(TOP_N, TOP_N, CHECK_INTERVAL, datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
    )
    while True:
        for item in MONITOR_ITEMS:
            check_item(item)
            time.sleep(3)
        print("  次回チェックまで {}秒待機...\n".format(CHECK_INTERVAL))
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
