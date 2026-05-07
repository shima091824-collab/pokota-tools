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
SCAN_N = 20

MONITOR_ITEMS = [
    {
        "name": "スリモアコーヒー",
        "url": "https://paypayfleamarket.yahoo.co.jp/search/%E3%82%B9%E3%83%AA%E3%83%A2%E3%82%A2%E3%82%B3%E3%83%BC%E3%83%92%E3%83%BC?sort=openTime&order=desc",
    },
    {
        "name": "ロートV5",
        "url": "https://paypayfleamarket.yahoo.co.jp/search/%E3%83%AD%E3%83%BC%E3%83%88V5%E3%80%80%E7%B2%92?sort=openTime&order=desc",
    },
]

QTY_KEYWORDS = {
    1: ["1袋", "1個", "1本", "1箱", "単品"],
    2: ["2袋", "2個", "2本", "2箱", "×2", "x2", "２袋", "２個"],
    3: ["3袋", "3個", "3本", "3箱", "×3", "x3", "３袋", "３個"],
    4: ["4袋", "4個", "4本", "4箱", "×4", "x4", "４袋", "４個"],
}

def detect_qty(title):
    for qty, keywords in QTY_KEYWORDS.items():
        for kw in keywords:
            if kw in title:
                return qty
    return None

last_status = {
    item["name"]: {"alerted": {}, "out_of_range_alerted": False}
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
    prev = last_status[name]

    pokota_prices = {}
    pokota_found = False
    for r in results[:SCAN_N]:
        if r.get("sellerId") == POKOTA_SELLER_ID:
            pokota_found = True
            price = r.get("price")
            title = (r.get("name") or r.get("title") or "")
            qty = detect_qty(title)
            if price is not None and qty is not None:
                if qty not in pokota_prices or int(price) < pokota_prices[qty]:
                    pokota_prices[qty] = int(price)

    if not pokota_found:
        print("[{}] {} | ポコタが上位{}件圏外".format(now, name, SCAN_N))
        if not prev["out_of_range_alerted"]:
            send_email(
                "【{}】圏外警告！上位{}件から外れました".format(name, SCAN_N),
                "【{}】ポコタが上位{}件から外れました\n\n"
                "至急確認・再出品または値下げを検討してください\n\n"
                "確認時刻: {}".format(name, SCAN_N, now)
            )
            last_status[name]["out_of_range_alerted"] = True
        return

    if prev["out_of_range_alerted"]:
        send_email(
            "【{}】上位{}件に復帰しました".format(name, SCAN_N),
            "【{}】ポコタが上位{}件に戻りました\n\n"
            "確認時刻: {}".format(name, SCAN_N, now)
        )
        last_status[name]["out_of_range_alerted"] = False

    if not pokota_prices:
        print("[{}] {} | ポコタ出品あり・個数判定不可".format(now, name))
        return

    pokota_str = ", ".join("{}個:¥{:,}".format(q, p) for q, p in sorted(pokota_prices.items()))

    rivals = {}
    for r in results[:SCAN_N]:
        if r.get("sellerId") == POKOTA_SELLER_ID:
            continue
        price = r.get("price")
        title = (r.get("name") or r.get("title") or "")
        seller_id = r.get("sellerId", "不明")
        qty = detect_qty(title)
        if price is None or qty is None:
            continue
        pokota_price = pokota_prices.get(qty)
        if pokota_price is None:
            continue
        if int(price) <= pokota_price:
            if qty not in rivals:
                rivals[qty] = []
            rivals[qty].append({
                "price": int(price),
                "title": title[:40],
                "seller_id": seller_id,
            })

    rival_log = ", ".join(
        "{}個:{}件".format(q, len(v)) for q, v in sorted(rivals.items())
    ) if rivals else "なし"
    print("[{}] {} | ポコタ({}) | 脅威({}件中): {}".format(
        now, name, pokota_str, SCAN_N, rival_log))

    for qty, pokota_price in sorted(pokota_prices.items()):
        qty_rivals = rivals.get(qty, [])
        threat_exists = len(qty_rivals) > 0
        prev_alerted = prev["alerted"].get(qty, False)

        if not prev_alerted and threat_exists:
            rival_lines = "\n".join(
                "  ¥{:,}「{}」(seller: {})".format(
                    r["price"], r["title"], r["seller_id"])
                for r in qty_rivals
            )
            send_email(
                "【{}】{}個セットに競合出現！".format(name, qty),
                "【{}】{}個セットでポコタより安い or 同価格の出品があります\n\n"
                "■ ポコタ価格: ¥{:,}\n\n"
                "■ 脅威ライバル\n{}\n\n"
                "確認時刻: {}".format(name, qty, pokota_price, rival_lines, now)
            )
            last_status[name]["alerted"][qty] = True

        elif prev_alerted and not threat_exists:
            send_email(
                "【{}】{}個セットの脅威が解消しました".format(name, qty),
                "【{}】{}個セットでポコタより安い競合がいなくなりました\n\n"
                "■ ポコタ価格: ¥{:,}\n\n"
                "確認時刻: {}".format(name, qty, pokota_price, now)
            )
            last_status[name]["alerted"][qty] = False

        else:
            status_str = "脅威あり（継続中）" if threat_exists else "異常なし"
            print("         {}個セット -> {}".format(qty, status_str))

def main():
    print("=" * 60)
    print("Yahoo!フリマ 価格監視ツール 起動 (v5.3)")
    print("監視方式: {}件スキャン・個数別価格比較".format(SCAN_N))
    print("圏外警告: ポコタが上位{}件から外れたら即通知".format(SCAN_N))
    print("チェック間隔: {}秒".format(CHECK_INTERVAL))
    print("=" * 60)
    send_email(
        "監視ツール起動 (v5.3)",
        "Yahoo!フリマ価格監視ツールが起動しました\n\n"
        "監視対象: スリモアコーヒー、ロートV5\n"
        "監視方式: {}件スキャン・個数別価格比較\n"
        "圏外警告: 上位{}件から外れたら即通知\n"
        "チェック間隔: {}秒\n"
        "起動時刻: {}".format(SCAN_N, SCAN_N, CHECK_INTERVAL, datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
    )
    while True:
        for item in MONITOR_ITEMS:
            check_item(item)
            time.sleep(3)
        print("  次回チェックまで {}秒待機...\n".format(CHECK_INTERVAL))
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
