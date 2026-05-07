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
        "default_qty": 1,
    },
    {
        "name": "ロートV5",
        "url": "https://paypayfleamarket.yahoo.co.jp/search/%E3%83%AD%E3%83%BC%E3%83%88V5%E3%80%80%E7%B2%92?sort=openTime&order=desc",
        "default_qty": None,
    },
    {
        "name": "ラクトロン60錠",
        "url": "https://paypayfleamarket.yahoo.co.jp/search/%E3%83%A9%E3%82%AF%E3%83%88%E3%83%AD%E3%83%B3%E3%80%8060%E9%8C%A0?sort=openTime&order=desc",
        "default_qty": 1,
        "check_interval": 180,
    },
    {
        "name": "アパコート",
        "url": "https://paypayfleamarket.yahoo.co.jp/search/%E3%82%A2%E3%83%91%E3%82%B3%E3%83%BC%E3%83%88%E3%80%80%E3%83%A4%E3%82%AF%E3%83%AB%E3%83%88?sort=openTime&order=desc",
        "default_qty": 1,
        "check_interval": 180,
    },
    {
        "name": "wの健康青汁プラス",
        "url": "https://paypayfleamarket.yahoo.co.jp/search/w%E3%81%AE%E5%81%A5%E5%BA%B7%E9%9D%92%E6%B1%81%E3%80%80%E3%83%97%E3%83%A9%E3%82%B9?sort=openTime&order=desc",
        "default_qty": 1,
        "check_interval": 180,
    },
    {
        "name": "えいようかん",
        "url": "https://paypayfleamarket.yahoo.co.jp/search/%E3%81%88%E3%81%84%E3%82%88%E3%81%86%E3%81%8B%E3%82%93?sort=openTime&order=desc",
        "default_qty": 1,
        "check_interval": 180,
    },
    {
        "name": "ヒハツ＆ギャバの恵み 和漢の森",
        "url": "https://paypayfleamarket.yahoo.co.jp/search/%E3%83%92%E3%83%8F%E3%83%84%E3%80%80%E3%82%AE%E3%83%A3%E3%83%90%E3%80%80%E6%81%B5%E3%81%BF?sort=openTime&order=desc",
        "default_qty": 1,
        "check_interval": 180,
    },
    {
        "name": "桑の葉＆茶カテキンの恵み 和漢の森",
        "url": "https://paypayfleamarket.yahoo.co.jp/search/%E6%A1%91%E3%81%AE%E8%91%89%E3%80%80%E3%82%AB%E3%83%86%E3%82%AD%E3%83%B3?sort=openTime&order=desc",
        "default_qty": 1,
        "check_interval": 180,
    },
    {
        "name": "リンクルストレッチ",
        "url": "https://paypayfleamarket.yahoo.co.jp/search/%E3%83%AA%E3%83%B3%E3%82%AF%E3%83%AB%E3%82%B9%E3%83%88%E3%83%AC%E3%83%83%E3%83%81?sort=openTime&order=desc",
        "default_qty": None,
        "check_interval": 180,
    },
]

QTY_KEYWORDS = {
    1: ["1袋", "1個", "1本", "1箱", "単品", "１袋", "１個", "１本", "１箱"],
    2: ["2袋", "2個", "2本", "2箱", "×2", "x2", "２袋", "２個", "２本", "２箱"],
    3: ["3袋", "3個", "3本", "3箱", "×3", "x3", "３袋", "３個", "３本", "３箱"],
    4: ["4袋", "4個", "4本", "4箱", "×4", "x4", "４袋", "４個", "４本", "４箱"],
}

def detect_qty(title, default_qty=None):
    for qty, keywords in QTY_KEYWORDS.items():
        for kw in keywords:
            if kw in title:
                return qty
    return default_qty

last_status = {
    item["name"]: {
        "alerted": {},
        "rank_alerted": {},
        "top1_alerted": {},
        "out_of_range_alerted": False
    }
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
    default_qty = item.get("default_qty")
    results = get_search_results(url)
    if not results:
        print("[{}] 結果取得失敗 - スキップ".format(name))
        return

    now = datetime.now().strftime("%H:%M:%S")
    prev = last_status[name]

    pokota_prices = {}
    pokota_ranks = {}
    pokota_found = False
    for i, r in enumerate(results[:SCAN_N]):
        if r.get("sellerId") == POKOTA_SELLER_ID:
            pokota_found = True
            price = r.get("price")
            title = (r.get("name") or r.get("title") or "")
            qty = detect_qty(title, default_qty)
            if price is not None and qty is not None:
                if qty not in pokota_prices or int(price) < pokota_prices[qty]:
                    pokota_prices[qty] = int(price)
                    pokota_ranks[qty] = i + 1

    if not pokota_found:
        print("[{}] {} | ポコタが上位{}件圏外".format(now, name, SCAN_N))
        if not prev["out_of_range_alerted"]:
            send_email(
                "【{}】圏外警告！上位{}件から外れました".format(name, SCAN_N),
                "【{}】ポコタが上位{}件から外れました\n\n至急確認・再出品または値下げを検討してください\n\n確認時刻: {}".format(name, SCAN_N, now)
            )
            last_status[name]["out_of_range_alerted"] = True
        return

    if prev["out_of_range_alerted"]:
        send_email(
            "【{}】上位{}件に復帰しました".format(name, SCAN_N),
            "【{}】ポコタが上位{}件に戻りました\n\n確認時刻: {}".format(name, SCAN_N, now)
        )
        last_status[name]["out_of_range_alerted"] = False

    if not pokota_prices:
        print("[{}] {} | ポコタ出品あり・個数判定不可".format(now, name))
        return

    pokota_str = ", ".join("{}個:¥{:,}({}位)".format(q, p, pokota_ranks.get(q, "?")) for q, p in sorted(pokota_prices.items()))

    rivals_cheap = {}
    rivals_higher = {}
    rivals_top1 = {}

    top1 = results[0] if results else None
    top1_seller = top1.get("sellerId", "") if top1 else ""
    top1_title = (top1.get("name") or top1.get("title") or "") if top1 else ""
    top1_price = top1.get("price") if top1 else None
    top1_qty = detect_qty(top1_title, default_qty) if top1 else None

    for i, r in enumerate(results[:SCAN_N]):
        if r.get("sellerId") == POKOTA_SELLER_ID:
            continue
        price = r.get("price")
        title = (r.get("name") or r.get("title") or "")
        seller_id = r.get("sellerId", "不明")
        qty = detect_qty(title, default_qty)
        if price is None or qty is None:
            continue
        pokota_price = pokota_prices.get(qty)
        pokota_rank = pokota_ranks.get(qty)
        if pokota_price is None or pokota_rank is None:
            continue
        rival_rank = i + 1
        if int(price) <= pokota_price:
            if qty not in rivals_cheap:
                rivals_cheap[qty] = []
            rivals_cheap[qty].append({"rank": rival_rank, "price": int(price), "title": title[:40], "seller_id": seller_id})
        elif int(price) > pokota_price and rival_rank < pokota_rank:
            if qty not in rivals_higher:
                rivals_higher[qty] = []
            rivals_higher[qty].append({"rank": rival_rank, "price": int(price), "title": title[:40], "seller_id": seller_id, "price_diff": int(price) - pokota_price})

    if top1_seller != POKOTA_SELLER_ID and top1_qty is not None and top1_qty in pokota_prices:
        rivals_top1[top1_qty] = {"price": int(top1_price) if top1_price else 0, "title": top1_title[:40], "seller_id": top1_seller}

    cheap_log = ", ".join("{}個:{}件".format(q, len(v)) for q, v in sorted(rivals_cheap.items())) if rivals_cheap else "なし"
    higher_log = ", ".join("{}個:{}件".format(q, len(v)) for q, v in sorted(rivals_higher.items())) if rivals_higher else "なし"
    top1_log = ", ".join("{}個".format(q) for q in sorted(rivals_top1.keys())) if rivals_top1 else "ポコタ"
    print("[{}] {} | ポコタ({}) | 安値:{} | 高値上位:{} | 1位:{}".format(now, name, pokota_str, cheap_log, higher_log, top1_log))

    for qty, pokota_price in sorted(pokota_prices.items()):
        qty_rivals = rivals_cheap.get(qty, [])
        threat_exists = len(qty_rivals) > 0
        prev_alerted = prev["alerted"].get(qty, False)
        if not prev_alerted and threat_exists:
            rival_lines = "\n".join("  {}位 ¥{:,}「{}」(seller: {})".format(r["rank"], r["price"], r["title"], r["seller_id"]) for r in qty_rivals)
            send_email("【{}】{}個セットに競合出現！".format(name, qty),
                "【{}】{}個セットでポコタより安い or 同価格の出品があります\n\n■ ポコタ価格: ¥{:,}（{}位）\n\n■ 脅威ライバル\n{}\n\n確認時刻: {}".format(name, qty, pokota_price, pokota_ranks.get(qty, "?"), rival_lines, now))
            last_status[name]["alerted"][qty] = True
        elif prev_alerted and not threat_exists:
            last_status[name]["alerted"][qty] = False
        else:
            print("         {}個セット(安値) -> {}".format(qty, "脅威あり（継続中）" if threat_exists else "異常なし"))

    for qty, pokota_price in sorted(pokota_prices.items()):
        qty_rivals = rivals_higher.get(qty, [])
        threat_exists = len(qty_rivals) > 0
        prev_alerted = prev["rank_alerted"].get(qty, False)
        if not prev_alerted and threat_exists:
            rival_lines = "\n".join("  {}位 ¥{:,}（+¥{}高い）「{}」(seller: {})".format(r["rank"], r["price"], r["price_diff"], r["title"], r["seller_id"]) for r in qty_rivals)
            send_email("【{}】{}個セットで高値競合が上位に！".format(name, qty),
                "【{}】{}個セットでポコタより高い価格なのに上位に表示されています\n\n■ ポコタ価格: ¥{:,}（{}位）\n\n■ 高値上位ライバル\n{}\n\n※1円値下げ→戻しで順位リフレッシュを検討してください\n\n確認時刻: {}".format(name, qty, pokota_price, pokota_ranks.get(qty, "?"), rival_lines, now))
            last_status[name]["rank_alerted"][qty] = True
        elif prev_alerted and not threat_exists:
            last_status[name]["rank_alerted"][qty] = False
        else:
            print("         {}個セット(高値上位) -> {}".format(qty, "脅威あり（継続中）" if threat_exists else "異常なし"))

    for qty, pokota_price in sorted(pokota_prices.items()):
        rival = rivals_top1.get(qty)
        threat_exists = rival is not None
        prev_alerted = prev["top1_alerted"].get(qty, False)
        if not prev_alerted and threat_exists:
            send_email("【{}】{}個セットの新着1位を取られました！".format(name, qty),
                "【{}】{}個セットでポコタが新着1位ではありません\n\n■ ポコタ価格: ¥{:,}（{}位）\n\n■ 新着1位\n  ¥{:,}「{}」(seller: {})\n\n確認時刻: {}".format(name, qty, pokota_price, pokota_ranks.get(qty, "?"), rival["price"], rival["title"], rival["seller_id"], now))
            last_status[name]["top1_alerted"][qty] = True
        elif prev_alerted and not threat_exists:
            last_status[name]["top1_alerted"][qty] = False
        else:
            print("         {}個セット(1位) -> {}".format(qty, "1位以外（継続中）" if threat_exists else "1位キープ"))

def main():
    print("=" * 60)
    print("Yahoo!フリマ 価格監視ツール 起動 (v5.10)")
    print("監視①: 同額以下の競合が出たら通知")
    print("監視②: 高値なのにポコタより上位の競合が出たら通知")
    print("監視③: 新着1位を取られたら通知")
    print("圏外警告: ポコタが上位{}件から外れたら即通知".format(SCAN_N))
    print("チェック間隔: {}秒".format(CHECK_INTERVAL))
    print("=" * 60)
    send_email(
        "監視ツール起動 (v5.10)",
        "Yahoo!フリマ価格監視ツールが起動しました\n\n"
        "監視対象: スリモアコーヒー、ロートV5、ラクトロン60錠、アパコート、えいようかん、wの健康青汁プラス、ヒハツ＆ギャバの恵み 和漢の森、桑の葉＆茶カテキンの恵み 和漢の森、リンクルストレッチ\n"
        "監視①: 同額以下の競合が出たら通知\n"
        "監視②: 高値なのにポコタより上位の競合が出たら通知\n"
        "監視③: 新着1位を取られたら通知\n"
        "改善: スリモアは個数不明→1個セットとして扱う\n"
        "改善: 全角個数キーワード対応\n"
        "圏外警告: 上位{}件から外れたら即通知\n"
        "チェック間隔: {}秒\n"
        "起動時刻: {}".format(SCAN_N, CHECK_INTERVAL, datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
    )
    last_checked = {item["name"]: 0 for item in MONITOR_ITEMS}
    while True:
        now_ts = time.time()
        for item in MONITOR_ITEMS:
            interval = item.get("check_interval", CHECK_INTERVAL)
            if now_ts - last_checked[item["name"]] >= interval:
                check_item(item)
                last_checked[item["name"]] = time.time()
                time.sleep(3)
        time.sleep(10)

if __name__ == "__main__":
    main()
