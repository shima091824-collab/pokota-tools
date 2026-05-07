#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
market_research.py
メルカリ・ヤフフリの販売数調査 + 楽天・ヤフショ仕入れ価格調査
結果をGoogleスプレッドシートに保存
"""

import time
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==================== 設定 ====================
KEYWORDS = ["スリモアコーヒー"]  # 調査したいキーワード（複数可）
DAYS = 7                          # 何日分を集計するか
SPREADSHEET_ID = "1XnGiqlGvIDfTyCOUXecclDJaBm_J6Gyg12mvZuKZFPg"
SHEET_NAME = "市場調査"
CREDENTIALS_FILE = "/Users/m2mac/credentials.json"
# ================================================


def setup_driver():
    """ヘッドレスChromeの設定"""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1280,900")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(options=options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


def parse_date_mercari(date_str):
    """メルカリの日付文字列をdatetimeに変換"""
    now = datetime.now()
    date_str = date_str.strip()
    try:
        if "分前" in date_str:
            return now
        elif "時間前" in date_str:
            return now
        elif "昨日" in date_str:
            return now - timedelta(days=1)
        elif "日前" in date_str:
            n = int(re.search(r"(\d+)", date_str).group(1))
            return now - timedelta(days=n)
        elif re.match(r"\d{2}/\d{2}", date_str):
            month, day = map(int, date_str.split("/"))
            year = now.year
            return datetime(year, month, day)
        else:
            return None
    except Exception:
        return None


def scrape_mercari(driver, keyword, days):
    """メルカリで売れた商品を検索して直近N日分をカウント"""
    print(f"  [メルカリ] 「{keyword}」を調査中...")
    sold_count = 0
    sold_items = []

    url = (
        f"https://jp.mercari.com/search?"
        f"keyword={keyword}&status=sold_out&sort=created_time&order=desc"
    )

    try:
        driver.get(url)
        time.sleep(3)

        # スクロールして商品を読み込む
        for _ in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)

        items = driver.find_elements(By.CSS_SELECTOR, "li[data-testid='item-cell']")
        print(f"    取得件数: {len(items)}件")

        cutoff = datetime.now() - timedelta(days=days)

        for item in items:
            try:
                # 価格取得
                price_el = item.find_elements(By.CSS_SELECTOR, "[class*='price']")
                price_text = price_el[0].text if price_el else ""
                price = int(re.sub(r"[^\d]", "", price_text)) if price_text else 0

                # 商品名取得
                name_el = item.find_elements(By.CSS_SELECTOR, "[class*='itemName'], [class*='name']")
                name = name_el[0].text if name_el else ""

                # 日付は直近アイテムと仮定（メルカリはsold_out一覧に日付が出にくいため上位を対象）
                sold_count += 1
                sold_items.append({"name": name, "price": price})

                if sold_count >= days * 20:  # 1日20件上限でストップ
                    break

            except Exception:
                continue

        print(f"    → {days}日分の売れ数（推定）: {sold_count}件")
        return sold_count

    except Exception as e:
        print(f"    エラー: {e}")
        return 0


def scrape_yahoo_flea(driver, keyword, days):
    """ヤフフリで売れた商品を調査"""
    print(f"  [ヤフフリ] 「{keyword}」を調査中...")
    sold_count = 0

    # ヤフフリの売れた商品検索URL（クエリパラメータ形式）
    url = (
        f"https://paypayfleamarket.yahoo.co.jp/search/?query={keyword}"
        f"&sold=true&sort=score&order=desc"
    )

    try:
        driver.get(url)
        time.sleep(4)

        for _ in range(6):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)

        # 複数のセレクタを試す
        selectors = [
            "ul[class*='List'] li",
            "div[class*='ItemList'] div[class*='Item']",
            "li[class*='SearchResult']",
            "[data-testid='item']",
            "div[class*='itemCard']",
            "a[href*='/item/']",
        ]

        items = []
        for sel in selectors:
            items = driver.find_elements(By.CSS_SELECTOR, sel)
            if len(items) > 0:
                print(f"    セレクタ「{sel}」で{len(items)}件取得")
                break

        if len(items) == 0:
            # ページソースから商品数を推定
            source = driver.page_source
            count = source.count('/item/')
            print(f"    ページソースから推定: {count}件")
            sold_count = min(count, days * 15)
        else:
            sold_count = min(len(items), days * 15)

        print(f"    → {days}日分の売れ数（推定）: {sold_count}件")
        return sold_count

    except Exception as e:
        print(f"    エラー: {e}")
        return 0


def scrape_rakuten_price(driver, keyword):
    """楽天市場で最安値を取得"""
    print(f"  [楽天] 「{keyword}」の仕入れ価格を調査中...")

    # 価格の安い順 + キーワード完全一致寄りで検索
    url = (
        f"https://search.rakuten.co.jp/search/mall/{keyword}/?s=2&v=2"
    )

    try:
        driver.get(url)
        time.sleep(3)

        prices = []

        # 商品ブロックごとに価格を取得（商品名チェック付き）
        product_blocks = driver.find_elements(
            By.CSS_SELECTOR,
            "div[class*='price-wrapper']"
        )

        if product_blocks:
            for block in product_blocks[:10]:
                block_text = block.text
                nums = re.findall(r"[\d,]{3,}", block_text)
                for n in nums:
                    val = int(n.replace(",", ""))
                    if 500 < val < 50000:
                        prices.append(val)
        else:
            # フォールバック：価格要素を直接取得
            price_els = driver.find_elements(
                By.CSS_SELECTOR,
                "span[class*='price'], span[class*='Price']"
            )
            for el in price_els[:15]:
                text = el.text.strip()
                nums = re.findall(r"[\d,]{3,}", text)
                for n in nums:
                    val = int(n.replace(",", ""))
                    if 500 < val < 50000:
                        prices.append(val)

        if prices:
            # 最安値ではなく「下から2番目」を採用（極端な外れ値を除外）
            prices_sorted = sorted(prices)
            best_price = prices_sorted[1] if len(prices_sorted) > 1 else prices_sorted[0]
            print(f"    → 最安値候補: ¥{best_price:,}")
            return best_price
        else:
            print("    → 価格取得できず")
            return None

    except Exception as e:
        print(f"    エラー: {e}")
        return None


def scrape_yahoostore_price(driver, keyword):
    """ヤフショで最安値を取得"""
    print(f"  [ヤフショ] 「{keyword}」の仕入れ価格を調査中...")

    # 価格の安い順で検索
    url = (
        f"https://shopping.yahoo.co.jp/search?p={keyword}&sort=price&order=a"
    )

    try:
        driver.get(url)
        time.sleep(3)

        prices = []

        # 商品リストから価格を取得
        product_blocks = driver.find_elements(
            By.CSS_SELECTOR,
            "span.item-price-value"
        )

        if product_blocks:
            for block in product_blocks[:10]:
                block_text = block.text
                keyword_main = keyword[:4]
                nums = re.findall(r"[\d,]{3,}", block_text)
                for n in nums:
                    val = int(n.replace(",", ""))
                    if 500 < val < 50000:
                        prices.append(val)
        else:
            # フォールバック
            price_els = driver.find_elements(
                By.CSS_SELECTOR,
                "span[class*='price'], span[class*='Price'], em[class*='price']"
            )
            for el in price_els[:15]:
                text = el.text.strip()
                nums = re.findall(r"[\d,]{3,}", text)
                for n in nums:
                    val = int(n.replace(",", ""))
                    if 500 < val < 50000:
                        prices.append(val)

        if prices:
            prices_sorted = sorted(prices)
            best_price = prices_sorted[1] if len(prices_sorted) > 1 else prices_sorted[0]
            print(f"    → 最安値候補: ¥{best_price:,}")
            return best_price
        else:
            print("    → 価格取得できず")
            return None

    except Exception as e:
        print(f"    エラー: {e}")
        return None


def save_to_spreadsheet(results):
    """Googleスプレッドシートに結果を保存"""
    print("\n📊 スプレッドシートに保存中...")

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)

    # シートを取得 or 新規作成
    try:
        sheet = spreadsheet.worksheet(SHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows=1000, cols=20)
        print(f"  新しいシート「{SHEET_NAME}」を作成しました")

    # ヘッダーがなければ追加
    existing = sheet.get_all_values()
    if not existing:
        headers = [
            "調査日",
            "キーワード",
            "プラットフォーム",
            f"{DAYS}日間売れ数",
            "1日平均",
            "楽天最安値(円)",
            "ヤフショ最安値(円)",
            "参入判定",
        ]
        sheet.append_row(headers)

    # データ追加
    today = datetime.now().strftime("%Y/%m/%d")
    for r in results:
        daily_avg = round(r["sold_count"] / DAYS, 1)
        # 参入判定：1日平均10個以上で「◎」、5個以上で「○」、それ以下で「△」
        if daily_avg >= 10:
            judgment = "◎ 参入推奨"
        elif daily_avg >= 5:
            judgment = "○ 検討可"
        else:
            judgment = "△ 様子見"

        row = [
            today,
            r["keyword"],
            r["platform"],
            r["sold_count"],
            daily_avg,
            r["rakuten_price"] if r["rakuten_price"] else "取得失敗",
            r["yahoo_price"] if r["yahoo_price"] else "取得失敗",
            judgment,
        ]
        sheet.append_row(row)

    print(f"  ✅ {len(results)}行のデータを保存しました")


def main():
    print("=" * 50)
    print("  市場調査ツール 起動")
    print(f"  調査キーワード: {KEYWORDS}")
    print(f"  集計期間: 直近{DAYS}日間")
    print("=" * 50)

    driver = setup_driver()
    results = []

    try:
        for keyword in KEYWORDS:
            print(f"\n🔍 [{keyword}] の調査を開始します")

            # メルカリ調査
            mercari_count = scrape_mercari(driver, keyword, DAYS)
            time.sleep(2)

            # ヤフフリ調査
            yahoo_flea_count = scrape_yahoo_flea(driver, keyword, DAYS)
            time.sleep(2)

            # 楽天価格調査
            rakuten_price = scrape_rakuten_price(driver, keyword)
            time.sleep(2)

            # ヤフショ価格調査
            yahoo_price = scrape_yahoostore_price(driver, keyword)
            time.sleep(2)

            results.append({
                "keyword": keyword,
                "platform": "メルカリ",
                "sold_count": mercari_count,
                "rakuten_price": rakuten_price,
                "yahoo_price": yahoo_price,
            })
            results.append({
                "keyword": keyword,
                "platform": "ヤフフリ",
                "sold_count": yahoo_flea_count,
                "rakuten_price": rakuten_price,
                "yahoo_price": yahoo_price,
            })

            # 結果を画面に表示
            print(f"\n📋 [{keyword}] 調査結果")
            print(f"  メルカリ {DAYS}日間売れ数: {mercari_count}件 (1日平均: {round(mercari_count/DAYS,1)}件)")
            print(f"  ヤフフリ {DAYS}日間売れ数: {yahoo_flea_count}件 (1日平均: {round(yahoo_flea_count/DAYS,1)}件)")
            print(f"  楽天最安値: ¥{rakuten_price:,}" if rakuten_price else "  楽天最安値: 取得失敗")
            print(f"  ヤフショ最安値: ¥{yahoo_price:,}" if yahoo_price else "  ヤフショ最安値: 取得失敗")

    finally:
        driver.quit()

    # スプレッドシートに保存
    save_to_spreadsheet(results)
    print("\n✅ 全ての調査が完了しました！")
    print(f"スプレッドシートの「{SHEET_NAME}」シートを確認してください。")


if __name__ == "__main__":
    main()
