#!/usr/bin/env python3
"""
mercari_research.py
メルカリの売り切れ商品（健康・美容カテゴリ、¥1,000〜¥5,000）を収集し
Googleスプレッドシートに出力するリサーチツール。

セッションファイル: ~/research_state.json  （販売用 mercari_state.json とは独立）
設定ファイル      : ~/research_config.json
認証トークン      : ~/research_token.json
"""

import json
import math
import os
import random
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# ─────────────────────────── 定数 ───────────────────────────
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
]
CONFIG_FILE   = os.path.expanduser('~/research_config.json')
JST           = timezone(timedelta(hours=9))
UA = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/124.0.0.0 Safari/537.36'
)

# ─────────────────────────── 設定読み込み ───────────────────────────

def load_config() -> dict:
    defaults = {
        'keyword':        '',
        'category_id':    '6',
        'category_name':  '健康・美容・ダイエット',
        'price_min':      1000,
        'price_max':      5000,
        'days_back':      30,
        'max_pages':      40,
        'wait_min':       2.0,
        'wait_max':       5.0,
        'credentials_file': '~/sales_entry_credentials.json',
        'token_file':     '~/research_token.json',
        'session_file':   '~/research_state.json',
    }
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, encoding='utf-8') as f:
            defaults.update(json.load(f))
    return defaults


# ─────────────────────────── Google 認証 ───────────────────────────

def get_google_creds(config: dict) -> Credentials:
    cred_file  = os.path.expanduser(config['credentials_file'])
    token_file = os.path.expanduser(config['token_file'])

    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(cred_file):
                print(f'[エラー] 認証ファイルが見つかりません: {cred_file}')
                print('  sales_entry_credentials.json が ~/に必要です。')
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(cred_file, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_file, 'w') as f:
            f.write(creds.to_json())
        print(f'  [認証] トークンを保存しました: {token_file}')

    return creds


# ─────────────────────────── スプレッドシート作成 ───────────────────────────

def create_spreadsheet(creds: Credentials, sheet_title: str) -> str:
    """新規スプレッドシートを作成し、スプレッドシートIDを返す"""
    service = build('sheets', 'v4', credentials=creds)
    body = {
        'properties': {'title': sheet_title},
        'sheets': [{
            'properties': {
                'title': sheet_title,
                'gridProperties': {'frozenRowCount': 1},
            }
        }]
    }
    result = service.spreadsheets().create(body=body).execute()
    ss_id = result['spreadsheetId']
    print(f'  [Sheets] 新規スプレッドシート作成: {sheet_title}')
    return ss_id


def write_to_sheet(creds: Credentials, ss_id: str, sheet_title: str, rows: list):
    """ヘッダー + データ行をスプレッドシートに書き込む"""
    service = build('sheets', 'v4', credentials=creds)

    header = ['商品名', '平均価格（円）', '売れた件数', '最終売れた日', '価格帯']
    values = [header] + rows

    body = {'values': values}
    service.spreadsheets().values().update(
        spreadsheetId=ss_id,
        range=f"'{sheet_title}'!A1",
        valueInputOption='USER_ENTERED',
        body=body,
    ).execute()

    # ヘッダー行を太字・背景色に
    requests = [{
        'repeatCell': {
            'range': {
                'sheetId': _get_sheet_id(service, ss_id, sheet_title),
                'startRowIndex': 0,
                'endRowIndex': 1,
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': {'red': 0.26, 'green': 0.52, 'blue': 0.96},
                    'textFormat': {
                        'bold': True,
                        'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
                    },
                }
            },
            'fields': 'userEnteredFormat(backgroundColor,textFormat)',
        }
    }, {
        'autoResizeDimensions': {
            'dimensions': {
                'sheetId': _get_sheet_id(service, ss_id, sheet_title),
                'dimension': 'COLUMNS',
                'startIndex': 0,
                'endIndex': 5,
            }
        }
    }]
    service.spreadsheets().batchUpdate(
        spreadsheetId=ss_id,
        body={'requests': requests},
    ).execute()

    print(f'  [Sheets] {len(rows)} 件を書き込みました')


def _get_sheet_id(service, ss_id: str, sheet_title: str) -> int:
    meta = service.spreadsheets().get(spreadsheetId=ss_id).execute()
    for s in meta['sheets']:
        if s['properties']['title'] == sheet_title:
            return s['properties']['sheetId']
    return 0


# ─────────────────────────── 価格帯ラベル ───────────────────────────

def price_range_label(avg_price: float, step: int = 500) -> str:
    """平均価格から価格帯文字列を生成（例: 1000-1500円）"""
    lo = int(avg_price // step) * step
    hi = lo + step
    return f'{lo}-{hi}円'


# ─────────────────────────── メルカリ スクレイピング ───────────────────────────

def wait(config: dict):
    t = random.uniform(config['wait_min'], config['wait_max'])
    time.sleep(t)


def build_search_url(config: dict, page: int = 1) -> str:
    """
    メルカリ検索URL を構築。
    - keyword が指定されていればキーワード検索、なければ category_id 検索
    - status=sold_out: 売り切れのみ
    - price_min / price_max
    """
    base = 'https://jp.mercari.com/search'
    if config.get('keyword', '').strip():
        params = (
            f'?status=sold_out'
            f'&keyword={config["keyword"].strip()}'
            f'&price_min={config["price_min"]}'
            f'&price_max={config["price_max"]}'
            f'&sort=created_time'
            f'&order=desc'
            f'&page={page}'
        )
    else:
        params = (
            f'?status=sold_out'
            f'&category_id={config["category_id"]}'
            f'&price_min={config["price_min"]}'
            f'&price_max={config["price_max"]}'
            f'&sort=created_time'
            f'&order=desc'
            f'&page={page}'
        )
    return base + params


def parse_price(text: str) -> int | None:
    """「¥1,234」→ 1234"""
    digits = re.sub(r'[^\d]', '', text)
    return int(digits) if digits else None


def parse_date_from_text(text: str) -> datetime | None:
    """
    メルカリのSOLD日時テキストをパース。
    例: "4月10日" / "3日前" / "2026/04/10"
    """
    now = datetime.now(JST)

    # "N分前" / "N時間前" / "N日前"
    m = re.search(r'(\d+)日前', text)
    if m:
        return now - timedelta(days=int(m.group(1)))
    m = re.search(r'(\d+)時間前', text)
    if m:
        return now - timedelta(hours=int(m.group(1)))
    m = re.search(r'(\d+)分前', text)
    if m:
        return now - timedelta(minutes=int(m.group(1)))

    # "M月D日"（当年）
    m = re.search(r'(\d+)月(\d+)日', text)
    if m:
        mo, day = int(m.group(1)), int(m.group(2))
        try:
            dt = datetime(now.year, mo, day, tzinfo=JST)
            if dt > now:
                dt = dt.replace(year=now.year - 1)
            return dt
        except ValueError:
            return None

    # "YYYY/MM/DD"
    m = re.search(r'(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})', text)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=JST)
        except ValueError:
            return None

    return None


def scrape_mercari(config: dict) -> list[dict]:
    """
    Playwright でメルカリの SOLD 商品を収集。
    戻り値: [{'name': str, 'price': int, 'sold_date': datetime | None}, ...]
    """
    state_path   = os.path.expanduser(config['session_file'])
    cutoff_date  = datetime.now(JST) - timedelta(days=config['days_back'])
    max_pages    = config['max_pages']
    items        = []
    stop_early   = False

    print(f'\n[スクレイピング開始]')
    if config.get('keyword', '').strip():
        print(f'  キーワード: {config["keyword"].strip()}')
    else:
        print(f'  カテゴリ : {config["category_name"]} (ID={config["category_id"]})')
    print(f'  価格帯   : ¥{config["price_min"]:,} 〜 ¥{config["price_max"]:,}')
    print(f'  対象期間 : 直近 {config["days_back"]} 日')
    print(f'  最大ページ: {max_pages}')
    print(f'  セッション: {state_path}')
    print()

    with sync_playwright() as p:
        # ────── ブラウザ起動（完全独立プロファイル） ──────
        ctx_kwargs = dict(
            user_agent=UA,
            locale='ja-JP',
            timezone_id='Asia/Tokyo',
            viewport={'width': 1280, 'height': 800},
        )
        if os.path.exists(state_path):
            ctx_kwargs['storage_state'] = state_path
            print(f'  [セッション] {state_path} を読み込みました')
        else:
            print(f'  [セッション] ファイルなし → 未ログイン状態で実行')

        browser = p.chromium.launch(headless=True)
        ctx     = browser.new_context(**ctx_kwargs)
        page    = ctx.new_page()

        # ────── ページネーションループ ──────
        for pg in range(1, max_pages + 1):
            if stop_early:
                break

            url = build_search_url(config, page=pg)
            print(f'  Page {pg:>3} / {max_pages}  {url}')

            try:
                page.goto(url, wait_until='domcontentloaded', timeout=30000)
            except PWTimeout:
                print(f'    [タイムアウト] ページ {pg} をスキップ')
                wait(config)
                continue

            # 商品カード要素を待機（最大10秒）
            try:
                page.wait_for_selector(
                    'li[data-testid="item-cell"], [data-testid="item-thumbnail"]',
                    timeout=10000,
                )
            except PWTimeout:
                print(f'    [商品なし] ページ {pg} に商品が見つかりません → 終了')
                break

            # ページの全テキスト+構造を解析
            page_items = _extract_items_from_page(page)

            if not page_items:
                print(f'    [終了] ページ {pg} で商品が取得できませんでした')
                break

            added_count = 0
            for item in page_items:
                sold_date = item.get('sold_date')
                # 日付が取れている場合はカットオフでフィルタ
                if sold_date and sold_date < cutoff_date:
                    stop_early = True
                    continue
                items.append(item)
                added_count += 1

            print(f'    → {added_count} 件取得 (累計 {len(items)} 件)')

            if pg < max_pages and not stop_early:
                wait(config)

        ctx.close()
        browser.close()

    print(f'\n[収集完了] 合計 {len(items)} 件')
    return items


def _extract_items_from_page(page) -> list[dict]:
    """ページ内の商品カードから商品名・価格・売れ日を抽出"""
    items = []

    # JavaScript で商品データを収集
    raw = page.evaluate("""
        () => {
            const results = [];

            // パターン1: data-testid="item-cell" の li 要素
            const cells = document.querySelectorAll('li[data-testid="item-cell"]');
            cells.forEach(cell => {
                const nameEl = cell.querySelector('[data-testid="item-name"], .item-name, h3, [class*="itemName"], [class*="item_name"]');
                const priceEl = cell.querySelector('[data-testid="item-price"], .item-price, [class*="itemPrice"], [class*="item_price"], [class*="price"]');
                const dateEl = cell.querySelector('[data-testid="item-sold-time"], [class*="soldTime"], [class*="sold_time"], time, [class*="date"]');

                const name  = nameEl  ? nameEl.textContent.trim()  : '';
                const price = priceEl ? priceEl.textContent.trim() : '';
                const date  = dateEl  ? (dateEl.getAttribute('datetime') || dateEl.textContent.trim()) : '';

                if (name && price) {
                    results.push({ name, price, date });
                }
            });

            // パターン2: mer-item-thumbnail
            if (results.length === 0) {
                const thumbs = document.querySelectorAll('mer-item-thumbnail, [data-testid="item-thumbnail"]');
                thumbs.forEach(el => {
                    const name  = el.getAttribute('item-name') || el.getAttribute('aria-label') || '';
                    const price = el.getAttribute('price') || '';
                    const date  = el.getAttribute('updated-time') || '';
                    if (name) {
                        results.push({ name, price, date });
                    }
                });
            }

            // パターン3: JSON-LD
            if (results.length === 0) {
                const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                scripts.forEach(s => {
                    try {
                        const data = JSON.parse(s.textContent);
                        const items = Array.isArray(data) ? data : (data['@graph'] || [data]);
                        items.forEach(item => {
                            if (item.name && item.offers) {
                                const offer = Array.isArray(item.offers) ? item.offers[0] : item.offers;
                                results.push({
                                    name:  item.name,
                                    price: String(offer.price || ''),
                                    date:  item.dateModified || '',
                                });
                            }
                        });
                    } catch(e) {}
                });
            }

            return results;
        }
    """)

    for r in (raw or []):
        name  = (r.get('name') or '').strip()
        price = parse_price_js(r.get('price') or '')
        date_str = (r.get('date') or '').strip()
        sold_date = None

        if date_str:
            # ISO 8601 形式
            try:
                sold_date = datetime.fromisoformat(date_str.replace('Z', '+00:00')).astimezone(JST)
            except ValueError:
                sold_date = parse_date_from_text(date_str)

        if name and price:
            items.append({'name': name, 'price': price, 'sold_date': sold_date})

    return items


def parse_price_js(text: str) -> int | None:
    digits = re.sub(r'[^\d]', '', str(text))
    return int(digits) if digits else None


# ─────────────────────────── 集計 ───────────────────────────

def aggregate(items: list[dict]) -> list[dict]:
    """
    商品名でグルーピングし、件数・平均価格・最終売れ日を集計。
    同一商品名の表記ゆれを簡易的に正規化（記号・スペースを除去して照合）。
    """
    def normalize(name: str) -> str:
        # 全角→半角、スペース・記号除去で正規化
        n = name.lower()
        n = re.sub(r'[\s\u3000\-・【】「」()（）]', '', n)
        return n

    groups: dict[str, dict] = {}  # normalized_name -> {'display': str, 'prices': [], 'dates': []}

    for item in items:
        key = normalize(item['name'])
        if key not in groups:
            groups[key] = {
                'display': item['name'],
                'prices':  [],
                'dates':   [],
            }
        groups[key]['prices'].append(item['price'])
        if item['sold_date']:
            groups[key]['dates'].append(item['sold_date'])

    result = []
    for key, g in groups.items():
        prices     = g['prices']
        avg_price  = sum(prices) / len(prices)
        count      = len(prices)
        latest     = max(g['dates']).strftime('%Y/%m/%d') if g['dates'] else ''
        price_lbl  = price_range_label(avg_price)

        result.append({
            'name':      g['display'],
            'avg_price': round(avg_price),
            'count':     count,
            'last_sold': latest,
            'price_range': price_lbl,
        })

    # 件数降順でソート
    result.sort(key=lambda x: x['count'], reverse=True)
    return result


# ─────────────────────────── メイン ───────────────────────────

def main():
    config = load_config()

    # ── 1. スクレイピング ──
    raw_items = scrape_mercari(config)

    if not raw_items:
        print('[警告] 商品が1件も取得できませんでした。')
        print('  ・save_research_session.py でログインセッションを保存してください。')
        print('  ・メルカリのページ構造が変わった可能性があります。')
        sys.exit(1)

    # ── 2. 集計 ──
    print('\n[集計中...]')
    aggregated = aggregate(raw_items)
    print(f'  ユニーク商品数: {len(aggregated)} 件')
    print(f'  上位5件:')
    for i, a in enumerate(aggregated[:5], 1):
        print(f'    {i}. {a["name"][:30]}  {a["count"]}件  ¥{a["avg_price"]:,}')

    # ── 3. Google Sheets ──
    print('\n[Google Sheets への書き込み...]')
    creds = get_google_creds(config)

    now_jst    = datetime.now(JST)
    keyword = config.get('keyword', '').strip()
    if keyword:
        sheet_title = f'{keyword}_{now_jst.strftime("%Y-%m")}'
    else:
        sheet_title = f'メルカリ売れ筋_{now_jst.strftime("%Y-%m")}'

    ss_id = create_spreadsheet(creds, sheet_title)

    rows = [
        [
            a['name'],
            a['avg_price'],
            a['count'],
            a['last_sold'],
            a['price_range'],
        ]
        for a in aggregated
    ]
    write_to_sheet(creds, ss_id, sheet_title, rows)

    ss_url = f'https://docs.google.com/spreadsheets/d/{ss_id}'
    print(f'\n✓ 完了！スプレッドシートURL:')
    print(f'  {ss_url}')
    print(f'  シート名: {sheet_title}')
    print(f'  商品数  : {len(aggregated)} 件')
    print(f'  収集数  : {len(raw_items)} 件（SOLD商品）')


if __name__ == '__main__':
    main()
