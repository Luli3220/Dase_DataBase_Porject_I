# 实际测试报告

首轮执行日期：2026-10-16，Asia/Shanghai；首轮环境记录时间11:20:13+08:00，见[evidence/environment.json](evidence/environment.json)，该时间点尚未初始化Git。当前最近一次完整功能验收是用户名修正后的113项通过（37.82秒），见文末和[证据总索引](evidence/README.md)，不要把早期文件名final误当作最新版本。2026-10-18只审核PDF/源码/原记录并收集当前113项测试，未重跑MongoDB/API/浏览器测试。

## 环境

Windows（platform报告Windows-10-10.0.26200-SP0）；Python3.11.5；MongoDB8.3.11（本机27018、rs0单节点）；FastAPI0.115.7；PyMongo4.19.0；Pydantic2.12.5；pytest8.4.2；Playwright1.64.0；实际使用已缓存Chromium chrome.exe。精确依赖见requirements-lock.txt，最终venv已禁用system-site-packages。

## 分阶段执行

|阶段/命令（均使用.venv/Scripts/python.exe）|实际结果|证据|
|---|---|---|
|A：-m pytest tests/unit tests/integration/test_core.py -q --junitxml=docs/evidence/phase-a.xml|72 passed，0失败/跳过，2.75秒|phase-a.txt/xml|
|B：-m pytest tests/integration/test_api.py -q --junitxml=docs/evidence/phase-b-api.xml|17 passed，0失败/跳过，14.90秒|phase-b-api.txt/xml|
|B：-m scripts.http_demo（8000真实HTTP）|22个请求检查PASS，含预期403/409|phase-b-http.json|
|C首次浏览器：-m pytest tests/web -q --junitxml=docs/evidence/browser.xml|2 passed，10.13秒|browser.txt/xml、实际PNG|
|C边界回归：-m pytest tests/unit tests/integration -q --junitxml=docs/evidence/regression.xml|98 passed，16.62秒|regression.txt/xml|
|最终隔离环境：-m pytest -q --junitxml=docs/evidence/final.xml|**102 passed，0 failed，0 skipped，31.36秒**|final.txt/xml、case-results.md|
|-m pip check|No broken requirements found|在隔离依赖环境实际执行|
|node --check app/static/app.js|exit0，无语法错误|实际执行，后续浏览器也加载成功|
|最终服务重启后 -m scripts.http_demo|22个HTTP检查再次PASS，/health返回200 ok|final-http.json|
|Docker Compose配置解析 / Python编译 / 文档本地链接|全部exit0/无缺失链接，未运行Docker容器|static-checks.json|

PowerShell安装/启动/测试脚本也实际通过System.Management.Automation.Language.Parser语法解析。文档与源码的交付包由scripts/package_delivery.py生成，压缩包逐文件SHA256与manifest核对，排除.env、.venv、.local及缓存。

首轮最终102项组成：69纯规则单元实例、31真实Mongo/API/并发实例、2真实浏览器实例。早期阶段数量少，是阶段后新增了极大整数、会话重放、分块请求等覆盖，不是删除旧测试。每例JUnit详见[evidence/case-results.md](evidence/case-results.md)。

## 实际问题与修复

1. conda启动器报“The system cannot execute the specified program”，直接检查db解释器为3.10.21且缺FastAPI。采用已有3.11.5建立项目venv，最终安装精确依赖并关闭系统包继承，没有修改原环境。
2. 沙箱内pip出现ProxyError/WinError10013；通过批准的网络执行安装到本项目venv。初期继承base的无关pyppeteer/pyee冲突提示，在最终完全隔离环境中消除，pip check通过。
3. Docker CLI29.0.1存在，但daemon管道不存在。使用本机mongod，不以mock数据库替代；Docker配置仅静态验证，不声称容器启动通过。
4. 自动化宿主启动的后台Mongo进程未持续可连接；初始化实际报告MongoDB did not start/10061。改用常驻独立进程，初始化rs0后所有真实数据库测试通过。README提供常驻终端命令。
5. 严格Pydantic日期字段可能拒绝正常ISO字符串。仅对AwareDatetime输入关闭strict转换；含时区正常接受，无时区仍422，API测试验证。
6. 静态审查发现极大整数调用math.isfinite可能溢出。先判断安全范围，再判断有限性；增加10**1000边界回归。该问题是审查发现，不虚称曾有失败测试。
7. 视觉检查发现答卷明细显示选项内部ID。前端依据被选历史版本映射标签，仍保留API的稳定ID，重新执行浏览器回归并更新截图。
8. 加强匿名/并发：明确DTO、历史匿名快照；统计改只读snapshot，避免同响应内计数漂移；新增复制Cookie退出失效与普通/分块2MiB限制验证。全部回归通过。

没有隐瞒失败或把预期当实际。本轮功能测试执行后均通过；前述安装/服务启动失败没有计为测试PASS。发布中断故障是测试主动注入，预期恢复通过。

## 浏览器证据与限制

editor.png：四类题及规则编辑；published.png：真实发布结果与链接；statistics.png：版本、口径、题目、有效/原始统计及匿名答卷；mobile.png：390px表单；login.png：真实登录页。截图包含测试随机账号，非真实用户账号。已经人工式视觉检查（由AI查看实际图像），不声称人类审查。

未验证：Docker镜像构建/容器运行、MongoDB7/8.0相容性运行（本机实测8.3.11）、公网HTTPS部署、多节点故障转移、负载容量、其他浏览器引擎。单节点副本集用于课程环境，不代表高可用生产系统。课程要求的六项、版本/匿名/重复/并发主要边界均有真实证据。

## 后续目录整理回归

用户要求将Prompt、源码等分目录，并做好索引。当前实现、依赖、Docker和测试均在source；原始PDF和规格分别在requirements/prompts；设计/证据保留docs。前述阶段命令与路径是初次开发时的真实历史，不改写。当前命令见[source运行手册](../source/README.md)。

迁移后在source执行：`../.venv/Scripts/python.exe -m pytest -q --junitxml=../docs/evidence/restructure/pytest.xml`，并设置`TEST_EVIDENCE_DIR=../docs/evidence/restructure`。实际 **102 passed / 0 failed / 0 skipped，31.82秒**，证据独立保存在[restructure/](evidence/restructure/README.md)，没有用旧测试结果替代本轮执行。

额外实际检查：原始PDF/Prompt共7份字节不变；24个app业务文件与首次提交字节相同；21份Markdown本地链接有效；pip check通过；JavaScript和PowerShell语法、source中的Compose配置解析通过。实际运行根入口setup、start-local和初始化：调用者目录恢复、既有source/.env未覆盖、MongoDB数据未删除。迁移后重启8000服务，复核网页、静态文件和真实HTTP演示。Docker仍仅配置解析，不声称容器运行。

## 后续最小修正：非匿名答卷的注册用户名

修改限定为submissions的DTO/当前页批量用户查询、网页身份显示、相关测试和说明。保留respondentId，新增respondentUsername；匿名仍由anonymousAtSubmission控制，旧匿名不因新实名版本泄露。用户名只读取不冗余存储，未改Schema、规则引擎、聚合筛选或统计口径。

新增11项：3个DTO白名单、4个API组合、2个双向跨版本、1个真实Mongo命令监听、1个缺失用户。现有浏览器测试增加实名显示用户名且不显示ID、历史匿名二者皆无的断言。批量测试证明当前页去重_id的一次users.find只取_id/username，与列表共用事务；匿名页/空页零查询。

首次运行时Mongo未启动，实际4 passed / 7 setup errors（41.03秒，连接10061），保留错误证据。复用原目录启动Mongo后，新增测试11 passed（7.02秒）。随后从source执行`../.venv/Scripts/python.exe -m pytest -q --junitxml=../docs/evidence/respondent-username/full.xml`，实际 **113 passed / 0 failed / 0 errors / 0 skipped，37.82秒**；包含原有测试、全部新增测试及真实Chromium桌面/手机流程。node --check及pip check也通过。

完整命令、输出、JUnit及环境错误记录见[本轮证据](evidence/respondent-username/README.md)。无破坏性兼容变更：原实名respondentId保留，新增username为查询时当前用户名；缺失用户返回null并回退ID。匿名输出不增加任何身份字段，无数据迁移。未将这些结果扩展宣称Docker/公网/容量验证。
