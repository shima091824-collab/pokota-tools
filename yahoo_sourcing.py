#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
yahoo_sourcing.py
メルカリ売れ筋商品 → Yahooショッピング最安値チェック → 利益率計算
"""

import json
import time
import re
import gspread
from google.oauth2.service_account import Credentials
from playwright.sync_api import sync_playwright

# ── 設定 ──────────────────────────────────────────
SPREADSHEET_ID = "12-F-g3gmqbTUx2CJeU2MFOH3ehHRmrbbDtEoYlXlJRc"
SOURCE_SHEET   = "サプリメント_2026-04"   # 売れ筋データのシート
OUTPUT_SHEET   = "仕入れ調査_2026-04"     # 結果を書き込むシート（自動作成）
CREDENTIALS    = "/Users/m2mac/credentials.json"

MERCARI_FEE_RATE = 0.10   # メルカリ手数料10%
SHIPPING_COST    = 160    # 送料固定¥160
MIN_PROFIT_RATE  = 0.15   # 利益率15%以上を採算ありとみなす

# ── Google Sheets接続 ──────────────────────────────
def connect_sheets():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds  = Credentials.from_service_account_file(CREDENTIALS, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID)

# ── 売れ筋リストを読み込む ────────────────────────
def load_products(book):
    ws = book.worksheet(SOURCE_SHEET)
    rows = ws.get_all_values()
    products = []
    for row in rows[1:]:  # 1行目はヘッダー
        if len(row) >= 3 and row[0].strip():
            try:
                name  = row[0].strip()
                price = int(row[1].strip()) if row[1].strip().isdigit() else 0
                count = int(row[2].strip()) if row[2].strip().isdigit() else 0
                if name and price > 0:
                    products.append({"name": name, "mercari_price": price, "sold_count": count})
            except:
                continue
    return products

# ── Yahooショッピングで最安値検索 ──────────────────
def search_yahoo_shopping(page, product_name):
    try:
        url = f"https://shopping.yahoo.co.jp/search?p={product_name}&sort=-price&order=a"
        page.goto(url, timeout=15000)
        page.wait_for_timeout(2000)

        results = page.evaluate("""
            () => {
                const items = [];
                // 商品カード取得（複数セレクタ対応）
                const cards = document.querySelectorAll(
                    '[data-cl-params], .LoopList__item, .Product'
                );
                cards.forEach(card => {
                    const nameEl  = card.querySelector('a[title], .Product__title a, h3 a');
                    const priceEl = card.querySelector(
                        '.Product__price, [class*="price"], .LoopList__itemPrice'
                    );
                    const linkEl  = card.querySelector('a[href*="shopping.yahoo"]');
                    if (nameEl && priceEl) {
                        const priceText = priceEl.textContent.replace(/[^0-9]/g, '');
                        const price = parseInt(priceText);
                        if (price > 0) {
                            items.push({
                                name:  nameEl.textContent.trim().slice(0, 60),
                                price: price,
                                url:   linkEl ? linkEl.href : ''
                            });
                        }
                    }
                });
                return items.slice(0, 5);
            }
        """)

        if results:
            # 最安値を返す
            min_item = min(results, key=lambda x: x['price'])
            return min_item
        return None

    except Exception as e:
        print(f"  ⚠️  検索エラー ({product_name[:20]}): {e}")
        return None

# ── 利益計算 ─────────────────────────────────────
def calc_profit(mercari_price, buy_price):
    """
    利益 = メルカリ売価 × (1 - 手数料) - 送料 - 仕入れ値
    """
    net_revenue = mercari_price * (1 - MERCARI_FEE_RATE)
    profit      = net_revenue - SHIPPING_COST - buy_price
    profit_rate = profit / mercari_price if mercari_price > 0 else 0
    return int(profit), round(profit_rate * 100, 1)

# ── 結果をスプレッドシートへ書き込む ───────────────
def write_results(book, results):
    # シートがなければ作成
    try:
        ws = book.worksheet(OUTPUT_SHEET)
        ws.clear()
    except:
        ws = book.add_worksheet(OUTPUT_SHEET, rows=100, cols=10)

    headers = [
        "商品名", "メルカリ売価(円)", "販売数",
        "Yahoo最安値(円)", "利益額(円)", "利益率(%)",
        "採算", "Yahoo商品名", "Yahoo URL"
    ]
    rows = [headers]
    for r in results:
        rows.append([
            r["name"],
            r["mercari_price"],
            r["sold_count"],
            r.get("buy_price", "取得不可"),
            r.get("profit", "-"),
            r.get("profit_rate", "-"),
            r.get("verdict", "-"),
            r.get("yahoo_name", "-"),
            r.get("yahoo_url", "-"),
        ])

    ws.update("A1", rows)

    # ヘッダー行を太字・背景色
    ws.format("A1:I1", {
        "textFormat": {"bold": True},
        "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 0.9}
    })

    # 採算あり行を緑に
    for i, r in enumerate(results, start=2):
        if r.get("verdict") == "✅ 採算あり":
            ws.format(f"A{i}:I{i}", {
                "backgroundColor": {"red": 0.85, "green": 0.95, "blue": 0.85}
            })

    print(f"\n✅ スプレッドシートへ書き込み完了: {OUTPUT_SHEET}")
    print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")

# ── メイン ────────────────────────────────────────
def main():
    print("📊 売れ筋商品リストを読み込み中...")
    book     = connect_sheets()
    products = load_products(book)
    print(f"   {len(products)} 件の商品を取得")

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page    = browser.new_page()
        # Botと判定されにくいUA設定
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        })

        for i, product in enumerate(products, 1):
            name = product["name"]
            print(f"\n[{i}/{len(products)}] {name[:30]}")

            yahoo = search_yahoo_shopping(page, name)

            if yahoo and yahoo["price"] > 0:
                profit, profit_rate = calc_profit(product["mercari_price"], yahoo["price"])
                verdict = "✅ 採算あり" if profit_rate >= MIN_PROFIT_RATE * 100 else "❌ 採算なし"
                print(f"   売価 ¥{product['mercari_price']:,} / 仕入れ ¥{yahoo['price']:,} "
                      f"/ 利益 ¥{profit:,} ({profit_rate}%) {verdict}")
                results.append({
                    **product,
                    "buy_price":   yahoo["price"],
                    "profit":      profit,
                    "profit_rate": profit_rate,
                    "verdict":     verdict,
                    "yahoo_name":  yahoo["name"],
                    "yahoo_url":   yahoo["url"],
                })
            else:
                print("   → Yahoo最安値取得できず")
                results.append({**product, "verdict": "⚠️ 取得不可"})

            time.sleep(1.5)  # サーバー負荷軽減

        browser.close()

    # 利益率の高い順にソート
    results.sort(key=lambda x: x.get("profit_rate", -999), reverse=True)

    print("\n" + "="*60)
    print("📈 採算あり商品ランキング")
    print("="*60)
    for r in results:
        if r.get("verdict") == "✅ 採算あり":
            print(f"  {r['profit_rate']:5.1f}% | ¥{r.get('profit',0):,} | {r['name'][:30]}")

    write_results(book, results)

if __name__ == "__main__":
    main()
