📰 全站 RSS 抓取工具（个人实验版）

版本：model(v2)
主文件路径：E:\RSSSiteCrawler\model(v2)\rss_gui.py
适用环境：Windows 11 + Python 3.13 + Virtual Environment
说明：仅供个人研究及小型网站内容整理使用。

🚀 项目简介

本工具为一个 全站自动 RSS 生成器，可对同域内网页进行爬取、正文提取，并生成 RSS 订阅源。
主要面向个人或小型网站用户，支持部分可视化与 AI 内容优化功能。

✨ 功能特性

✅ 自动爬取同域网站内容（含分页链接）
✅ 自动生成标准 RSS 文件（site_full_rss.xml）
✅ 图形化界面（PyWebView 驱动）
✅ 实时日志与进度条显示
✅ 简单的 AI 正文提取支持（需自备 Gemini API Key）
✅ 自动内容去重与基本排版优化
✅ 内置左右分栏式阅读界面
✅ 深浅主题可切换（部分功能仍在完善）

⚙️ 环境配置

在虚拟环境中安装依赖：

pip install pywebview requests beautifulsoup4 readability-lxml feedgen lxml tldextract fake-useragent

🧠 AI 功能（可选）

AI 功能用于自动补全文章正文，需配置 Google Gemini API。

在代码顶部可填写：

GEMINI_API_KEY = "你的Gemini_API_Key"


⚠️ 注意：原始 API Key 已移除。请自行申请并谨慎保管。
若未填写，程序仍可正常运行，但无法进行 AI 正文提取。

🖥️ 启动方式
python "E:\RSSSiteCrawler\model(v2)\rss_gui.py"


启动后会打开图形界面，操作方式如下：

区域	功能
输入栏	输入目标网站 URL（仅支持小型、结构清晰的网站）
日志区	实时显示抓取状态与错误信息
进度条	抓取进度可视化
左侧文章列表	自动生成的文章目录
右侧阅读区	显示正文内容
主题设置	支持字体与背景模式调整（部分功能暂未完成）
📡 RSS 输出

生成文件路径：

E:\RSSSiteCrawler\model(v2)\site_full_rss.xml


生成后可通过 RSS 阅读器导入使用。

⚠️ 当前限制与状态
模块	状态
GUI 启动	✅ 可用
网站爬取	✅ 可用（推荐小型网站）
AI 正文提取	⚙️ 可用（需有效 Gemini Key）
深浅主题切换	⚙️ 部分功能实现
RSS 生成	✅ 可用
打包为 EXE	❌ 当前不可用（PyWebView 打包兼容性问题）
🧱 关于 EXE 打包（暂不可用）

⚠️ 由于 PyWebView 与 Chromium 的兼容问题，当前 无法成功生成可执行 EXE 文件。
尝试通过以下命令会导致应用无法启动：

pyinstaller --onefile --windowed --noconsole --name "全站RSS生成器" "E:\RSSSiteCrawler\model(v2)\rss_gui.py"


建议：
直接使用 Python 运行脚本，而非打包为 EXE。

🧭 使用建议

仅适用于 个人学习、小型网站或自建博客 的信息整理。
不建议用于大规模网站或商业抓取用途。
请尊重目标网站的 robots.txt 及版权要求。
若目标网页结构复杂，可自行修改 extract_article_content() 提取逻辑。

🌙 后续可拓展方向

 深浅主题按钮完善
 AI 摘要与关键词提取
 本地缓存与断点续抓
 导出为 Markdown / PDF
 RSS 在线服务端发布

📄 版权与免责声明

本项目仅用于个人研究与技术学习。
作者不对任何因滥用或非法抓取造成的后果承担责任。
请确保使用符合相关网站的法律与道德规范。
