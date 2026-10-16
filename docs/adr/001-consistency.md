# ADR 001：MongoDB 副本集、事务与发布恢复

状态：采纳。原规格允许 standalone 的冻结后 CAS 发布，也允许事务。本实现选择单节点 replica set（本机开发和 Compose 一致），使用 MongoDB snapshot/majority 事务创建问卷、派生草稿、写答卷与锁定策略。原因：单靠先查再写无法保证“首个提交之后策略不可改”，也无法阻止关闭/切版与提交竞态。业务事务均写 surveys.writeRevision，与关闭/发布元数据更新形成写冲突并重试。hasSubmissions 在成功提交的同一事务置 true；失败事务不锁策略。

发布有意采用两步：先按 revision CAS 冻结版本，再原子切 surveys 指针。进程在中间终止时，draftVersion 仍指向 sealed 版本；原公开指针不变。相同 revision 再次 publish 完成恢复；不修改任何 sealed 内容。编辑返回 DRAFT_CONFLICT。测试用 after_seal 注入中断。关闭后不重新开放，防止恢复发布绕过关闭状态。

不选择 standalone 模拟事务或进程内锁：前者不足以维护跨集合写入约束，后者在多个 worker/重启时不成立。代价：启动必须配置 replica set；同问卷写入会串行竞争 survey 文档，课程规模可接受；大规模应拆分线性化状态并评估热点。第二阶段沿用数据模型和服务接口，不推倒重做。

题目/选项稳定 ID 由编辑器创建，改语义时应新增题目/选项，不复用旧 ID。技术上无法自动判断自然语言语义是否根本变化，因此文档提示并保留不可变历史版本。
