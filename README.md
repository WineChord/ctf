# CTF

一份持续生长的 CTF 与安全知识库：在合法授权的赛事与靶场环境中，从现象、证据和原理出发，沉淀可复现、可迁移的解题能力。

**在线阅读：[www.wineandchord.com/ctf](https://www.wineandchord.com/ctf/)**

[![Deploy site](https://github.com/WineChord/ctf/actions/workflows/pages.yml/badge.svg)](https://github.com/WineChord/ctf/actions/workflows/pages.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-0d7680.svg)](LICENSE)

## 内容范围

- Web、Pwn、逆向、密码学、数字取证与 Misc。
- Linux、网络、字节表示、调试与自动化等共同基础。
- 从观察、假设、实验到验证的解题方法。
- 可复现的 Writeup、失败路径、变种与知识关联。

所有内容仅面向明确授权的 CTF、靶场、教学实验和防御研究场景。

## 本地预览

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/check_content.py
python scripts/check_figures.py
python scripts/check_python.py
python scripts/check_rendering.py
mkdocs build --strict
python scripts/check_figures.py --site-dir site
python scripts/check_rendering.py --site-dir site --browser
mkdocs serve
```

浏览器打开 `http://127.0.0.1:8000/ctf/`。

## 目录

- `docs/`：网站正文
- `mkdocs.yml`：站点配置与导航
- `scripts/check_content.py`：内容与敏感信息模式检查
- `scripts/check_figures.py`：图表来源、许可、资产、位置与渲染检查
- `scripts/check_python.py`：逐个检查完整 Python 代码块
- `scripts/check_rendering.py`：校对 Markdown、公式、构建产物与浏览器渲染
- `FIGURE_NOTICE.md`：第三方图表署名与复用边界
- `.github/workflows/pages.yml`：GitHub Pages 自动发布

## License

仓库原创代码、正文与原创图示采用 [MIT License](LICENSE)。`docs/assets/figures/external/` 中的第三方图表保留各自的复用条款、署名与来源，详见 [FIGURE_NOTICE.md](FIGURE_NOTICE.md)。
