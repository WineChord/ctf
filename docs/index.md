---
hide:
  - navigation
  - toc
---

<div class="scholar-home scholar-home--ctf">
<header class="scholar-masthead">
<div class="scholar-running-head">
<span>Wine &amp; Chord · Security Studies</span>
<span>Authorized research only</span>
</div>
<div class="scholar-hero-grid">
<div class="scholar-hero-copy">
<p class="scholar-overline">安全研究札记 · 第一卷</p>
<h1>把系统失效，写成可验证的知识</h1>
<p class="scholar-deck">在明确授权的赛事与靶场中，从原始证据建立分层模型，用最小实验检验假设，再把一次解题沉淀为能够独立复现的安全知识。</p>
<nav class="scholar-actions" aria-label="首页入口">
<a href="guide/roadmap/">进入学习路径 <span aria-hidden="true">→</span></a>
<a href="writeups/">查阅 Writeup <span aria-hidden="true">→</span></a>
</nav>
</div>
<aside class="scholar-abstract">
<p class="scholar-label">Abstract / 摘要</p>
<p>这里不罗列孤立命令，而是记录观察、推断、失败假设与验证条件；把漏洞放回协议、解析器、状态机和机器模型中，解释系统假设究竟在哪里断裂。</p>
<dl class="scholar-facts">
<div><dt>研究边界</dt><dd>Authorized Labs Only</dd></div>
<div><dt>分析主线</dt><dd>Observe → Verify</dd></div>
<div><dt>常用语言</dt><dd>Python · C · Shell</dd></div>
</dl>
</aside>
</div>
<div class="scholar-meta">
<span><b>范围</b> CTF 与授权安全研究</span>
<span><b>重点</b> 证据、原理与稳定复现</span>
<span><b>语言</b> 中文为主，术语双语</span>
<span><b>版本</b> 持续修订</span>
</div>
</header>
<section class="scholar-section">
<header class="scholar-section-head">
<span class="scholar-section-number">01</span>
<div>
<h2>研究目录</h2>
<p>先建立共同的系统基础与证据方法，再进入不同攻击面；主题之间通过数据流、边界与失效假设互相连接。</p>
</div>
</header>
<nav class="scholar-catalog" aria-label="CTF 知识目录">
<a class="scholar-entry" href="guide/methodology/">
<span class="scholar-entry-no">01</span>
<span class="scholar-entry-title"><strong>解题方法</strong><small>Methodology</small></span>
<span class="scholar-entry-desc">范围确认、证据采集、提出假设、最小实验、验证与复盘。</span>
<span class="scholar-entry-arrow" aria-hidden="true">↗</span>
</a>
<a class="scholar-entry" href="fundamentals/">
<span class="scholar-entry-no">02</span>
<span class="scholar-entry-title"><strong>共同基础</strong><small>Fundamentals</small></span>
<span class="scholar-entry-desc">Linux、网络、字节、编码、文件格式与脚本自动化。</span>
<span class="scholar-entry-arrow" aria-hidden="true">↗</span>
</a>
<a class="scholar-entry" href="web/">
<span class="scholar-entry-no">03</span>
<span class="scholar-entry-title"><strong>Web 安全</strong><small>Web Security</small></span>
<span class="scholar-entry-desc">HTTP、浏览器边界、服务端数据流、身份与业务逻辑。</span>
<span class="scholar-entry-arrow" aria-hidden="true">↗</span>
</a>
<a class="scholar-entry" href="pwn/">
<span class="scholar-entry-no">04</span>
<span class="scholar-entry-title"><strong>Pwn</strong><small>Binary Exploitation</small></span>
<span class="scholar-entry-desc">ELF、汇编、调用约定、内存错误、保护机制与调试。</span>
<span class="scholar-entry-arrow" aria-hidden="true">↗</span>
</a>
<a class="scholar-entry" href="reverse/">
<span class="scholar-entry-no">05</span>
<span class="scholar-entry-title"><strong>逆向工程</strong><small>Reverse Engineering</small></span>
<span class="scholar-entry-desc">静态分析、动态调试、数据流恢复与算法重建。</span>
<span class="scholar-entry-arrow" aria-hidden="true">↗</span>
</a>
<a class="scholar-entry" href="crypto/">
<span class="scholar-entry-no">06</span>
<span class="scholar-entry-title"><strong>密码学</strong><small>Cryptography</small></span>
<span class="scholar-entry-desc">整数与模运算、经典密码、现代原语及其实现失误。</span>
<span class="scholar-entry-arrow" aria-hidden="true">↗</span>
</a>
<a class="scholar-entry" href="forensics/">
<span class="scholar-entry-no">07</span>
<span class="scholar-entry-title"><strong>数字取证</strong><small>Forensics</small></span>
<span class="scholar-entry-desc">文件、磁盘、内存、流量、日志、隐写与时间线。</span>
<span class="scholar-entry-arrow" aria-hidden="true">↗</span>
</a>
<a class="scholar-entry" href="misc/">
<span class="scholar-entry-no">08</span>
<span class="scholar-entry-title"><strong>Misc</strong><small>Cross-disciplinary</small></span>
<span class="scholar-entry-desc">编程、Jail、OSINT、协议、自动化与跨领域题目。</span>
<span class="scholar-entry-arrow" aria-hidden="true">↗</span>
</a>
</nav>
</section>
<section class="scholar-section scholar-methods">
<div class="scholar-methods-copy">
<span class="scholar-section-number">02</span>
<h2>从证据到复现</h2>
<p>可靠分析不是猜中漏洞名称，而是让事实、推断与实验彼此对齐，并给出第三方能够重复的判定标准。</p>
<p class="scholar-reading-note"><span>研究边界</span>本站仅讨论 CTF、教学靶场、个人隔离实验与明确授权的防御研究。建议先读<a href="guide/lab-safety/">合法边界与实验安全</a>，再进入<a href="guide/methodology/">解题方法</a>。</p>
</div>
<ol class="scholar-method-list">
<li><span>01 · Scope</span><strong>确认范围</strong><p>先确定目标、数据、时间和允许动作；保存样本、哈希、版本与环境。</p></li>
<li><span>02 · Observe</span><strong>记录事实</strong><p>从可重复的输入输出出发，区分直接观察、推断、未知与失败路径。</p></li>
<li><span>03 · Hypothesize</span><strong>建立模型</strong><p>把现象放回协议层、解析层、数据流或机器状态，提出可证伪的解释。</p></li>
<li><span>04 · Reproduce</span><strong>最小验证</strong><p>每次只改变一个变量，交叉验证根因，并写出独立复现与防御含义。</p></li>
</ol>
</section>
<footer class="scholar-colophon">
<p>“证据先于解释，复现先于确信。”</p>
<span>Security Studies · Wine &amp; Chord</span>
</footer>
</div>
