# 非匿名填写者用户名修正：实际验证

工作目录source，Python解释器../.venv/Scripts/python.exe。保留原始102项验收记录，本轮证据单独存放于此。

|执行|实际结果|证据|
|---|---|---|
|首次新增测试，Mongo未运行|4 passed / 7 setup errors，41.03秒；WinError10061|[首次输出](initial-no-mongo.txt)、[首次JUnit](initial-no-mongo.xml)|
|复用原Mongo目录启动rs0后重跑新增测试|11 passed / 0 failed / 0 errors / 0 skipped，7.02秒|[输出](targeted.txt)、[JUnit](targeted.xml)|
|全部现有及新增测试|113 passed / 0 failed / 0 errors / 0 skipped，37.82秒|[输出](full.txt)、[JUnit](full.xml)|
|JavaScript语法检查|node --check app/static/app.js，exit0|本轮实际执行|
|依赖检查|No broken requirements found|本轮实际执行|

命令：

```powershell
..\.venv\Scripts\python.exe -m pytest tests/unit/test_owner_submission.py tests/integration/test_respondent_usernames.py -q --junitxml=../docs/evidence/respondent-username/targeted.xml
$env:TEST_EVIDENCE_DIR='../docs/evidence/respondent-username'
..\.venv\Scripts\python.exe -m pytest -q --junitxml=../docs/evidence/respondent-username/full.xml
```

11个新增实例包括3个DTO身份白名单、4个API匿名/实名与口径组合、2个双向跨版本隐私、1个真实Mongo批量命令监听、1个用户缺失回退。完整113项包括72单元、39数据库/API/并发、2浏览器实例。现有浏览器流程新增断言：V2实名答卷显示注册用户名而非ID；V1历史匿名答卷既无用户名也无ID。

命令监听验证分页3份答卷只调用一次users.find，$in仅含当前页非匿名去重用户ID，projection仅_id/username，使用与答卷聚合同一事务；空页和匿名页0次用户名查询。首次数据库不可用属于真实环境错误，未删去或伪装成通过；启动Mongo后没有修改功能代码即通过重跑。

兼容性：非匿名增加可空respondentUsername，原respondentId保留；匿名仍省略二者。用户名为读取时users.username，账号缺失时null，前端回退原ID。无集合、Schema、索引、规则或统计口径变更，无数据迁移。
