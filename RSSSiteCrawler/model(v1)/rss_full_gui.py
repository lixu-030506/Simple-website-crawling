import threading
import requests
from bs4 import BeautifulSoup
from readability import Document
from urllib.parse import urljoin, urlparse, urlunparse
import tldextract
import difflib
import webview
import time
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# ---------------------- 配置 ----------------------
GEMINI_API_KEY = "AIzaSyCNVUA07VPfhHfKQk3DxDL8N3bCQXJyYIM"
MAX_PAGES = 500
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

# ---------------------- 全局状态 ----------------------
visited_links = set()
articles = []  # {"title":, "url":, "content":, "content_text":}

# ---------------------- 工具函数 ----------------------
def normalize_url(url):
    parsed = urlparse(url)
    normalized = parsed._replace(query="", fragment="")
    return urlunparse(normalized).rstrip("/")

def is_same_domain(base, target):
    base_domain = tldextract.extract(base).top_domain_under_public_suffix
    target_domain = tldextract.extract(target).top_domain_under_public_suffix
    return base_domain == target_domain

def html_to_text(html):
    return BeautifulSoup(html, "html.parser").get_text("\n", strip=True)

def fix_image_urls(content_html, base_url):
    soup = BeautifulSoup(content_html, "html.parser")
    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            img["src"] = urljoin(base_url, src)
        img["style"] = "max-width:100%;height:auto;margin:5px 0;"
    return str(soup)

# ---------------------- Gemini AI 提取正文 ----------------------
def gemini_extract(html):
    try:
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": GEMINI_API_KEY
        }
        payload = {
            "contents": [{"parts": [{"text": html}]}]
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        result = data.get("candidates", [{}])[0].get("content", "")
        if not result:
            result = html_to_text(html)
        return result
    except Exception as e:
        append_log(f"⚠️ Gemini 提取失败: {e}")
        return html_to_text(html)

# ---------------------- 日志和进度 ----------------------
def append_log(msg):
    print(msg)
    try:
        if webview.windows:
            js = f'document.getElementById("log").innerHTML += "{msg.replace("\"","\\\"")}<br>";' \
                 'document.getElementById("log").scrollTop = document.getElementById("log").scrollHeight;'
            webview.windows[0].evaluate_js(js)
    except:
        pass

def update_progress(val):
    try:
        if webview.windows:
            js = f'document.getElementById("progress").value = {val};'
            webview.windows[0].evaluate_js(js)
    except:
        pass

# ---------------------- 抓取文章 ----------------------
def extract_article(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        r.raise_for_status()
    except Exception as e:
        append_log(f"❌ 请求失败: {url} ({e})")
        return None
    if "text/html" not in r.headers.get("Content-Type", ""):
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    h1 = soup.find("h1")
    title = h1.get_text(strip=True) if h1 else (soup.title.string.strip() if soup.title else url)
    try:
        doc = Document(r.text)
        content_html = doc.summary()
    except:
        content_html = r.text
    if len(html_to_text(content_html)) < 200:
        content_html = gemini_extract(r.text)
    content_html = fix_image_urls(content_html, url)
    content_text = html_to_text(content_html)
    return {"title": f"{title}", "url": url, "content": content_html, "content_text": content_text}

# ---------------------- 去重 ----------------------
def deduplicate_articles(articles):
    unique = []
    texts = []
    for a in articles:
        text_clean = a["content_text"].replace("\n","").replace(" ","")
        duplicate = False
        for t in texts:
            ratio = difflib.SequenceMatcher(None, t, text_clean).ratio()
            if ratio > 0.9:
                duplicate = True
                break
        if not duplicate:
            unique.append(a)
            texts.append(text_clean)
    return unique

# ---------------------- 全站抓取 ----------------------
def get_all_links(base_url):
    to_visit = [base_url]
    all_articles = []
    count = 0
    while to_visit and len(all_articles) < MAX_PAGES:
        url = to_visit.pop(0)
        normalized = normalize_url(url)
        if normalized in visited_links:
            continue
        visited_links.add(normalized)
        article = extract_article(url)
        if article:
            all_articles.append(article)
            append_log(f"📄 抓取: {article['title']}")
            count += 1
            update_progress(int(count / MAX_PAGES * 100))
            try:
                soup = BeautifulSoup(requests.get(url, headers=HEADERS, timeout=10, verify=False).text,"html.parser")
                for a_tag in soup.find_all("a", href=True):
                    link = normalize_url(urljoin(url, a_tag["href"]))
                    if is_same_domain(base_url, link) and link not in visited_links:
                        to_visit.append(link)
            except:
                pass
    all_articles = deduplicate_articles(all_articles)
    update_progress(100)
    return all_articles

# ---------------------- GUI ----------------------
html_template = """
<html>
<head>
<meta charset="utf-8">
<style>
body { font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif'; margin:0; padding:0; height:100%; background:#f0f0f0; color:#000; }
#container { display:flex; height:100vh; }
#left { width:30%; border-right:1px solid #ccc; padding:10px; overflow:auto; background:#f7f7f7; }
#right { flex:1; padding:10px; overflow:auto; background:#fff; }
#url_section { margin-bottom:10px; }
#url_input { width:60%; padding:5px; }
#progress { width:100%; height:15px; margin-bottom:10px; }
#log { height:120px; overflow:auto; border:1px solid #ccc; padding:5px; background:#fff; font-size:12px; margin-top:10px; }
#article_list { list-style:none; padding-left:0; max-height:350px; overflow:auto; background:#fff; border:1px solid #ccc; }
#article_list li { padding:5px; border-bottom:1px solid #eee; cursor:pointer; }
#article_list li:hover { background:#e0e0e0; }
#content { min-height:100px; max-width:900px; margin:0 auto; line-height:1.6; font-size:16px; }
.control { margin-bottom:10px; }
input[type=range] { width:100%; }
.dark-mode body { background:#1e1e1e; color:#f0f0f0; }
.dark-mode #left { background:#2e2e2e; }
.dark-mode #right { background:#252526; }
.dark-mode #article_list li:hover { background:#444; }
</style>
<script>
function showArticle(index){ window.pywebview.api.selectArticle(index); }
function startCrawl(){ var url=document.getElementById("url_input").value; window.pywebview.api.startCrawl(url); }
function toggleTheme(){ document.body.classList.toggle("dark-mode"); }
function updateStyle(){ 
    var content=document.getElementById("content");
    content.style.fontFamily=document.getElementById("fontSelect").value;
    content.style.fontSize=document.getElementById("fontSize").value+'px';
    content.style.lineHeight=document.getElementById("lineHeight").value;
    content.style.backgroundColor=document.getElementById("bgColor").value;
    content.style.color=document.getElementById("textColor").value;
}
</script>
</head>
<body>
<div id="container">
<div id="left">
<div id="url_section" class="control">
<input type="text" id="url_input" placeholder="输入网站 URL">
<button onclick="startCrawl()">开始抓取</button>
<button onclick="toggleTheme()">深色/浅色</button>
</div>
<div class="control">
<label>字体:</label>
<select id="fontSelect" onchange="updateStyle()">
<option>Segoe UI</option>
<option>Arial</option>
<option>Verdana</option>
<option>Times New Roman</option>
<option>Courier New</option>
</select>
</div>
<div class="control">
<label>字号(px):</label>
<input type="range" id="fontSize" min="12" max="32" value="16" onchange="updateStyle()">
</div>
<div class="control">
<label>行高:</label>
<input type="range" id="lineHeight" min="1" max="3" step="0.1" value="1.6" onchange="updateStyle()">
</div>
<div class="control">
<label>背景色:</label>
<input type="color" id="bgColor" value="#ffffff" onchange="updateStyle()">
<label>文字色:</label>
<input type="color" id="textColor" value="#000000" onchange="updateStyle()">
</div>
<progress id="progress" value="0" max="100"></progress>
<ul id="article_list"></ul>
<div id="log"></div>
</div>
<div id="right">
<h2>文章内容</h2>
<div id="content">请选择文章</div>
</div>
</div>
</body>
</html>
"""

def build_article_list_js():
    js = "var list='';"
    for i, a in enumerate(articles):
        safe_title = a["title"].replace('"','&quot;').replace("`","'")
        js += f"list += '<li onclick=\"showArticle({i})\">{safe_title}</li>';"
    js += "document.getElementById('article_list').innerHTML=list;"
    return js

class Api:
    def selectArticle(self, index):
        content = articles[int(index)]["content"].replace("`","'")
        js = f'document.getElementById("content").innerHTML = `{content}`;'
        webview.windows[0].evaluate_js(js)

    def startCrawl(self, url):
        threading.Thread(target=self._crawl_thread, args=(url,), daemon=True).start()

    def _crawl_thread(self, url):
        global articles
        append_log("🚀 开始抓取...")
        articles.clear()
        visited_links.clear()
        articles.extend(get_all_links(url))
        append_log(f"✅ 抓取完成，共 {len(articles)} 篇文章")
        js = build_article_list_js()
        webview.windows[0].evaluate_js(js)

# ---------------------- 主程序 ----------------------
def main():
    api = Api()
    webview.create_window("全站RSS抓取工具", html=html_template, js_api=api, width=1200, height=800)
    webview.start(gui='edgechromium')

if __name__ == "__main__":
    main()