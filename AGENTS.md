# AGENTS.md — buildhelper

本文件供维护 buildhelper 仓库的 agent 使用。调用此 skill 时读取 `SKILL.md`，下游项目的指令范本在 `references/templates/AGENTS.template.md`。

## 命令

```powershell
# 校验文档骨架。退出码 0 通过 / 1 有 FAIL / 2 用法或配置错误
python scripts\check_docs.py -root . -stage founding
# 阶段累计：milestone 加 docs/plan.md，release 加 CHANGELOG.md
# 发布物 / 提交内容 / 存量项目长度放宽
python scripts\check_docs.py -root . -stage release --published
python scripts\check_docs.py -root . --staged
python scripts\check_docs.py -root . -config references\checks-stock.json
# 只读盘点：每份文档的角色与 keep/merge/archive 建议，不改文件
python scripts\check_docs.py -root . -stage release --inventory
# 反例：空目录 founding 应 exit 1；release 缺 CHANGELOG 应 exit 1；未知阶段应 exit 2；--published 与 --staged 同给应 exit 2
# 运行校验器单元测试（需要 Python 和 Git）
python scripts\test_check_docs.py
```

## 禁止事项

- 不要把规则写回脚本或 `SKILL.md`：阶段、章节、长度只在 `references/checks.json`（ADR-006）
- 不要给校验脚本加第三方依赖，也不要让它打印 traceback：异常一律收敛成一行 `error: ...` 并 exit 2
- 不要把模板命名为 `AGENTS.md` / `CLAUDE.md`。Windows 大小写不敏感，`agents.md` 会被当成真指令注入会话
- 不要在 `SKILL.md` 里写具体项目的路径或命令，只写探测顺序
- 不要一次生成全套文档，不要用 `<!-- fill -->` 占位充当完成
- 不要为某次事故单独加一条规则而不注明来源（issue 号或日期）
- 不要把 skill 物料放回 `skill/` 之类的子目录：DSH 只发现一层 `<根>/<名字>/SKILL.md`，多一层就失去「克隆即用」（ADR-004）
- 不要提交 `docs/` 下任何文件：整个文档集都是本地过程记录，`.gitignore` 已挡（ADR-007）
- 不要让脚本自动移动或删除文档：`--inventory` 只出建议，收敛动作必须由用户确认（ADR-008）

## 仓库结构与运行要求

- 仓库根即 skill 根（ADR-004）。入口为 `SKILL.md`，模板和规则在 `references/`，校验器和测试在 `scripts/`。
- 校验器使用 Python 3.8+ 标准库。索引模式需要 Git。PowerShell 读取中文文档时显式指定 UTF-8。
- 文档写入白名单：`README.md`、`CHANGELOG.md`、`AGENTS.md`、`SKILL.md`、`docs/**`、`references/**`、`scripts/**`。
- 提交前逐项检查 `git diff --cached`。文档示例使用仓库相对路径或占位符。机器标识、个人目录、工具安装状态和原始日志留在本地（2026-11-26 文档审查）。

## 完成定义

- 改 `SKILL.md`、模板、`checks.json` 或 `check_docs.py` 后，必须跑三档 `-stage` 并贴实际输出：正常 `0`、空目录 `1`、坏配置或未知阶段 `2`
- 改校验器后还要跑 `--published`、`--staged`、`--strict`、`--inventory` 与 `-config references\checks-stock.json`，并核对单元测试结果。受限环境的已知问题和替代验证见本地 `docs/test-records.md`
- 新增检查项时同时给正例（应 0 FAIL）和反例（应非 0）
- 文档与实现不一致时先改文档

## 文档指针

- 目标与范围：`docs/goal.md`（仅本地）
- 架构：`docs/architecture.md`（仅本地）
- 计划与 DoD：`docs/plan.md`（仅本地）
- 决策：`docs/adr/`（仅本地）
