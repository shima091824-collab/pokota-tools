from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re, time

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1280,900")
options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=options)
keyword = "スリモアコーヒー"

# 楽天
print("=== 楽天：価格らしい文字列を抽出 ===")
driver.get(f"https://search.rakuten.co.jp/search/mall/{keyword}/?s=2")
time.sleep(3)
src = driver.page_source
# 「円」前後の数字を抜き出す
hits = re.findall(r'[\d,]{3,8}円', src)
print("「円」パターン:", hits[:20])
# ¥マーク
hits2 = re.findall(r'¥[\d,]{3,8}', src)
print("「¥」パターン:", hits2[:20])
# price JSON
hits3 = re.findall(r'"price"\s*:\s*(\d+)', src)
print("JSONパターン:", hits3[:20])

# ヤフショ
print("\n=== ヤフショ：価格らしい文字列を抽出 ===")
driver.get(f"https://shopping.yahoo.co.jp/search?p={keyword}&sort=price&order=a")
time.sleep(3)
src2 = driver.page_source
hits4 = re.findall(r'[\d,]{3,8}円', src2)
print("「円」パターン:", hits4[:20])
hits5 = re.findall(r'¥[\d,]{3,8}', src2)
print("「¥」パターン:", hits5[:20])
hits6 = re.findall(r'"price"\s*:\s*(\d+)', src2)
print("JSONパターン:", hits6[:20])
hits7 = re.findall(r'"salePrice"\s*:\s*(\d+)', src2)
print("salePriceパターン:", hits7[:20])

driver.quit()
