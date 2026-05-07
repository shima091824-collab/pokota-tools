from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1280,900")
options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=options)

keyword = "スリモアコーヒー"

# ヤフフリ確認
print("=== ヤフフリ ===")
driver.get(f"https://paypayfleamarket.yahoo.co.jp/search/?query={keyword}&sold=true")
time.sleep(4)
print("タイトル:", driver.title)
print("URL:", driver.current_url)
print("ページ文字数:", len(driver.page_source))
print("item/含む数:", driver.page_source.count('/item/'))

# 楽天確認
print("\n=== 楽天 ===")
driver.get(f"https://search.rakuten.co.jp/search/mall/{keyword}/?s=2")
time.sleep(3)
print("タイトル:", driver.title)
print("URL:", driver.current_url)
print("ページ文字数:", len(driver.page_source))

# ヤフショ確認
print("\n=== ヤフショ ===")
driver.get(f"https://shopping.yahoo.co.jp/search?p={keyword}&sort=price&order=a")
time.sleep(3)
print("タイトル:", driver.title)
print("URL:", driver.current_url)
print("ページ文字数:", len(driver.page_source))

driver.quit()
print("\n診断完了")
