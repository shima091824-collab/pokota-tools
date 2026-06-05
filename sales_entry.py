#!/usr/bin/env python3
# sales_entry.py — Yahoo!フリマCSV + メルカリスクレイピング → スプレッドシート自動入力
import os, re, sys, csv, json, datetime
from zoneinfo import ZoneInfo
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES           = ['https://www.googleapis.com/auth/spreadsheets']
CREDENTIALS_FILE = os.path.expanduser('~/sales_entry_credentials.json')
TOKEN_FILE       = os.path.expanduser('~/sales_entry_token.json')
SPREADSHEET_ID   = '1XnGiqlGvIDfTyCOUXecclDJaBm_J6Gyg12mvZuKZFPg'
SHEET_NAME       = '2026売上管理'
EXCLUDE_IDS      = {
    'z588484752', 'z588782316', 'z588333714', 'z588334936',
}
JST              = ZoneInfo('Asia/Tokyo')
INVENTORY_FILE   = os.path.expanduser('~/inventory.json')

# ──────────────────────────────────────────────
# 在庫管理（FIFO）
# ──────────────────────────────────────────────

def load_inventory():
    """inventory.json を読み込む。なければデフォルト値で新規作成。"""
    if os.path.exists(INVENTORY_FILE):
        with open(INVENTORY_FILE, encoding='utf-8') as f:
            return json.load(f)
    # 初回起動時：現在の仕入れ値でデフォルト在庫を作成（在庫数=9999=実質無制限）
    default = {
        'スリモアコーヒー':                 [{"cost": 2745, "stock": 9999, "date": "2026-04-01"}],
        'ロートV5':                         [{"cost": 1142, "stock": 9999, "date": "2026-04-01"}],
        'スカルプDまつ毛美容液':            [{"cost": 2128, "stock": 9999, "date": "2026-04-01"}],
        'スカルプD 薬用オイリーシャンプー': [{"cost": 2447, "stock": 9999, "date": "2026-04-01"}],
        'アパコート':                       [{"cost": 1397, "stock": 9999, "date": "2026-04-01"}],
    }
    save_inventory(default)
    print(f'  [在庫] inventory.json を新規作成しました: {INVENTORY_FILE}')
    return default

def save_inventory(inventory):
    """inventory.json に書き込み、スプレッドシートにも同期する。"""
    with open(INVENTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(inventory, f, ensure_ascii=False, indent=2)
    try:
        import gspread
        from google.oauth2.service_account import Credentials as SACredentials
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = SACredentials.from_service_account_file(
            os.path.expanduser('~/credentials.json'), scopes=scopes)
        gc = gspread.authorize(creds)
        ws = gc.open_by_key(SPREADSHEET_ID).worksheet('在庫管理')
        ws.clear()
        ws.update(values=[['商品名', '仕入れ値', '仕入れ日', '在庫数']], range_name='A1')
        rows = []
        for name, lots in inventory.items():
            for lot in lots:
                rows.append([name, lot['cost'] if lot.get('stock', 0) != 0 else '', lot['date'], lot.get('stock', '')])
        if rows:
            ws.update(values=rows, range_name='A2')
        print('  [在庫] スプレッドシート同期完了')
    except Exception as e:
        print(f'  [在庫警告] スプレッドシート同期エラー: {e}')

def get_cost_and_consume(title, inventory, qty=1):
    """
    商品名からロットを特定し、仕入れ値を返す。
    在庫をqty分消費し（FIFOで古いロットから）、inventory を更新する。
    在庫がないキーワードにはマッチしない。
    """
    for keyword, lots in inventory.items():
        if keyword in title:
            # 有効ロット（stock > 0）を日付順に取得
            active = [lot for lot in lots if lot['stock'] > 0]
            if not active:
                print(f'  [在庫警告] 「{keyword}」の在庫がゼロです')
                cost = lots[-1]['cost'] if lots else 0
                return cost if cost != 0 else ''

            # 先頭ロット（最古）から消費
            remaining = qty
            cost = active[0]['cost']  # 最古ロットの仕入れ値を使用
            for lot in active:
                if remaining <= 0:
                    break
                consume = min(lot['stock'], remaining)
                lot['stock'] -= consume
                remaining -= consume
                if lot['stock'] == 0:
                    print(f'  [在庫] 「{keyword}」ロット {lot["date"]} ¥{lot["cost"]} が完売 → 次ロットへ切替')

            if remaining > 0:
                print(f'  [在庫警告] 「{keyword}」在庫不足（{remaining}個分不足）')
            return cost

    return ''  # マッチなし

def show_inventory_summary(inventory):
    """在庫状況をターミナルに表示。"""
    print('\n── 在庫状況 ──────────────────────')
    for keyword, lots in inventory.items():
        total = sum(l['stock'] for l in lots if l['stock'] > 0)
        active = [l for l in lots if l['stock'] > 0]
        if active:
            current = active[0]
            print(f'  {keyword}: 計{total}個 | 現在ロット ¥{current["cost"]} ({current["date"]}) 残{current["stock"]}個')
        else:
            print(f'  {keyword}: ⚠️ 在庫ゼロ')
    print('──────────────────────────────────\n')

# ──────────────────────────────────────────────
# Google Sheets
# ──────────────────────────────────────────────

def get_sheets_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
    return build('sheets', 'v4', credentials=creds).spreadsheets()

def get_existing_ids(sheets):
    result = sheets.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f'{SHEET_NAME}!B:B'
    ).execute()
    rows = result.get('values', [])
    return {r[0].strip() for r in rows if r and r[0].strip()}

# ──────────────────────────────────────────────
# データ処理
# ──────────────────────────────────────────────

def normalize_date(raw):
    raw = raw.strip()
    m = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日 (\d{1,2})時(\d{2})分', raw)
    if m:
        return f"{m.group(1)}/{int(m.group(2)):02d}/{int(m.group(3)):02d} {int(m.group(4)):02d}:{m.group(5)}"
    m = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日 (\d{1,2}):(\d{2})', raw)
    if m:
        return f"{m.group(1)}/{int(m.group(2)):02d}/{int(m.group(3)):02d} {int(m.group(4)):02d}:{m.group(5)}"
    m = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', raw)
    if m:
        return f"{m.group(1)}/{int(m.group(2)):02d}/{int(m.group(3)):02d}"
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', raw)
    if m:
        return f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
    return raw

def parse_int(val):
    val = val.strip().replace(',', '')
    if val == '-' or val == '':
        return 0
    return int(re.sub(r'[^\d]', '', val))

def fetch_yahoo_csv(csv_path):
    sales = []
    # Shift-JIS → UTF-8(BOM含む) の順で文字コードを自動判別
    for enc in ('shift-jis', 'cp932', 'utf-8-sig'):
        try:
            with open(csv_path, encoding=enc) as f:
                f.read(1024)
            break
        except UnicodeDecodeError:
            continue
    else:
        enc = 'utf-8'
    with open(csv_path, encoding=enc) as f:
        reader = csv.DictReader(f)
        for row in reader:
            tid    = row['商品ID'].strip()
            title  = row['取扱内容'].strip()
            status = row.get('状態', '').strip()
            if not tid or tid == '-' or not title or tid in EXCLUDE_IDS:
                continue
            if status == 'キャンセル':
                continue
            date    = normalize_date(row['取扱日'])
            price   = parse_int(row['決済金額'])
            fee     = parse_int(row['販売手数料'])
            sales.append({
                'platform': 'ヤフーフリマ',
                'id': tid,
                'date': date,
                'title': title,
                'price': price,
                'fee': fee,
                'shipping': 160,
                'status': status,
            })
    return sales

def fetch_mercari():
    from playwright.sync_api import sync_playwright
    import re as re2
    sales = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=os.path.expanduser('~/mercari_state.json'))
        page = context.new_page()
        try:
            page.goto('https://jp.mercari.com/todos', wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(5000)
            links = page.query_selector_all('a')
            transaction_ids = []
            for link in links:
                href = link.get_attribute('href') or ''
                m = re2.search(r'/transaction/(m[0-9]+)', href)
                if m and m.group(1) not in transaction_ids:
                    transaction_ids.append(m.group(1))
            print(f'  メルカリ取引ID: {len(transaction_ids)}件')
            for tid in transaction_ids:
                try:
                    page.goto(f'https://jp.mercari.com/transaction/{tid}', wait_until='networkidle', timeout=30000)
                    page.wait_for_timeout(8000)
                    text = page.inner_text('body')
                    name = re2.search(r'取引情報\n(.+)', text)
                    price_m = re2.search(r'商品代金\n¥([0-9,]+)', text)
                    fee_m = re2.search(r'販売手数料\n¥([0-9,]+)', text)
                    date_m = re2.search(r'購入日時\n([0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日 [0-9]{1,2}:[0-9]{2})', text)
                    if not name or not price_m:
                        print(f'  [skip] {tid}')
                        continue
                    title = name.group(1).strip()
                    price = int(price_m.group(1).replace(',', ''))
                    fee = int(fee_m.group(1).replace(',', '')) if fee_m else round(price * 0.10)
                    date = normalize_date(date_m.group(1)) if date_m else ''
                    if not date:
                        print(f'  [skip - no date] {tid}')
                        continue
                    sales.append({
                        'platform': 'メルカリ',
                        'id': tid,
                        'date': date,
                        'title': title,
                        'price': price,
                        'fee': fee,
                        'shipping': 160,
                        'status': 'メルカリ',
                    })
                except Exception as e:
                    print(f'  [Mercari skip] {tid}: {e}')
        except Exception as e:
            print(f'  [Mercari error] {e}')
        finally:
            browser.close()
    return sales

def detect_quantity(title):
    # （×2）や(×2)、（x2）など末尾カッコ表記を優先して拾う
    m = re.search(r'[（(][×x×](\d+)[）)]', title)
    if m:
        return int(m.group(1))
    return 1

def append_rows(sheets, new_sales, inventory):
    result = sheets.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f'{SHEET_NAME}!A:A'
    ).execute()
    existing = result.get('values', [])
    next_row = len(existing) + 1
    rows_to_write = []
    for s in new_sales:
        qty  = detect_quantity(s['title'])
        cost = get_cost_and_consume(s['title'], inventory, qty)
        row = [
            "'" + s['date'], s['id'], s['title'], s['platform'],
            s['price'], s['fee'], cost, qty, s['shipping'],
            None, None,
            s['status'],
        ]
        rows_to_write.append(row)
    if not rows_to_write:
        return 0
    rows_to_write.sort(key=lambda x: x[0].lstrip("'"))
    for i, row in enumerate(rows_to_write):
        r = next_row + i
        row[9]  = f'=E{r}-F{r}-I{r}-G{r}*H{r}'
        row[10] = f'=IF(E{r}>0,ROUND(J{r}/E{r}*100,2),"")'
    sheets.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f'{SHEET_NAME}!A{next_row}',
        valueInputOption='USER_ENTERED',
        body={'values': rows_to_write}
    ).execute()
    return len(rows_to_write)

# ──────────────────────────────────────────────
# メイン
# ──────────────────────────────────────────────

def find_yahoo_csv():
    """~/Downloads から最新の Yahoo!フリマ CSVを自動検索する。"""
    import glob
    downloads = os.path.expanduser('~/Downloads')
    # saleslist*.csv を対象
    candidates = glob.glob(os.path.join(downloads, 'saleslist*.csv'))
    if not candidates:
        return None
    # 更新日時が最新のものを返す
    return max(candidates, key=os.path.getmtime)

LOCK_FILE = os.path.expanduser('~/sales_entry.lock')

def acquire_lock():
    """二重起動防止ロック。既に起動中なら False を返す。"""
    if os.path.exists(LOCK_FILE):
        with open(LOCK_FILE) as f:
            pid = f.read().strip()
        # プロセスが実際に生きているか確認
        try:
            os.kill(int(pid), 0)
            return False  # 既に起動中
        except (ProcessLookupError, ValueError):
            pass  # プロセスは死んでいる → ロックファイルが残骸
    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))
    return True

def release_lock():
    try:
        os.remove(LOCK_FILE)
    except FileNotFoundError:
        pass

def main():
    print('=== sales_entry.py ===')
    if not acquire_lock():
        print('⚠️  既に起動中です。二重起動を防止しました。')
        sys.exit(0)
    try:
        _main()
    finally:
        release_lock()

def _main():
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    else:
        csv_path = find_yahoo_csv()

    # 在庫読み込み
    inventory = load_inventory()
    show_inventory_summary(inventory)

    sheets = get_sheets_service()
    existing_ids = get_existing_ids(sheets)
    print(f'既存取引ID: {len(existing_ids)}件')

    all_sales = []

    if csv_path:
        print(f'\n[1/2] Yahoo!フリマ CSV読み込み中... ({os.path.basename(csv_path)})')
        yahoo_sales = fetch_yahoo_csv(csv_path)
        print(f'  -> {len(yahoo_sales)}件取得')
        all_sales.extend(yahoo_sales)
    else:
        print('\n[1/2] Yahoo!フリマ CSVなし（スキップ）')

    print('\n[2/2] メルカリ 取得中...')
    mercari_sales = fetch_mercari()
    print(f'  -> {len(mercari_sales)}件取得')
    all_sales.extend(mercari_sales)

    new_sales = [s for s in all_sales if s['id'] and s['id'] not in existing_ids]
    print(f'\n未入力件数: {len(new_sales)}件')

    if new_sales:
        written = append_rows(sheets, new_sales, inventory)
        # 在庫ファイルを保存（消費後）
        save_inventory(inventory)
        print(f'完了: {written}件追記しました')
        print('\n── 処理後在庫 ───────────────────────')
        show_inventory_summary(inventory)
    else:
        print('追記対象なし')

if __name__ == '__main__':
    main()
