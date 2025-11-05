import threading
import requests
from bs4 import BeautifulSoup
from readability import Document
from urllib.parse import urljoin, urlparse, urlunparse
import tldextract
import webview
import json

# ---------------------- 配置 ----------------------
GEMINI_API_KEY = ""
MAX_PAGES = 500

# ---------------------- 全局状态 ----------------------
visited_links = set()
articles = []  # {"title":, "url":, "content":, "content_text":}
theme_settings = {
    "background_color": "#1e1e1e",
    "font_color": "#f5f5f5",
    "font_family": "Segoe UI, Tahoma, Geneva, Verdana, sans-serif",
    "font_size": "14px",
    "line_height": "1.6"
}

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
    return str(soup)

# ---------------------- Gemini AI 提取正文 ----------------------
def gemini_extract(url, html):
    try:
        endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": GEMINI_API_KEY
        }
        data = {
            "contents": [
                {"parts": [{"text": html}]}
            ]
        }
        response = requests.post(endpoint, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        res_json = response.json()
        text_parts = res_json.get("candidates", [{}])[0].get("content", [])
        return "\n".join([p.get("text", "") for p in text_parts])
    except Exception as e:
        append_log(f"⚠️ Gemini 提取失败: {e}")
        return html_to_text(html)

# ---------------------- 日志和进度 ----------------------
def append_log(msg):
    print(msg)
    try:
        if webview.windows:
            js = f'document.getElementById("log").innerHTML += {json.dumps(msg+"<br>")};' \
                 f'document.getElementById("log").scrollTop = document.getElementById("log").scrollHeight;'
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
        r = requests.get(url, timeout=10, verify=False)
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

    # 使用 Gemini 提取正文
    if len(html_to_text(content_html)) < 200:
        content_html = gemini_extract(url, r.text)

    content_html = fix_image_urls(content_html, url)
    content_text = html_to_text(content_html)

    return {"title": f"{title}", "url": url, "content": content_html, "content_text": content_text}

def deduplicate_articles(articles):
    seen = {}
    result = []
    for a in articles:
        key = a["content_text"][:500]  # 前500字符去重
        if key in seen:
            if len(a["content_text"]) > len(seen[key]["content_text"]):
                seen[key] = a
        else:
            seen[key] = a
    result.extend(seen.values())
    return result

def get_all_links(base_url):
    to_visit = [base_url]
    all_articles = []
    count = 0
    while to_visit and len(all_articles) < MAX_PAGES:
        url = to_visit.pop()
        normalized = normalize_url(url)
        if normalized in visited_links:
            continue
        visited_links.add(normalized)
        article = extract_article(url)
        if article:
            all_articles.append(article)
            append_log(f"📄 抓取: {article['title']} ({url})")
            count += 1
            update_progress(int(count / MAX_PAGES * 100))
            try:
                soup = BeautifulSoup(requests.get(url, timeout=10, verify=False).text, "html.parser")
                for a in soup.find_all("a", href=True):
                    link = normalize_url(urljoin(url, a["href"]))
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
body {{ font-family: {font_family}; margin:0; padding:0; background:{bg}; color:{fc}; }}
#container {{ display:flex; height:100vh; }}
#left {{ width:35%; border-right:1px solid #555; padding:10px; overflow:auto; background:#2c2c2c; }}
#right {{ flex:1; padding:10px; overflow:auto; background:{bg}; }}
#url_section {{ margin-bottom:10px; }}
#url_input {{ width:70%; padding:5px; }}
#progress {{ width:100%; height:20px; margin-bottom:10px; }}
#log {{ height:150px; overflow:auto; border:1px solid #555; padding:5px; background:#1e1e1e; }}
#article_list {{ list-style:none; padding-left:0; max-height:300px; overflow:auto; background:#1e1e1e; border:1px solid #555; }}
#article_list li {{ padding:5px; border-bottom:1px solid #444; cursor:pointer; }}
#article_list li:hover {{ background:#444; }}
#content {{ min-height:100px; }}
</style>
<script>
function showArticle(index){{ window.pywebview.api.selectArticle(index); }}
function startCrawl(){{ var url = document.getElementById("url_input").value; window.pywebview.api.startCrawl(url); }}
</script>
</head>
<body>
<div id="container">
    <div id="left">
        <div id="url_section">
            <input type="text" id="url_input" placeholder="输入网站 URL">
            <button onclick="startCrawl()">开始抓取</button>
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
""".format(
    font_family=theme_settings["font_family"],
    bg=theme_settings["background_color"],
    fc=theme_settings["font_color"]
)

def build_article_list_js():
    js = "var list='';"
    for i, a in enumerate(articles):
        safe_title = json.dumps(a["title"])
        js += f"list += '<li onclick=\"showArticle({i})\">'+{safe_title}+'</li>';"
    js += "document.getElementById('article_list').innerHTML=list;"
    return js

class Api:
    def selectArticle(self, index):
        article = articles[int(index)]
        content = article["content"]
        css = f"font-size:{theme_settings['font_size']};line-height:{theme_settings['line_height']};" \
              f"background:{theme_settings['background_color']};color:{theme_settings['font_color']};" \
              f"font-family:{theme_settings['font_family']};"
        safe_content = json.dumps(content)
        js = f'document.getElementById("content").style="{css}";' \
             f'document.getElementById("content").innerHTML={safe_content};'
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
