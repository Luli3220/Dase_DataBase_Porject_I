# 目录整理后回归

本目录独立保存本次目录调整后的测试结果和浏览器截图，原先验收证据保持原位。

工作目录为source，解释器为仓库根目录.venv。执行命令：

```powershell
$env:TEST_EVIDENCE_DIR='../docs/evidence/restructure'
..\.venv\Scripts\python.exe -m pytest -q --junitxml=../docs/evidence/restructure/pytest.xml
```

实际执行：**102 passed / 0 failed / 0 skipped，31.82秒**，见 [pytest输出](pytest.txt) 与 [JUnit](pytest.xml)。本轮测试包括真实MongoDB/API并发和Chromium桌面/手机流程，截图及临时服务日志保存在本目录。

补充验证：[原始文件/业务文件与链接检查](layout-checks.json)确认7份原始材料字节不变、24个业务文件未改、21份Markdown无缺失本地链接；[脚本检查](script-checks.json)确认setup从新入口执行、调用者目录和已有.env不变，Mongo启动/初始化成功。pip check、JS/PowerShell语法及Compose配置解析也通过。

在新source目录启动8000服务后，[真实HTTP演示](http.json)的22项请求检查再次PASS；health、login、JS/CSS和OpenAPI均返回200。

当前运行手册见 [source/README](../../../source/README.md)，完整历史报告见 [test-report](../../test-report.md)。
