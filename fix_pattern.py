with open('/Users/m2mac/market_research.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 楽天パターン修正
old1 = """        patterns = [
            r'(\\d{1,2},\\d{3})円',   # 1,980円 形式
            r'¥(\\d{1,2},\\d{3})',     # ¥1,980 形式
            r'"price":(\\d{3,5})',    # JSON形式 "price":1980
            r'(\\d{4,5})円',          # 12800円 形式
        ]"""
new1 = """        patterns = [
            r'([\\d,]+)円',
            r'"price"\\s*:\\s*(\\d+)',
        ]"""

# ヤフショパターン修正
old2 = """        patterns = [
            r'"price":(\\d{3,5})',      # JSON形式
            r'"salePrice":(\\d{3,5})',  # セール価格JSON
            r'(\\d{1,2},\\d{3})円',      # 1,980円 形式
            r'¥(\\d{1,2},\\d{3})',       # ¥1,980 形式
            r'(\\d{4,5})円',            # 12800円 形式
        ]"""
new2 = """        patterns = [
            r'([\\d,]+)円',
            r'"price"\\s*:\\s*(\\d+)',
        ]"""

content = content.replace(old1, new1)
content = content.replace(old2, new2)

with open('/Users/m2mac/market_research.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("修正完了")
# 確認
import re
matches = re.findall(r'patterns = \[.*?\]', content, re.DOTALL)
for m in matches[:4]:
    print(m[:100])
