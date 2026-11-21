---
name: project-docs
description: Scaffold and maintain a project's documentation set — goal and scope, architecture with ADRs, milestone plan, phase records, test records, README, CHANGELOG, and project-level AGENTS.md constraints. Use when starting a project, opening or closing a milestone, preparing a release, running a retrospective, or when asked to organize, audit, or scaffold project documentation.
whenToUse: 新项目立项、里程碑开始或结束、发版、复盘，或被要求整理、补齐、审计项目文档
---

# 项目文档建设与维护

把「什么时候需要哪份文档」变成可执行的流程。默认输出中文，代码、命令、标识符、提交信息用英文。

## 何时用

- 新项目从零建立文档骨架
- 里程碑开始时写本期计划，结束时写阶段结论
- 发版前对齐 README、CHANGELOG、测试记录
- 文档审计：检查缺失文件、断链、过期命令、重复的 ADR 编号

## 何时不用

- 只是补一段 API 说明 — 直接改对应文档，不要跑流程
- 用户只想要一份空模板 — 直接从 `references/templates/` 复制给他，不写盘

## 三条硬规则

1. **只补缺，不重写。** 已存在的文件一律先读；已有段落只做校准，不整篇覆盖；结构性改动先给出 diff 摘要并等确认。
2. **写盘白名单。** 只允许写 `README.md`、`CHANGELOG.md`、`AGENTS.md`、`docs/**`。不碰源码、CI 配置、`.git`、依赖清单。
3. **信息不足就问，不编。** 目标、用户、完成标准探测不出来时，停在第 2 步用一次 `ask_user_question` 收集；不允许生成占位式假目标然后把流程走完。

## 阶段门与产出

| 触发 | 必产出 | 可延后 |
|---|---|---|
| 立项 | `README.md` 骨架、`docs/goal.md`、`docs/architecture.md` 初稿、`AGENTS.md` | `CHANGELOG`、ADR |
| 里程碑开始 | `docs/plan.md` 的本期目标与 DoD | — |
| 里程碑结束 | `docs/history/NN-<名字>.md`、`plan.md` 状态更新 | 独立测试记录 |
| 发版 | `CHANGELOG.md`、README 的安装与运行节 | — |
| 复盘 / 事故 | `docs/postmortems/YYYY-MM-DD-<标题>.md`，并提炼出一条规则 | — |

阶段门之外不主动生成文档。用户没有说要发版，就不要写 CHANGELOG。

## 执行顺序

1. **探测（只读）** — 见下节；先看清项目是什么，再决定写什么。
2. **盘点** — 列出「已有 / 缺失 / 过期」三列，不要边盘点边写。
3. **询问** — 只问三件事：一句话目标、谁用、本期做到哪算完成。
4. **生成** — 只写缺失项；从 `references/templates/` 复制，替换掉所有 `<!-- fill -->`。
5. **交叉校验** — README 的命令 = 清单文件里的脚本名；plan 的里程碑 = CHANGELOG 的版本号；`AGENTS.md` 的命令真实存在；`goal.md` 的非目标与 plan 的任务不冲突。
6. **自检** — 运行 `python scripts/check_docs.py -root <项目根>`；退出码 `1` 表示有 FAIL，先修；`2` 表示用法或配置错误（不是文档问题）。
7. **报告** — 新增、修改、跳过分别列清；跳过必须给理由。

## 探测清单（只读）

- 清单文件：`package.json`、`pyproject.toml`、`go.mod`、`Cargo.toml`、`*.csproj`
- 命令来源：清单里的 `scripts`、`Makefile`、`justfile`、CI 配置
- 已有文档：`README*`、`docs/**`、`CHANGELOG*`、`AGENTS.md`、`CLAUDE.md`
- 事实来源：所有命令从上述文件抄，不凭印象写；查不到就标「未验证」

## 每份文档的最低要求

| 文件 | 必须有 | 目标长度 |
|---|---|---|
| `README.md` | 一句话目标、状态、跑起来的命令、文档索引 | ≤ 40 行 |
| `docs/goal.md` | 问题、用户、目标、非目标、成功标准 | ≤ 1 页 |
| `docs/architecture.md` | 组件边界、数据流、外部依赖、ADR 索引、已知边界 | ≤ 2 页 |
| `docs/adr/NNN-*.md` | 背景、决策、备选、后果 | ≤ 1 页 |
| `docs/plan.md` | 本期目标、粗粒度任务、DoD、风险、验收方式 | ≤ 1 页 |
| `docs/history/NN-*.md` | 达成情况、未完成及原因、风险、下阶段 | ≤ 1 页 |
| `docs/test-records.md` | 验收结论、已知缺陷与复现、证据位置 | 追加式 |
| `AGENTS.md` | 命令、禁止项、环境事实、完成定义 | ≤ 100 行 |

## 反模式（禁止）

- 一次性生成全套文档；空表格、空章节、`TBD` 留在交付物里
- 独立 `FIXME.md` / `TODO.md` 当长期仓库（改用 issue，或代码内 `FIXME(owner,#id): 原因`）
- `plan.md` 细化到任务级；`README.md` 里塞目标、架构、计划
- 把命令手抄进 README 而不指向真实脚本名
- 用自己编的目标替代用户确认，或把「待定」当成已完成

## 校验

`scripts/check_docs.py` 检查必填文件、必填章节、相对链接、ADR 编号、残留占位符。只用 Python 3.8+ 标准库，Windows / macOS / Linux 是同一份脚本。

```text
python3 scripts/check_docs.py -root <项目根>   # macOS / Linux
python  scripts/check_docs.py -root <项目根>   # Windows
```

退出码约定：`0` 通过、`1` 有 FAIL、`2` 用法或配置错误（`-root` 不存在、`checks.json` 缺失或语法坏）。脚本不打印 traceback，错误一律一行 `error: ...`。文档按 UTF-8 → GB18030 依次尝试解码，UTF-8 BOM、CRLF、GBK 都能正确匹配章节。没有 Python 时不要硬跑，按 `references/checklist.md` 人工核对。

章节要求放 `references/checks.json`，要加检查项就改那个文件，不改脚本。

## 资源

- `references/templates/` — 9 份模板，按阶段门取用。模板一律用 `<名字>.template.md` 命名：`AGENTS.md` 在 Windows 上大小写不敏感，`agents.md` 会被当成真指令注入会话
- `references/checklist.md` — 交付前逐条勾
- `references/checks.json` — 校验脚本的章节要求，按项目调整
- `scripts/check_docs.py` — 必填文件 / 必填章节 / 相对链接 / ADR 编号 / 占位符
