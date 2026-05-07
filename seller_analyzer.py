#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seller_analyzer.py
メルカリ・ヤフフリ セラー分析ツール
- キーワード検索 → 売り切れ商品集計 → 評価500以上セラー抽出 → スプレッドシート保存
"""

import time
import random
import re
import json
from datetime import datetime, timedelta
from collections import defaultdict

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ============================================================
# 設定
# ============================================================
KEYWORDS = [
    "健康食品", "サプリ", "プロテイン", "コーヒー",
    "ダイエット", "ビタミン", "コラーゲン", "酵素"
]

ITEMS_PER_KEYWORD = 50          # 1キーワードあたり収集件数
MIN_DAILY_SALES = 10            # 1日平均最低売れ数
MIN_SELLER_RATING = 500         # セラー評価最低数

SPREADSHEET_ID = "1XnGiqlGvIDfTyCOUXecclDJaBm_J6Gyg12mvZuKZFPg"
SHEET_NAME = "セラー分析"

CREDENTIALS_FILE = "/Users/m2mac/credentials.json"  # Google認証ファイル


# ============================================================
# Chrome起動（ヘッドレス・プロファイルなし）
# ============================================================
def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,900")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def sleep_random(a=2.0, b=4.5):
    time.sleep(random.uniform(a, b))


# ============================================================
# 日付パース ユーティリティ
# ============================================================
def parse_date_jp(text):
    """
    「3日前」「1週間前」「2025/04/01」「04/01」などを date に変換
    取得できない場合は None
    """
    today = datetime.today().date()
    if not text:
        return None
    text = text.strip()

    m = re.search(r"(\d+)分前", text)
    if m:
        return today

    m = re.search(r"(\d+)時間前", text)
    if m:
        return today

    m = re.search(r"(\d+)日前", text)
    if m:
        return today - timedelta(days=int(m.group(1)))

    m = re.search(r"(\d+)週間前", text)
    if m:
        return today - timedelta(weeks=int(m.group(1)))

    m = re.search(r"(\d+)ヶ月前", text)
    if m:
        return today - timedelta(days=int(m.group(1)) * 30)

    m = re.search(r"(\d{4})[/\-年](\d{1,2})[/\-月](\d{1,2})", text)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).date()
        except Exception:
            return None

    m = re.search(r"(\d{1,2})[/\-月](\d{1,2})", text)
    if m:
        try:
            year = today.year
            d = datetime(year, int(m.group(1)), int(m.group(2))).date()
            if d > today:
                d = datetime(year - 1, int(m.group(1)), int(m.group(2))).date()
            return d
        except Exception:
            return None

    return None


def calc_daily_avg(sold_count, listed_date, sold_date):
    """出品日〜売り切れ日の日数で1日平均を計算"""
    if listed_date and sold_date and sold_date > listed_date:
        days = (sold_date - listed_date).days
        return sold_count / days if days > 0 else sold_count
    return 0


# ============================================================
# メルカリ スクレイピング
# ============================================================
def scrape_mercari_keyword(driver, keyword, max_items=50):
    """
    メルカリで売り切れ商品を収集
    戻り値: [{"name", "price", "seller_url", "sold_date", "listed_date"}, ...]
    """
    results = []
    url = f"https://jp.mercari.com/search?keyword={keyword}&status=sold_out&sort=sold_desc"
    print(f"  [メルカリ] '{keyword}' 検索中...")

    try:
        driver.get(url)
        sleep_random(3, 5)

        items_collected = []
        scroll_count = 0

        while len(items_collected) < max_items and scroll_count < 15:
            cards = driver.find_elements(By.CSS_SELECTOR, "li[data-testid='item-cell']")
            for card in cards:
                if len(items_collected) >= max_items:
                    break
                try:
                    link_el = card.find_element(By.TAG_NAME, "a")
                    href = link_el.get_attribute("href")
                    if href and "/item/" in href and href not in [x.get("url") for x in items_collected]:
                        name_el = card.find_elements(By.CSS_SELECTOR, "[class*='itemName'], [class*='item-name'], span")
                        name = name_el[0].text.strip() if name_el else ""
                        price_el = card.find_elements(By.CSS_SELECTOR, "[class*='price'], [class*='Price']")
                        price = price_el[0].text.strip() if price_el else ""
                        items_collected.append({"url": href, "name": name, "price": price})
                except Exception:
                    continue

            driver.execute_script("window.scrollBy(0, 1200);")
            sleep_random(2, 3.5)
            scroll_count += 1

        print(f"    → {len(items_collected)}件の一覧を取得。詳細を取得中...")

        # 詳細ページから売り切れ日・出品日・セラーURLを取得
        for i, item in enumerate(items_collected[:max_items]):
            try:
                driver.get(item["url"])
                sleep_random(2, 4)

                # セラーURL
                seller_url = ""
                try:
                    seller_link = driver.find_element(
                        By.CSS_SELECTOR,
                        "a[href*='/user/profile/'], a[data-testid='seller-link']"
                    )
                    seller_url = seller_link.get_attribute("href")
                except Exception:
                    pass

                # 売り切れ日・出品日（メタ情報から）
                sold_date = None
                listed_date = None
                try:
                    info_items = driver.find_elements(
                        By.CSS_SELECTOR,
                        "[data-testid='item-info'] span, .merText"
                    )
                    for el in info_items:
                        t = el.text
                        if "売り切れ" in t or "購入" in t:
                            sold_date = parse_date_jp(t)
                        if "出品" in t:
                            listed_date = parse_date_jp(t)
                except Exception:
                    pass

                results.append({
                    "name": item["name"],
                    "price": item["price"],
                    "seller_url": seller_url,
                    "sold_date": sold_date,
                    "listed_date": listed_date,
                    "platform": "メルカリ"
                })

                if (i + 1) % 10 == 0:
                    print(f"    詳細取得: {i+1}/{len(items_collected[:max_items])}件")

            except Exception as e:
                print(f"    詳細取得エラー: {e}")
                continue

    except Exception as e:
        print(f"  [メルカリ] エラー: {e}")

    return results


# ============================================================
# ヤフフリ スクレイピング
# ============================================================
def scrape_yahoo_keyword(driver, keyword, max_items=50):
    """
    ヤフフリで売り切れ商品を収集
    戻り値: [{"name", "price", "seller_url", "sold_date", "listed_date"}, ...]
    """
    results = []
    url = (
        f"https://paypayfleamarket.yahoo.co.jp/search/{keyword}"
        f"?status=2&sort=-updatedTime"  # status=2: 売り切れ
    )
    print(f"  [ヤフフリ] '{keyword}' 検索中...")

    try:
        driver.get(url)
        sleep_random(3, 5)

        items_collected = []
        scroll_count = 0

        while len(items_collected) < max_items and scroll_count < 15:
            cards = driver.find_elements(
                By.CSS_SELECTOR,
                "a[href*='/item/'], li[class*='item'], div[class*='Item']"
            )
            for card in cards:
                try:
                    href = card.get_attribute("href") if card.tag_name == "a" else ""
                    if not href:
                        a_el = card.find_elements(By.TAG_NAME, "a")
                        href = a_el[0].get_attribute("href") if a_el else ""
                    if href and "/item/" in href and href not in [x.get("url") for x in items_collected]:
                        name_els = card.find_elements(
                            By.CSS_SELECTOR,
                            "[class*='title'], [class*='name'], p"
                        )
                        name = name_els[0].text.strip() if name_els else ""
                        price_els = card.find_elements(
                            By.CSS_SELECTOR,
                            "[class*='price'], [class*='Price']"
                        )
                        price = price_els[0].text.strip() if price_els else ""
                        items_collected.append({"url": href, "name": name, "price": price})
                except Exception:
                    continue

            driver.execute_script("window.scrollBy(0, 1200);")
            sleep_random(2, 3.5)
            scroll_count += 1

        print(f"    → {len(items_collected)}件の一覧を取得。詳細を取得中...")

        for i, item in enumerate(items_collected[:max_items]):
            try:
                driver.get(item["url"])
                sleep_random(2, 4)

                seller_url = ""
                try:
                    seller_link = driver.find_element(
                        By.CSS_SELECTOR,
                        "a[href*='/user/'], a[href*='/seller/']"
                    )
                    seller_url = seller_link.get_attribute("href")
                except Exception:
                    pass

                sold_date = None
                listed_date = None
                try:
                    time_els = driver.find_elements(
                        By.CSS_SELECTOR,
                        "time, [class*='date'], [class*='Date'], [class*='time'], span"
                    )
                    for el in time_els:
                        t = el.get_attribute("datetime") or el.text
                        d = parse_date_jp(t)
                        if d:
                            if not listed_date:
                                listed_date = d
                            else:
                                sold_date = d
                except Exception:
                    pass

                results.append({
                    "name": item["name"],
                    "price": item["price"],
                    "seller_url": seller_url,
                    "sold_date": sold_date,
                    "listed_date": listed_date,
                    "platform": "ヤフフリ"
                })

                if (i + 1) % 10 == 0:
                    print(f"    詳細取得: {i+1}/{len(items_collected[:max_items])}件")

            except Exception as e:
                print(f"    詳細取得エラー: {e}")
                continue

    except Exception as e:
        print(f"  [ヤフフリ] エラー: {e}")

    return results


# ============================================================
# セラー詳細取得
# ============================================================
def get_seller_info_mercari(driver, seller_url):
    """メルカリ セラープロフィール取得"""
    if not seller_url:
        return {"name": "", "rating": 0, "other_items": 0}
    try:
        driver.get(seller_url)
        sleep_random(2, 4)

        name = ""
        rating = 0
        other_items = 0

        try:
            name_el = driver.find_element(
                By.CSS_SELECTOR,
                "[data-testid='user-name'], h1, [class*='userName']"
            )
            name = name_el.text.strip()
        except Exception:
            pass

        try:
            rating_els = driver.find_elements(
                By.CSS_SELECTOR,
                "[class*='rating'], [class*='Rating'], [data-testid='rating']"
            )
            for el in rating_els:
                nums = re.findall(r"[\d,]+", el.text)
                if nums:
                    rating = int(nums[0].replace(",", ""))
                    break
        except Exception:
            pass

        try:
            sold_els = driver.find_elements(
                By.CSS_SELECTOR,
                "[class*='sold'], li[data-testid='item-cell']"
            )
            other_items = len(sold_els)
        except Exception:
            pass

        return {"name": name, "rating": rating, "other_items": other_items}

    except Exception as e:
        print(f"    セラー情報取得エラー(メルカリ): {e}")
        return {"name": "", "rating": 0, "other_items": 0}


def get_seller_info_yahoo(driver, seller_url):
    """ヤフフリ セラープロフィール取得"""
    if not seller_url:
        return {"name": "", "rating": 0, "other_items": 0}
    try:
        driver.get(seller_url)
        sleep_random(2, 4)

        name = ""
        rating = 0
        other_items = 0

        try:
            name_el = driver.find_element(
                By.CSS_SELECTOR,
                "[class*='userName'], [class*='nickname'], h1, h2"
            )
            name = name_el.text.strip()
        except Exception:
            pass

        try:
            rating_els = driver.find_elements(
                By.CSS_SELECTOR,
                "[class*='rating'], [class*='Rating'], [class*='review']"
            )
            for el in rating_els:
                nums = re.findall(r"[\d,]+", el.text)
                if nums:
                    rating = int(nums[0].replace(",", ""))
                    break
        except Exception:
            pass

        try:
            item_els = driver.find_elements(
                By.CSS_SELECTOR,
                "a[href*='/item/'], [class*='item'], [class*='Item']"
            )
            other_items = len(item_els)
        except Exception:
            pass

        return {"name": name, "rating": rating, "other_items": other_items}

    except Exception as e:
        print(f"    セラー情報取得エラー(ヤフフリ): {e}")
        return {"name": "", "rating": 0, "other_items": 0}


# ============================================================
# 集計・フィルタリング
# ============================================================
def aggregate_products(all_items):
    """
    商品名ごとに売れ数・1日平均を集計
    戻り値: {商品名: {"count", "daily_avg", "sellers": [seller_url, ...]}}
    """
    product_map = defaultdict(lambda: {"count": 0, "daily_total": 0, "days_count": 0, "sellers": []})

    for item in all_items:
        key = item["name"][:40]  # 商品名の先頭40文字で集約
        if not key:
            continue
        product_map[key]["count"] += 1
        product_map[key]["sellers"].append({
            "url": item.get("seller_url", ""),
            "platform": item.get("platform", "")
        })

        # 1日平均計算
        listed = item.get("listed_date")
        sold = item.get("sold_date")
        if listed and sold and sold > listed:
            days = (sold - listed).days
            if days > 0:
                product_map[key]["daily_total"] += 1 / days
                product_map[key]["days_count"] += 1

    result = {}
    for name, data in product_map.items():
        daily_avg = data["daily_total"] if data["days_count"] > 0 else 0
        result[name] = {
            "count": data["count"],
            "daily_avg": round(daily_avg, 2),
            "sellers": data["sellers"]
        }
    return result


def filter_hot_products(product_map, min_daily=MIN_DAILY_SALES):
    """1日平均売れ数が基準以上の商品を返す（日付が取れない場合は件数で代替）"""
    hot = {}
    for name, data in product_map.items():
        # 日付が取得できた場合はdaily_avgで判定
        if data["daily_avg"] >= min_daily:
            hot[name] = data
        # 日付なしの場合: 全体件数が min_daily * 7 以上なら候補に入れる（緩い基準）
        elif data["daily_avg"] == 0 and data["count"] >= min_daily * 7:
            hot[name] = data
    return hot


# ============================================================
# スプレッドシート保存
# ============================================================
def save_to_spreadsheet(rows):
    """Google スプレッドシートの「セラー分析」シートに書き込む"""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    ss = client.open_by_key(SPREADSHEET_ID)

    # シートがなければ作成
    try:
        sheet = ss.worksheet(SHEET_NAME)
    except Exception:
        sheet = ss.add_worksheet(title=SHEET_NAME, rows=2000, cols=10)

    # ヘッダーがなければ追加
    existing = sheet.get_all_values()
    header = ["調査日", "商品名", "全体売れ数", "1日平均", "セラー名", "評価数", "セラー他商品数", "プラットフォーム", "セラーURL"]
    if not existing or existing[0] != header:
        sheet.insert_row(header, 1)

    # データ追記
    if rows:
        sheet.append_rows(rows, value_input_option="USER_ENTERED")
        print(f"\n✅ スプレッドシートに {len(rows)} 件を保存しました。")
    else:
        print("\n⚠️  保存するデータがありませんでした。")


# ============================================================
# メイン処理
# ============================================================
def main():
    today_str = datetime.today().strftime("%Y/%m/%d")
    print("=" * 60)
    print("  seller_analyzer.py 開始")
    print(f"  調査日: {today_str}")
    print(f"  キーワード数: {len(KEYWORDS)}  各{ITEMS_PER_KEYWORD}件")
    print("=" * 60)

    driver = create_driver()
    all_items = []

    try:
        # ── Step 1: 全キーワード × 両プラットフォームで収集 ──
        for kw in KEYWORDS:
            print(f"\n【キーワード: {kw}】")
            mercari_items = scrape_mercari_keyword(driver, kw, ITEMS_PER_KEYWORD)
            yahoo_items = scrape_yahoo_keyword(driver, kw, ITEMS_PER_KEYWORD)
            all_items.extend(mercari_items)
            all_items.extend(yahoo_items)
            print(f"  小計: メルカリ{len(mercari_items)}件 / ヤフフリ{len(yahoo_items)}件")
            sleep_random(3, 6)

        print(f"\n✅ 収集完了: 合計 {len(all_items)} 件")

        # ── Step 2: 商品名で集計 ──
        print("\n【集計中...】")
        product_map = aggregate_products(all_items)
        print(f"  ユニーク商品数: {len(product_map)} 種類")

        # ── Step 3: ホット商品を絞り込み ──
        hot_products = filter_hot_products(product_map)
        print(f"  1日{MIN_DAILY_SALES}個以上の候補: {len(hot_products)} 種類")

        if not hot_products:
            print("\n⚠️  条件を満たす商品が見つかりませんでした。閾値を下げることを検討してください。")
            return

        # ── Step 4: セラー詳細取得 ──
        print("\n【セラー情報取得中...】")
        output_rows = []
        processed_sellers = {}  # キャッシュ（同じURLを2度取得しない）

        for prod_name, data in hot_products.items():
            print(f"\n  商品: {prod_name[:30]}... (売れ数:{data['count']} 1日平均:{data['daily_avg']})")

            for seller_info in data["sellers"]:
                seller_url = seller_info.get("url", "")
                platform = seller_info.get("platform", "")
                if not seller_url:
                    continue

                # キャッシュ確認
                if seller_url in processed_sellers:
                    sinfo = processed_sellers[seller_url]
                else:
                    if platform == "メルカリ":
                        sinfo = get_seller_info_mercari(driver, seller_url)
                    else:
                        sinfo = get_seller_info_yahoo(driver, seller_url)
                    processed_sellers[seller_url] = sinfo

                # 評価500以上のみ
                if sinfo["rating"] < MIN_SELLER_RATING:
                    continue

                print(f"    ★ {sinfo['name']} 評価:{sinfo['rating']} 他商品:{sinfo['other_items']}件")

                output_rows.append([
                    today_str,
                    prod_name,
                    data["count"],
                    data["daily_avg"],
                    sinfo["name"],
                    sinfo["rating"],
                    sinfo["other_items"],
                    platform,
                    seller_url
                ])

        # ── Step 5: スプレッドシート保存 ──
        print("\n【スプレッドシートに保存中...】")
        save_to_spreadsheet(output_rows)

        # ── 結果サマリー ──
        print("\n" + "=" * 60)
        print(f"  完了！評価{MIN_SELLER_RATING}以上のセラー: {len(output_rows)} 件を保存")
        print("=" * 60)

    finally:
        driver.quit()
        print("Chromeを終了しました。")


if __name__ == "__main__":
    main()
