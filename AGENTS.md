# AGENTS.md — buildhelper

## 命令

```powershell
# 校验文档骨架。退出码 0 通过 / 1 有 FAIL / 2 用法或配置错误
python scripts\check_docs.py -root .
# 反例：空目录（无 README/goal/architecture/AGENTS）应 exit 1；坏 checks.json 应 exit 2
```

## 禁止事项

- 不要给校验脚本加第三方依赖，也不要让它打印 traceback：异常一律收敛成一行 `error: ...` 并 exit 2；规则数据放 `references/checks.json`
- 不要把模板命名为 `AGENTS.md` / `CLAUDE.md`。Windows 大小写不敏感，`agents.md` 会被当成真指令注入会话
- 不要在 `SKILL.md` 里写具体项目的路径或命令，只写探测顺序
- 不要一次生成全套文档，不要用 `<!-- fill -->` 占位充当完成
- 不要为某次事故单独加一条规则而不注明来源（issue 号或日期）
- 不要把 skill 物料放回 `skill/` 之类的子目录：DSH 只发现一层 `<根>/<名字>/SKILL.md`，多一层就失去「克隆即用」（ADR-004）
- 不要提交 `docs/plan.md`、`docs/adr/`、`docs/history/`、`docs/test-records.md`：这些是本地过程记录，`.gitignore` 已挡（2026-11-21 用户要求，不公开构建过程）

## 环境事实

- Windows 11 + PowerShell 5.1；有 `python`（3.15）和 `git`，没有 `pnpm`，没有 `rg`
- 校验脚本是 Python：`python scripts\check_docs.py -root .`；`.ps1` 已删除，不要再写 `powershell -File`
- `Get-Content` 默认按 ANSI 解码，读 UTF-8 中文会乱码（行数也会数错）；读文件必须带 `-Encoding UTF8`
- 沙箱内 `git clone <本地路径>` 会失败（msys sh 起不来，`0xC0000022`）；要检查提交内容就用 `git archive` 导出，真实 clone 留给沙箱外的终端（2026-11-21 实测）
- 项目根：`C:\Users\ottol\myproject\buildhelper`（git 仓库）
- 仓库根即 skill 根（ADR-004）：`SKILL.md`、`references/`、`scripts/` 直接在根；装到 `.dsh/skills/` 或跨工具的 `.agents/skills/`，本机尚未安装到任何 agent
- 文档写入白名单：`README.md`、`CHANGELOG.md`、`AGENTS.md`、`SKILL.md`、`docs/**`、`references/**`、`scripts/**`

## 完成定义

- 改 `SKILL.md`、模板、`checks.json` 或 `check_docs.py` 后，必须跑一次校验并贴实际输出：正常 `0`、空目录 `1`、坏配置 `2`
- 新增检查项时同时给正例（应 0 FAIL）和反例（应非 0）
- 文档与实现不一致时先改文档

## 文档指针

- 目标与范围：`docs/goal.md`
- 架构：`docs/architecture.md`
- 计划与 DoD：`docs/plan.md`（仅本地，不提交）
- 决策：`docs/adr/`（仅本地，不提交）
