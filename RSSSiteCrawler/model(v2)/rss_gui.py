import threading
import requests
from bs4 import BeautifulSoup
from readability import Document
from urllib.parse import urljoin, urlparse, urlunparse
import tldextract
from feedgen.feed import FeedGenerator
from http.server import HTTPServer, BaseHTTPRequestHandler
import webview
import hashlib
import ssl

# ---------------------- 配置 ----------------------
GEMINI_API_KEY = ""
RSS_FILENAME = "site_full_rss.xml"
LOCAL_RSS_URL = "http://localhost:8000/rss"
MAX_PAGES = 500

# ---------------------- 全局状态 ----------------------
visited_links = set()
articles = []
rss_cache = ""
theme_settings = {
    "font_size": "16px",
    "line_height": "1.8",
    "background_color": "#ffffff",
    "font_family": "Segoe UI, sans-serif"
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

def fix_image_urls(soup, base_url):
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-original")
        if src:
            img["src"] = urljoin(base_url, src)
            img["style"] = "max-width:100%;height:auto;"
    return soup

def append_log(msg):
    print(msg)
    try:
        if webview.windows:
            js = f'document.getElementById("log").innerHTML += "{msg}<br>";' \
                 f'document.getElementById("log").scrollTop=document.getElementById("log").scrollHeight;'
            webview.windows[0].evaluate_js(js)
    except:
        pass

def update_progress(val):
    try:
        if webview.windows:
            js = f'document.getElementById("progress").value={val:.2f};' \
                 f'document.getElementById("progress_text").innerText="进度: {val:.2f}%";'
            webview.windows[0].evaluate_js(js)
    except:
        pass

# ---------------------- AI 提取正文 ----------------------
def gemini_extract(url, html):
    try:
        headers = {"Authorization": f"Bearer {GEMINI_API_KEY}"}
        data = {"input": html, "task": "extract_article"}
        response = requests.post("https://api.gemini.com/v1/extract", headers=headers, json=data, timeout=15)
        response.raise_for_status()
        content = response.json().get("content","")
        if content.strip():
            return content
        return html
    except Exception as e:
        append_log(f"⚠️ Gemini 提取失败: {e}")
        return html

# ---------------------- 文章抓取 ----------------------
def extract_title(soup, url):
    for selector in ['h1','h2','h3']:
        tag = soup.select_one(selector)
        if tag and tag.get_text(strip=True):
            return tag.get_text(strip=True)
    og = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name":"twitter:title"})
    if og and og.get("content"):
        return og["content"]
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return url.split("/")[-1] or url

def extract_article(url):
    try:
        r = requests.get(url, timeout=10, headers={'User-Agent':'Mozilla/5.0'}, verify=False)
        r.raise_for_status()
        if "text/html" not in r.headers.get("Content-Type",""):
            return None
        soup = BeautifulSoup(r.text,"html.parser")
        title = extract_title(soup,url)
        try:
            doc = Document(r.text)
            content_html = doc.summary()
        except:
            content_html = str(soup)
        soup_content = BeautifulSoup(content_html,"html.parser")
        soup_content = fix_image_urls(soup_content,url)
        content_text = html_to_text(str(soup_content))
        if len(content_text)<200:
            ai_content = gemini_extract(url,r.text)
            soup_content = BeautifulSoup(ai_content,"html.parser")
            soup_content = fix_image_urls(soup_content,url)
            content_text = html_to_text(str(soup_content))
        return {"title":f"{title} ({url})","url":url,"content":str(soup_content),"content_text":content_text}
    except Exception as e:
        append_log(f"❌ 请求失败: {url} ({e})")
        return None

def deduplicate_articles(arts):
    seen = {}
    result = []
    for a in arts:
        key = hashlib.md5(a["content_text"].encode("utf-8")).hexdigest()
        if key in seen:
            if len(a["content_text"])>len(seen[key]["content_text"]):
                seen[key]=a
        else:
            seen[key]=a
    result.extend(seen.values())
    return result

# ---------------------- 全站抓取 ----------------------
def get_all_links(base_url):
    to_visit = [base_url]
    all_articles = []
    count = 0
    while to_visit and len(all_articles)<MAX_PAGES:
        url = to_visit.pop(0)
        normalized = normalize_url(url)
        if normalized in visited_links:
            continue
        visited_links.add(normalized)
        article = extract_article(url)
        if article:
            all_articles.append(article)
            count += 1
            append_log(f"📄 抓取: {article['title']}")
            update_progress(count/MAX_PAGES*100)
            try:
                soup = BeautifulSoup(requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, verify=False).text,"html.parser")
                for a in soup.find_all("a", href=True):
                    link = normalize_url(urljoin(url, a["href"]))
                    if is_same_domain(base_url, link) and link not in visited_links:
                        to_visit.append(link)
            except:
                pass
    all_articles = deduplicate_articles(all_articles)
    update_progress(100)
    return all_articles

# ---------------------- RSS生成 ----------------------
def generate_rss(base_url, articles):
    fg = FeedGenerator()
    fg.title(f"{base_url} 全站 RSS")
    fg.link(href=base_url)
    fg.description("自动生成全站RSS")
    for art in articles:
        fe = fg.add_entry()
        fe.title(art["title"])
        fe.link(href=art["url"])
        fe.content(art["content"], type="CDATA")
    rss_str = fg.rss_str(pretty=True).decode("utf-8")
    with open(RSS_FILENAME,"w",encoding="utf-8") as f:
        f.write(rss_str)
    append_log(f"📄 RSS 已生成: {RSS_FILENAME}")
    return rss_str

# ---------------------- 本地 RSS 服务 ----------------------
class RSSHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global rss_cache
        if self.path=="/rss":
            if not rss_cache:
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b"RSS not ready")
                return
            self.send_response(200)
            self.send_header("Content-Type","application/rss+xml; charset=utf-8")
            self.end_headers()
            self.wfile.write(rss_cache.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

def start_rss_server():
    server = HTTPServer(("localhost",8000),RSSHandler)
    append_log(f"📡 本地 RSS 服务: {LOCAL_RSS_URL}")
    server.serve_forever()

# ---------------------- GUI ----------------------
html_template = """<html>
<head><meta charset="utf-8"><style>
body{font-family:'Segoe UI',sans-serif;margin:0;padding:0;height:100%;background:#f0f0f0;}
#container{display:flex;height:100vh;}
#left{width:35%;border-right:1px solid #ccc;padding:10px;display:flex;flex-direction:column;background:#f7f7f7;}
#url_section{margin-bottom:10px;}
#url_input{width:70%;padding:5px;}
#progress{width:100%;height:20px;margin-bottom:5px;}
#progress_text{margin-bottom:5px;}
#log{height:120px;overflow:auto;border:1px solid #ccc;padding:5px;background:#fff;margin-bottom:10px;flex-shrink:0;}
#article_list{list-style:none;padding-left:0;overflow:auto;flex:1;background:#fff;border:1px solid #ccc;}
#article_list li{padding:5px;border-bottom:1px solid #eee;cursor:pointer;}
#article_list li:hover{background:#e0e0e0;}
#right{flex:1;padding:20px;overflow:auto;background:#fff;}
#content{line-height:1.8;font-size:16px;font-family:Segoe UI, sans-serif;}
#content img{max-width:100%;display:block;margin:10px 0;}
#theme_controls{margin-top:10px;padding:5px;border:1px solid #ccc;background:#e9e9e9;}
</style>
<script>
function showArticle(index){window.pywebview.api.selectArticle(index);}
function startCrawl(){var url=document.getElementById("url_input").value;window.pywebview.api.startCrawl(url);}
function applyTheme(){var fsize=document.getElementById("font_size").value;var lheight=document.getElementById("line_height").value;var bgcolor=document.getElementById("bgcolor").value;var ffamily=document.getElementById("font_family").value;window.pywebview.api.applyTheme(fsize,lheight,bgcolor,ffamily);}
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
<div id="progress_text">进度: 0%</div>
<ul id="article_list"></ul>
<div id="log"></div>
<div id="theme_controls">
<h4>阅读主题</h4>
字体大小:<input type="text" id="font_size" value="16px">
行距:<input type="text" id="line_height" value="1.8">
背景色:<input type="text" id="bgcolor" value="#ffffff">
字体:<input type="text" id="font_family" value="Segoe UI, sans-serif">
<button onclick="applyTheme()">应用</button>
</div>
</div>
<div id="right">
<h2>文章内容</h2>
<div id="content">请选择文章</div>
</div>
</div>
</body></html>
"""

def build_article_list_js():
    js = "var list='';"
    for i,a in enumerate(articles):
        safe_title = a["title"].replace('"','&quot;')
        js += f"list+='<li onclick=\"showArticle({i})\">{safe_title}</li>';"
    js += "document.getElementById('article_list').innerHTML=list;"
    return js

class Api:
    def selectArticle(self,index):
        content = articles[int(index)]["content"]
        css = f"font-size:{theme_settings['font_size']};line-height:{theme_settings['line_height']};background:{theme_settings['background_color']};font-family:{theme_settings['font_family']};"
        js = f'document.getElementById("content").style="{css}";document.getElementById("content").innerHTML=`{content}`;'
        webview.windows[0].evaluate_js(js)

    def startCrawl(self,url):
        threading.Thread(target=self._crawl_thread,args=(url,),daemon=True).start()

    def applyTheme(self,fsize,lheight,bgcolor,ffamily):
        theme_settings["font_size"]=fsize
        theme_settings["line_height"]=lheight
        theme_settings["background_color"]=bgcolor
        theme_settings["font_family"]=ffamily
        if articles:
            self.selectArticle(0)

    def _crawl_thread(self,url):
        global articles,rss_cache,visited_links
        append_log("🚀 开始抓取...")
        articles.clear()
        visited_links.clear()
        rss_cache=""
        arts = get_all_links(url)
        articles.extend(arts)
        append_log(f"✅ 抓取完成，共 {len(articles)} 篇文章")
        rss_cache = generate_rss(url, articles)
        js = build_article_list_js()
        webview.windows[0].evaluate_js(js)

def main():
    threading.Thread(target=start_rss_server,daemon=True).start()
    api = Api()
    webview.create_window("全站RSS抓取工具",html=html_template,js_api=api,width=1200,height=800)
    webview.start(gui='edgechromium')

if __name__=="__main__":

    main()
