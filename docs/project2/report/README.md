# 第二阶段排版报告

- [main.tex](main.tex)：与用户工作区 `report1/1.2.tex` 同步的完整独立源文件。
- [1.2.pdf](1.2.pdf)：7页，XeLaTeX编译，并逐页渲染检查。

沿第一阶段双栏、Times衬线字体、Fandol中文字体和浅色关系图。等宽字体优先Latin Modern Mono，缺失时回退Consolas。默认使用XeLaTeX编译两次，无外部图片依赖；数据库、架构、版本与统计流程图为TeX/TikZ原生对象。

报告图为系统结构图，真实运行截图另见 [full-browser](../evidence/full-browser/)，没有把结构示意图冒充浏览器证据。编译日志见 [report-compile.log](../evidence/report-compile.log)。本轮没有改写第一阶段1.1.tex或原报告PDF。

2026-10-27修订：同步原子保存、activeOnly分页、surveyCount含义和167项回归结果，仍为7页；本轮编译日志独立保存于 [修复编译记录](../evidence/fixes-2026-10-27/report-compile.log)，上方首轮编译日志历史保留。新增浏览器冲突证据见 [fix-atomic-conflict.png](../evidence/fixes-2026-10-27/full-browser/fix-atomic-conflict.png)。
