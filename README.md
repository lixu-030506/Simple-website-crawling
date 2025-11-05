<!DOCTYPE html>
<h1>📰 全站 RSS 抓取工具（个人实验版）</h1>

<p><strong>版本</strong>： <code>model(v2)</code><br>
<strong>主文件路径</strong>： <code>E:\RSSSiteCrawler\model(v2)\rss_gui.py</code><br>
<strong>适用环境</strong>： Windows 11 + Python 3.13 + Virtual Environment<br>
<strong>说明</strong>： 仅供个人研究及小型网站内容整理使用。</p>

<hr>

<h2>🚀 项目简介</h2>

<p>本工具是一个 <strong>全站自动 RSS 生成器</strong>，可对同域内网页进行爬取、正文提取，并生成标准 RSS 订阅源。<br>
主要面向 <strong>个人用户</strong> 或 <strong>小型网站</strong>，支持部分可视化界面与 AI 内容优化功能。</p>

<hr>

<h2>✨ 功能特性</h2>

<table>
    <thead>
        <tr>
            <th>功能</th>
            <th>状态</th>
            <th>说明</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>自动爬取同域网站内容（含分页链接）</td>
            <td>✅</td>
            <td>支持深度链接发现</td>
        </tr>
        <tr>
            <td>自动生成标准 RSS 文件（<code>site_full_rss.xml</code>）</td>
            <td>✅</td>
            <td>符合 RSS 2.0 规范</td>
        </tr>
        <tr>
            <td>图形化界面（PyWebView 驱动）</td>
            <td>✅</td>
            <td>原生窗口应用体验</td>
        </tr>
        <tr>
            <td>实时日志与进度条显示</td>
            <td>✅</td>
            <td>清晰了解运行状态</td>
        </tr>
        <tr>
            <td>简单的 AI 正文提取支持</td>
            <td>⚙️</td>
            <td>需自备 Gemini API Key</td>
        </tr>
        <tr>
            <td>自动内容去重与基本排版优化</td>
            <td>✅</td>
            <td>去除重复项，清理 HTML</td>
        </tr>
        <tr>
            <td>内置左右分栏式阅读界面</td>
            <td>✅</td>
            <td>类似 RSS 阅读器</td>
        </tr>
        <tr>
            <td>深浅主题可切换</td>
            <td>⚙️</td>
            <td>部分功能仍在完善中</td>
        </tr>
    </tbody>
</table>

<hr>

<h2>⚙️ 环境配置</h2>

<p>在虚拟环境中安装依赖：</p>

<pre><code>pip install pywebview requests beautifulsoup4 readability-lxml feedgen lxml tldextract fake-useragent</code></pre>

<hr>

<h2>🧠 AI 功能（可选）</h2>

<blockquote>
    <p>用于自动补全或增强文章正文提取效果。</p>
</blockquote>

<h3>配置方式：</h3>
<p>在 <code>rss_gui.py</code> 顶部填写：</p>

<pre><code class="language-python">GEMINI_API_KEY = "你的Gemini_API_Key"</code></pre>

<blockquote>
    <p>⚠️ <strong>原始 API Key 已移除</strong>。请自行申请并妥善保管。<br>
    若未填写，程序仍可正常运行（仅跳过 AI 增强提取）。</p>
</blockquote>

<hr>

<h2>🖥️ 启动方式</h2>

<pre><code>python "E:\RSSSiteCrawler\model(v2)\rss_gui.py"</code></pre>

<p>启动后将打开图形界面，操作区域说明如下：</p>

<table>
    <thead>
        <tr>
            <th>区域</th>
            <th>功能</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>输入栏</strong></td>
            <td>输入目标网站 URL（建议小型、结构清晰的网站）</td>
        </tr>
        <tr>
            <td><strong>日志区</strong></td>
            <td>实时显示抓取状态、错误信息</td>
        </tr>
        <tr>
            <td><strong>进度条</strong></td>
            <td>抓取进度可视化</td>
        </tr>
        <tr>
            <td><strong>左侧文章列表</strong></td>
            <td>自动生成的文章目录</td>
        </tr>
        <tr>
            <td><strong>右侧阅读区</strong></td>
            <td>显示提取后的正文内容</td>
        </tr>
        <tr>
            <td><strong>主题设置</strong></td>
            <td>支持字体、背景模式调整（部分功能开发中）</td>
        </tr>
    </tbody>
</table>

<hr>

<h2>📡 RSS 输出</h2>

<p>生成文件路径：</p>

<pre><code>E:\RSSSiteCrawler\model(v2)\site_full_rss.xml</code></pre>

<p>生成后可通过任意 RSS 阅读器（如 Feedly、Fluent Reader、NewsBlur）导入使用。</p>

<hr>

<h2>⚠️ 当前限制与状态</h2>

<table>
    <thead>
        <tr>
            <th>模块</th>
            <th>状态</th>
            <th>备注</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>GUI 启动</td>
            <td>✅ 可用</td>
            <td>正常运行</td>
        </tr>
        <tr>
            <td>网站爬取</td>
            <td>✅ 可用</td>
            <td>推荐小型网站</td>
        </tr>
        <tr>
            <td>AI 正文提取</td>
            <td>⚙️ 可用</td>
            <td>需有效 Gemini Key</td>
        </tr>
        <tr>
            <td>深浅主题切换</td>
            <td>⚙️ 部分实现</td>
            <td>按钮存在，样式待完善</td>
        </tr>
        <tr>
            <td>RSS 生成</td>
            <td>✅ 可用</td>
            <td>输出标准 XML</td>
        </tr>
        <tr>
            <td>打包为 EXE</td>
            <td>❌ 不可用</td>
            <td>PyWebView 打包兼容性问题</td>
        </tr>
    </tbody>
</table>

<hr>

<h2>🧱 关于 EXE 打包（暂不可用）</h2>

<blockquote>
    <p>⚠️ 由于 PyWebView 依赖 Chromium 嵌入式框架，<strong>当前无法成功打包为独立 EXE</strong>。</p>
</blockquote>

<p>尝试命令（会导致应用闪退）：</p>

<pre><code>pyinstaller --onefile --windowed --noconsole --name "全站RSS生成器" "E:\RSSSiteCrawler\model(v2)\rss_gui.py"</code></pre>

<p><strong>建议</strong>：<br>
请直接使用 Python 脚本运行，避免打包问题。</p>

<hr>

<h2>🧭 使用建议</h2>

<ul>
    <li>仅适用于 <strong>个人学习、小型网站或自建博客</strong> 的信息整理。</li>
    <li>不建议用于大规模网站或商业抓取。</li>
    <li>请尊重目标网站的 <code>robots.txt</code> 及版权要求。</li>
    <li>若目标网页结构复杂，可自行修改 <code>extract_article_content()</code> 函数逻辑。</li>
</ul>

<hr>

<h2>🌙 后续可拓展方向</h2>

<ul>
    <li>[ ] 完善深浅主题切换按钮</li>
    <li>[ ] AI 摘要与关键词提取</li>
    <li>[ ] 本地缓存 + 断点续抓</li>
    <li>[ ] 导出为 Markdown / PDF</li>
    <li>[ ] RSS 在线服务端发布（Flask/FastAPI）</li>
</ul>

<hr>

<h2>📄 版权与免责声明</h2>

<blockquote>
    <p>本项目仅用于 <strong>个人研究与技术学习</strong>。<br>
    作者不对任何因滥用或非法抓取造成的后果承担责任。<br>
    请确保您的使用行为符合目标网站的法律与道德规范。</p>
</blockquote>

<hr>

</body>
</html>
