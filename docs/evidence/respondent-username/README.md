# 非匿名答卷的用户名显示测试

本次修正在非匿名答卷中增加注册用户名展示，并检查历史匿名保护、跨版本统计和分页查询。

## 执行结果

|测试范围|结果|记录|
|---|---|---|
|新增测试首次执行|4项通过、7项准备错误，41.03秒；MongoDB未启动|[错误输出](initial-no-mongo.txt)|
|启动数据库后重跑新增测试|11项通过，7.02秒|[执行输出](targeted.txt)|
|完整回归|113项通过，37.82秒|[执行输出](full.txt)、[JUnit](full.xml)|

## 测试内容

新增11个实例包括3个响应字段测试、4个API匿名/实名组合、2个跨版本测试、1个批量查询测试和1个关联用户缺失测试。

主要验证内容如下：

- 非匿名记录返回respondentId和respondentUsername；匿名记录隐藏这两个字段。
- V1与V2使用各自提交时的匿名设置，版本切换后历史答卷的身份展示保持一致。
- 当前页的用户ID去重后一次查询，读取字段为_id和username；空页及匿名页无需查询用户。
- 关联账号缺失时，用户名返回null，页面回退显示原ID。
- 浏览器页面优先展示注册用户名，查看旧匿名版本时继续显示“匿名”。

完整回归包括72项单元、39项数据库/API及2项浏览器测试。批量查询通过真实MongoDB命令监听检查，用户查询与答卷聚合使用同一事务。

## 复现命令

在source目录执行：

```powershell
..\.venv\Scripts\python.exe -m pytest tests/unit/test_owner_submission.py tests/integration/test_respondent_usernames.py -q
$env:TEST_EVIDENCE_DIR='../docs/evidence/respondent-username'
..\.venv\Scripts\python.exe -m pytest -q --junitxml=../docs/evidence/respondent-username/full.xml
```

此次修正保留原respondentId，用户名在读取时从users补充。数据库结构与统计口径沿用原有设计。
