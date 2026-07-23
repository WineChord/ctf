# Web 安全知识地图

Web 题的核心不是记住请求片段，而是追踪数据穿过浏览器、代理、Web 服务器、框架、业务逻辑和存储时，每一层如何解析和信任它。

## 请求生命周期

```text
用户操作
  ↓
浏览器：URL、DOM、Cookie、同源策略
  ↓
HTTP：方法、路径、头、正文、重定向
  ↓
代理 / CDN / Web Server
  ↓
框架：路由、参数解析、中间件、模板
  ↓
业务逻辑：身份、权限、状态机
  ↓
数据库 / 文件 / 内部服务 / 外部 API
```

题目往往发生在边界处：两个组件对路径、编码、长度、Host、参数或身份状态的理解不同。

## 必备基础

### HTTP

能独立解释：

- 请求行、状态码和响应头；
- GET、POST 等方法的语义与实际实现差异；
- Query、表单、JSON、Multipart 的解析；
- Cookie 属性与会话标识；
- 重定向、缓存和内容协商；
- HTTP/1.1 与 HTTP/2 的消息边界差异。

### 浏览器安全模型

重点理解：

- Origin 由 scheme、host、port 共同决定；
- 同源策略限制哪些读取，而不是禁止所有跨源发送；
- CORS 是服务器声明的跨源读取策略；
- Cookie、Local Storage、Session Storage 的作用域不同；
- CSP、Sandbox、Trusted Types 等防护分别约束什么。

### 服务端

至少熟悉一种完整后端栈：路由、模板、ORM、认证中间件、文件处理、缓存和错误处理。只看浏览器代码无法证明服务端真的执行了同样检查。

## 题型分层

| 层 | 典型问题 | 首要问题 |
| --- | --- | --- |
| 输入与解析 | 注入、路径、上传、反序列化 | 输入在哪一层被解释为结构或代码？ |
| 身份与会话 | 登录、Token、Cookie、找回流程 | 身份依据是什么，生命周期如何变化？ |
| 访问控制 | 水平/垂直越权、对象引用 | 服务端是否对每个对象重新授权？ |
| 业务逻辑 | 状态机、并发、金额/次数 | 哪个不变量只存在于前端或单请求内？ |
| 浏览器 | XSS、跨源、DOM 数据流 | 数据从 source 到 sink 经过哪些变换？ |
| 服务端边界 | SSRF、代理/后端差异 | 谁实际发起请求，各层如何解析目标？ |
| 缓存与协议 | Cache、Request Smuggling | 不同组件对请求边界是否一致？ |

这些名称用于组织知识，不应替代具体数据流分析。

## 授权环境中的分析流程

1. 保存最小正常请求和响应；
2. 标记所有可控输入及其编码层；
3. 画出身份、对象和状态变化；
4. 每次只修改一个字段；
5. 比较状态码、头、正文长度、时间和副作用；
6. 清理缓存和会话后重复；
7. 在规则允许的前提下自动化；
8. 从服务端安全边界解释结果。

!!! warning "响应差异不是漏洞证明"

    长度、时间或错误信息差异只是候选信号。缓存、网络、随机性、并发和负载均可造成差异，需要重复和对照实验。

## 访问控制优先于前端界面

隐藏按钮、禁用表单和前端路由都不是服务端授权。可靠的访问控制需要在服务端对：

- 当前主体；
- 请求动作；
- 目标对象；
- 当前状态；
- 所属租户或作用域；

进行一致检查。

练习：[PortSwigger Web Security Academy · Access control](https://portswigger.net/web-security/access-control)。

## 输入到危险操作的数据流

分析注入类问题时，沿 source → transform → sink：

```text
请求参数
  ↓ URL/JSON/模板等解码
规范化、拼接、类型转换
  ↓
SQL / Shell / 模板 / 路径 / HTML / 反序列化入口
```

关键是明确“数据在哪一步变成语法”。同一个转义函数无法适用于 SQL、HTML、JavaScript、Shell 和路径等不同语法上下文。

练习：

- [PortSwigger Web Security Academy · SQL injection](https://portswigger.net/web-security/sql-injection)
- [PortSwigger Web Security Academy · Cross-site scripting](https://portswigger.net/web-security/cross-site-scripting)
- [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)

## 身份与 Token

看到 Token 先分层：

1. 编码格式；
2. 完整性机制；
3. 密钥或公钥选择；
4. Claims 语义；
5. 过期、撤销和轮换；
6. 服务端最终授权。

能解码 Token 不代表能伪造；签名有效也不代表 Claims 符合当前业务权限。

## 文件与路径

上传和下载题要分别追踪：

- 原始文件名与服务端生成名；
- MIME、扩展名、魔数和实际解析器；
- 临时目录与最终目录；
- 路径规范化、符号链接和权限；
- 上传后由谁、以什么方式再次处理；
- 响应头如何影响浏览器解释。

## 防御视角

一篇完整 Web 复盘还应回答：

- 应在哪一层验证和规范化；
- 使用参数化查询、上下文编码还是隔离；
- 访问控制应该绑定哪些对象和状态；
- 日志如何保留足够检测信号而不泄露秘密；
- 单元测试、集成测试和安全测试如何覆盖变种。

## 推荐顺序

1. HTTP 消息与浏览器开发者工具；
2. Cookie、Session、Origin、CORS；
3. 服务端路由、模板和数据库；
4. 输入解析与注入；
5. 身份、访问控制和业务逻辑；
6. 文件、SSRF、缓存和协议差异；
7. 防御设计与日志检测。
