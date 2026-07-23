---
hide:
  - navigation
  - toc
---

<div class="ctf-hero" markdown>
<div class="ctf-kicker">Observe · Hypothesize · Verify</div>
# 拆开每一层假设，理解系统如何失效

在明确授权的赛事与靶场环境中，从现象到证据、从原理到复现、从一次解题到可迁移知识。这里不只保存命令，更关心<strong>看见了什么、为什么成立、如何可靠验证</strong>。

[开始学习](guide/roadmap.md){ .md-button .md-button--primary }
[浏览 Writeup](writeups/index.md){ .md-button }
</div>

## 知识地图

<div class="ctf-grid" markdown>
<a class="ctf-card" href="guide/methodology/">
<strong>解题方法</strong>
<span>范围确认、证据采集、假设、最小实验、验证与复盘。</span>
</a>
<a class="ctf-card" href="fundamentals/">
<strong>共同基础</strong>
<span>Linux、网络、字节、编码、文件格式与脚本自动化。</span>
</a>
<a class="ctf-card" href="web/">
<strong>Web</strong>
<span>HTTP、浏览器边界、服务端数据流、身份与业务逻辑。</span>
</a>
<a class="ctf-card" href="pwn/">
<strong>Pwn</strong>
<span>ELF、汇编、调用约定、内存错误、保护机制与调试。</span>
</a>
<a class="ctf-card" href="reverse/">
<strong>逆向工程</strong>
<span>静态分析、动态调试、数据流恢复与算法重建。</span>
</a>
<a class="ctf-card" href="crypto/">
<strong>密码学</strong>
<span>整数、模运算、经典密码、现代原语与实现失误。</span>
</a>
<a class="ctf-card" href="forensics/">
<strong>数字取证</strong>
<span>文件、磁盘、内存、流量、日志、隐写与时间线。</span>
</a>
<a class="ctf-card" href="misc/">
<strong>Misc</strong>
<span>编程、Jail、OSINT、协议、自动化与跨领域题目。</span>
</a>
</div>

## 一次可靠分析留下什么

=== "证据"

    保存原始样本、哈希、环境、命令与输出。事实、推断和未验证猜想分别标记。

=== "模型"

    把现象放回协议层、解析层、数据流、状态机或机器模型中，找出被破坏的假设。

=== "实验"

    每次只改变一个变量，用最小输入验证一个假设；失败路径同样能缩小搜索空间。

=== "复现"

    写清依赖、版本、步骤与判定标准。别人能在同一授权环境中重现，结论才真正稳定。

!!! warning "授权边界先于技术"

    本站内容仅用于 CTF、教学靶场、个人隔离实验和明确授权的防御研究。不要把赛事或靶场中的技巧直接用于未授权系统；目标、数据、时间和允许动作都应在测试前确认。

## 解题闭环

```text
确认范围 → 保存原始证据 → 建立分层模型 → 提出假设
    ↑                                      ↓
整理复盘 ← 独立复现 ← 交叉验证 ← 最小化实验
```

推荐先读[解题方法](guide/methodology.md)和[合法边界与实验安全](guide/lab-safety.md)，再完成[字节、编码与端序](fundamentals/bytes-encoding.md)。共同基础会同时影响 Web、Pwn、逆向、密码和取证。

> 工具能放大判断，但不能替代判断。最有价值的记录，通常是把一个偶然成功的操作解释成可验证的系统行为。
