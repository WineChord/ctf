# 更新日志

## 2026-07-28

### 图表与证据

- 为[学习路线](guide/roadmap.md)、[解题方法](guide/methodology.md)、[实验安全](guide/lab-safety.md)、[工具链](guide/tooling.md)、[共同基础](fundamentals/index.md)及 [Web](web/index.md)、[Pwn](pwn/index.md)、[逆向](reverse/index.md)、[密码学](crypto/index.md)、[数字取证](forensics/index.md)、[Misc](misc/index.md) 加入与正文紧密对应的语义图。
- 在[端序专题](fundamentals/bytes-encoding.md#fig-big-endian)采用固定版本的 Public Domain 图示，在[取证专题](forensics/index.md#fig-nist-forensic-process)采用 NIST SP 800-86 的精确图幅，并提供就近来源、许可和变换说明。
- 为技术专题补充精炼的 `Reference`，优先连接规范、官方文档与原始指南。
- 建立图表清单和发布检查，校验来源版本、许可、哈希、尺寸、元数据、替代文本、页面位置及生成后的 HTML。

## 2026-07-24

### 渲染质量

- 统一公式分隔符并固定 MathJax 版本，避免合法 TeX 被当作普通文本。
- 发布前校对 Markdown 与公式源、生成的 HTML，以及桌面和移动视口中的真实浏览器渲染。

### 界面精简

- 恢复 MkDocs Material 的原生布局、配色与组件，只保留必要的字体设置。
- 全站正文优先使用苹方，[首页](index.md)改为短标题、直接入口与分类链接。

### 站点初始化

- 建立 CTF 与安全知识库及 GitHub Pages 自动发布流程。
- 完成[学习路线](guide/roadmap.md)、[证据驱动解题方法](guide/methodology.md)、[合法边界与实验安全](guide/lab-safety.md)和[工具工作台](guide/tooling.md)。
- 建立 [Web](web/index.md)、[Pwn](pwn/index.md)、[逆向](reverse/index.md)、[密码学](crypto/index.md)、[数字取证](forensics/index.md)和 [Misc](misc/index.md) 知识地图。
- 发布[字节、编码与端序](fundamentals/bytes-encoding.md)专题，覆盖文本/字节、Base64、端序、补码、XOR 与文件结构。
- 建立 [Writeup 索引](writeups/index.md)、[写作模板](writeups/template.md)、全文搜索、MathJax 和深浅色主题。
- 加入敏感信息模式检查、Python 示例语法检查和严格站点构建。

### 视觉系统

- [首页](index.md)改为学术编辑风格，以摘要、研究边界、目录式索引和验证方法替代展示型卡片。
- 统一纸张色背景、衬线标题、细分隔线与克制的深青强调色，并完善移动端和深色模式。
