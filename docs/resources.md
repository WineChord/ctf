# 学习与比赛资源

资源按“练习环境—权威参考—工具文档”组织。平台和工具会更新，使用前检查当前规则、支持版本与许可。

## CTF 与靶场

- [picoCTF](https://picoctf.org/)：适合建立基础分类与解题闭环。
- [OverTheWire Wargames](https://overthewire.org/wargames/)：Linux、网络和安全基础。
- [pwn.college](https://pwn.college/)：系统化的计算机安全课程和隔离挑战。
- [PortSwigger Web Security Academy](https://portswigger.net/web-security)：Web 安全专题与实验。
- [CryptoHack](https://cryptohack.org/)：交互式密码学挑战。
- [CTFtime](https://ctftime.org/)：赛事日历、队伍与公开 Writeup 索引。

比赛前阅读平台规则；题目实例的授权不自动扩展到平台其他资产。

## 安全知识参考

- [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)：Web 测试方法。
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)：面向防御实现的专题清单。
- [MITRE CWE](https://cwe.mitre.org/)：软件弱点分类。
- [RFC Editor](https://www.rfc-editor.org/)：互联网协议原始规范。
- [Linux man-pages](https://man7.org/linux/man-pages/)：Linux 系统调用和接口。
- [Python 标准库](https://docs.python.org/3/library/)：字节、网络、压缩、哈希等模块。

## 工具文档

- [Wireshark User’s Guide](https://www.wireshark.org/docs/wsug_html_chunked/)：抓包与协议分析。
- [Ghidra](https://ghidra-sre.org/)：静态分析和反编译。
- [GDB Documentation](https://sourceware.org/gdb/documentation/)：调试器文档。
- [pwndbg](https://pwndbg.re/)：GDB/LLDB 二进制分析扩展。
- [pwntools](https://docs.pwntools.com/)：CTF 交互与二进制脚本。
- [Volatility 3 Documentation](https://volatility3.readthedocs.io/)：内存取证。
- [SageMath Documentation](https://doc.sagemath.org/)：数学与密码分析计算。
- [CyberChef](https://gchq.github.io/CyberChef/)：浏览器内数据转换。

## 如何使用公开 Writeup

1. 先独立完成低成本观察和至少一个假设；
2. 只看提示或关键观察，继续自己验证；
3. 阅读完整 Writeup 时核对环境、证据和边界；
4. 关闭文章，从原始附件重新复现；
5. 改变输入、版本或保护机制检查迁移；
6. 把新知识连接到专题，不只收藏链接。

## 如何评估资料

优先级：

1. 协议、语言和工具的官方文档；
2. 赛事官方题解和作者说明；
3. 能提供环境、证据、脚本和验证的高质量 Writeup；
4. 只给命令或结果的速记内容。

内容发布时间很重要：浏览器、编译器、内核、库和防护机制变化会让旧结论失效。

## 比赛复盘清单

- 哪些题卡在分类，哪些卡在原理，哪些卡在实现；
- 哪个假设消耗时间最多，为什么没有更早证伪；
- 工具输出是否被误当成事实；
- 环境、版本、网络或授权规则是否影响路径；
- 哪个脚本可以抽象为通用模块；
- 需要补充哪个基础专题；
- 哪些材料可以公开，哪些必须继续保密。
