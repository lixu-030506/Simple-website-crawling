import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

print("✅ 环境检测中...")

url = "https://example.com"
r = requests.get(url)
soup = BeautifulSoup(r.text, "html.parser")

print("网页标题：", soup.title.string)

# 创建RSS对象
fg = FeedGenerator()
fg.title("测试RSS")
fg.link(href=url)
fg.description("这是一个测试RSS")

# 正确写法：先获取 entry 对象
entry = fg.add_entry()
entry.title("测试文章")
entry.link(href=url)
entry.description("正文内容")

# 生成RSS文件
fg.rss_file("test_feed.xml")

print("✅ RSS已生成：test_feed.xml")