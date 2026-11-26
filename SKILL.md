---
name: project-docs
description: Scaffold and maintain a project's documentation set — goal and scope, architecture with ADRs, milestone plan, phase records, test records, README, CHANGELOG, and project-level AGENTS.md constraints. Use when starting a project, opening or closing a milestone, preparing a release, running a retrospective, or when asked to organize, audit, or scaffold project documentation.
whenToUse: 新项目立项、里程碑开始或结束、发版、复盘，或被要求整理、补齐、审计项目文档
---

# 项目文档建设与维护

阅读本 skill 的 agent 协助用户约定项目文档和工作方式。默认输出中文，代码、命令、标识符、提交信息用英文。

先确定两个目录。**Skill 根目录**是本文件所在的目录，根 `README.md` 介绍 buildhelper，根 `AGENTS.md` 供维护 buildhelper 的 agent 使用。**目标项目根目录**由本次任务确定，即使 skill 安装在该项目的子目录中，项目文档也写到目标项目。

| 从 skill 读取 | 在目标项目中编写 |
|---|---|
| `references/templates/README.md` | 根 `README.md`，给项目使用者阅读 |
| `references/templates/AGENTS.template.md` | 根 `AGENTS.md`，给接手项目的 agent 阅读，默认入库，由用户按项目调整 |
| `references/templates/` 中的目标、计划、架构等模板 | 按阶段写入目标项目 `docs/`，只发布已确认且可共享的内容 |

buildhelper 自己的 `docs/` 是本地维护记录。使用者从安装包内的 `SKILL.md`、`references/` 和 `scripts/` 即可开展工作。

## 何时用

- 新项目从零建立文档骨架
- 里程碑开始时写本期计划，结束时写阶段结论
- 发版前对齐 README、CHANGELOG、测试记录
- 文档审计：检查缺失文件、断链、过期命令、重复的 ADR 编号、同一件事的多份副本
- 文档越积越多，需要收敛到唯一归属

## 何时不用

- 只是补一段 API 说明 — 直接改对应文档，不要跑流程
- 用户只想要一份空模板 — 直接从 `references/templates/` 复制给他，不写盘

## 三条硬规则

1. **只补缺，不重写。** 已存在的文件一律先读；已有段落只做校准。项目约定与模板不同时，先指出具体差异、对实际工作的影响，让用户取舍，保留用户已有的修改；结构性改动先给出 diff 摘要并等确认。唯一例外是用户明确要求的「存量整理」（见下节）。
2. **写盘白名单。** 只允许写 `README.md`、`CHANGELOG.md`、`AGENTS.md`、`docs/**`。不碰源码、CI 配置、`.git`、依赖清单。
3. **信息不足就问，不编。** 目标、用户、完成标准探测不出来时，从尚不清楚且会影响当前工作的事项中选一个询问用户；不允许生成占位式假目标然后把流程走完。

## 阶段门与产出

| 触发 | 必产出 | 可延后 |
|---|---|---|
| 立项 | 项目 `README.md`、`AGENTS.md`、`docs/goal.md`。在目标文档中记下最终使用效果和粗略阶段路线 | 架构文档、ADR、详细排期 |
| 首次确定关键设计，或接入已有项目时查明模块边界 | 在 `docs/architecture.md` 记下已确认的边界、依据和选择理由。旧决定的原因无法查证时写「原因未确认」 | 需要单独追溯的取舍再写 ADR |
| 里程碑开始 | `docs/plan.md` 的本期目标与 DoD | — |
| 里程碑结束 | `docs/history/NN-<名字>.md`、`plan.md` 状态更新 | 独立测试记录 |
| 发版 | `CHANGELOG.md`、README 的安装与运行节 | — |
| 复盘 / 事故 | `docs/postmortems/YYYY-MM-DD-<标题>.md`，并提炼出一条规则 | — |

阶段门之外不主动生成文档。用户没有说要发版，就不要写 CHANGELOG。

## 三种调用场景

同一个 skill，三套起手式。先判断处在哪一步，再决定要不要新建文件。

| 场景 | 起手动作 | 产物 |
|---|---|---|
| 开工（bootstrap） | 探测项目类型 + 盘点已有文档 | 缺失的核心文档骨架 |
| 中期（maintain） | 读 `docs/plan.md` 的当前里程碑 | 只补缺、只校准 |
| 收尾 / 整理（consolidate） | 先跑 `--inventory`，出清单等确认 | 合并、归档、删除后的收敛结果 |

判断错了代价很高：中期误当开工＝重复造文档；开工误当整理＝把仅有的几份也清掉。拿不准就直接问用户处在哪一步。

## 执行顺序

1. **探测（只读）** — 见下节；先看清项目是什么，再决定写什么。
2. **盘点** — 列出「已有 / 缺失 / 过期」三列，不要边盘点边写。
3. **询问** — 用“谁做什么、会看到什么结果”复述用户已确认的方向。选项中的例子不等于选定的方案。如果同一句需求有两种解释，会改变用户能做什么或看到什么，先说明差别，一次问一个问题。可以后定的记为开放问题；普通、可回滚且不改变使用效果的实现细节留给编码时决定，不逐项追问。
4. **生成** — 只写缺失项；从 `references/templates/` 复制，替换掉所有 `<!-- fill -->`。
5. **交叉校验** — 对照本次立项的原话和已查证的项目事实，核对 README、目标和架构描述的输入、输出与范围是否一致。按交付清单分别核对项目名和目标目录。用户只确认了使用形态时，具体场景可标为示例，影响范围的歧义列为开放问题。建议不得写成决定，候选指标须经用户认可才能作为验收门槛（2026-11-26 立项试用反馈）。README 和 `AGENTS.md` 里的可运行命令须有实际入口；有计划后核对范围，发版时再核对变更记录。
6. **自检** — 新建或调整文档骨架、阶段交付或审计时，使用 skill 安装目录中的校验器，以目标项目为 `-root`（见「校验」）；退出码 `1` 表示有 FAIL，先修；`2` 表示用法或配置错误（不是文档问题）。文档入库时可加 `--staged` 辅助检查。它按索引选文件、读取工作区文本，最终用 `git diff --cached` 审阅实际暂存的内容。日常纯代码改动若未改变文档所述行为、命令或约定，运行对应代码测试即可。
7. **报告** — 新增、修改、跳过分别列清；跳过必须给理由。

新建或整理下游 `AGENTS.md` 时，交付前按 `references/checklist.md` 的 Git 核对项通读成稿。不要求照抄模板：已有等效约定就保留，新生成时漏掉的补齐；已有项目明确采用不同做法时，保留原文，说明差异与影响，让用户取舍。结构检查通过不能代替这一步（2026-11-26 下游试用）。

## 一份文档只有一个家

文档乱的根因不是数量，是同一件事有几份文档。新建文件之前先查这张表；表里没有归属的先问，默认不建。下表用于下游项目，`docs/` 选择性入库。buildhelper 自身的 `docs/` 是维护过程记录，只留本地。

| 内容 | 唯一位置 | 入库 |
|---|---|---|
| 入口、安装、许可 | `README.md`、`INSTALL.md`、`LICENSE` | 是 |
| agent 约束 | `AGENTS.md` | 是 |
| 版本变化 | `CHANGELOG.md` | 是 |
| 目标与非目标 | `docs/goal.md` | 已确认、可共享的目标 |
| 架构、模块边界 | `docs/architecture.md`（模块多才拆 `docs/modules/`） | 已确认、可共享的边界 |
| 里程碑与 DoD | `docs/plan.md` | 已确认的共享路线与验收条件 |
| 决策与理由 | `docs/adr/NNN-*.md` | 已采纳、可共享的决定及理由 |
| 对外接口契约 | `docs/api/` | 可向仓库读者公开的契约 |
| 验收与缺陷 | `docs/test-records.md` | 脱敏后的实测结论与复现方法 |
| 阶段结论、复盘 | `docs/history/`、`docs/postmortems/` | 可共享的结论。原始日志、设备信息和未公开材料留在本地 |

三条推论：

- `*_api.md`、`*_module.md` 散落在模块目录，就是同一件事的多个副本，校验器会报 `duplicate scope`。
- 归档目录（`adr/`、`history/`、`postmortems/`）允许增长；`docs/` 其余文件有预算（`checks.json` 的 `budgets`），超了说明该合并，而不是接着加。
- 过程物料（`plans/`、`specs/`、带日期的设计稿）用完归档成一份阶段结论，原件不要留在现行文档里。


## 存量整理（仅在用户明确要求时）

用户说「整理 / 合并 / 清理 / 迁移文档」才进入；其余情况一律走上一节的「只补缺」。整理会删改已有内容，权限和风险都不同。

1. **递归盘点，不看索引。** 用 `glob` 列出全部 `*.md`（跳过 `node_modules`、`.venv`、构建产物），不要只读 README 的文档索引——索引本身可能过期，没被索引的文档恰恰最该处理。
2. **先分类，不写盘。** 每份标一类：**保留**（仍有效）、**合并**（结论有效但归属错）、**仅本地**（有价值但不入库）、**删除**（已被替代或纯过程流水）。给出四列清单和份数。
3. **合并与删除必须写去处。** 每条都要说明：有效结论搬到哪份文件的哪一节、哪些引用要同步改。没有去处的不能删——原样搬进 `docs/history/` 不算处理，归档不是垃圾桶。
4. **停等确认。** 清单交给用户，等明确批准再动；批准范围之外的文档不碰。
5. **执行后复验。** 跑一次校验，报告删了几份、合并了几条结论、哪些引用被更新、哪些判定为仅本地。

## 探测清单（只读）

- **是不是一个项目**：根目录有 `README` 或清单文件 → 是项目；根目录没有 `README` 但有子目录自带 `.git` → 是容器工作区，让用户挑一个子项目，不要给容器根写文档；纯笔记、归档、下载目录不接入，除非用户明确要求（2026-11-22 studyAI 实测：容器根上校验只会得到 4 个无意义的 FAIL）
- 清单文件：`package.json`、`pyproject.toml`、`go.mod`、`Cargo.toml`、`*.csproj`
- 命令来源：清单里的 `scripts`、`Makefile`、`justfile`、CI 配置
- 已有文档：`README*`、`docs/**`、`CHANGELOG*`、`AGENTS.md`、`CLAUDE.md`
- 写入边界：核对目标项目的 `.gitignore` 和 Git 已跟踪文件。若既有规则会排除原本要共享的文档，说明影响，请用户取舍。
- 事实来源：所有命令从上述文件抄，不凭印象写；查不到就标「未验证」

## 每份文档的最低要求

| 文件 | 必须有什么 |
|---|---|
| `README.md` | 适用人群、用途、已有与待验证的能力。从干净环境到首个可观察结果的步骤，或明确当前尚无可运行入口。只链接已经存在且可共享的文档 |
| `docs/goal.md` | 问题、用户、最终使用效果、非目标、成功标准和粗略阶段路线 |
| `docs/architecture.md`（按需） | 写实际组件边界、数据流和已确认的设计理由。已有 ADR 时再加索引 |
| `docs/adr/NNN-*.md` | 背景、决策、备选、后果 |
| `docs/plan.md` | 本期目标、粗粒度任务、DoD、风险、验收方式 |
| `docs/history/NN-*.md` | 达成情况、未完成及原因、风险、下阶段 |
| `docs/test-records.md` | 验收结论、已知缺陷与复现、证据位置 |
| `AGENTS.md` | 简明协作约定、可复现的命令和运行要求、实际模块边界、禁止事项、验收及本地提交方式 |

长度上限不写在这里：`references/checks.json` 的 `maxLines` 是唯一事实源，超限报 WARN 但不阻断。

## 反模式（禁止）

- 一次性生成全套文档；空表格、空章节、`TBD` 留在交付物里
- 独立 `FIXME.md` / `TODO.md` 当长期仓库（改用 issue，或代码内 `FIXME(owner,#id): 原因`）
- `plan.md` 细化到任务级；`README.md` 里塞目标、架构、计划
- 把命令手抄进 README 而不指向真实脚本名
- 用自己编的目标替代用户确认，或把「待定」当成已完成
- 不要链接此刻不存在的文件：阶段文档等它产生后再加索引（2026-11-22 dogfooding 暴露，模板索引会让立项即断链）
- 存量项目不要为了通过长度检查去压缩 README：先补缺失文档，超长记为已知（2026-11-22 ctrip：168 行 vs 上限 40，压缩等于重写）
- 把「整理」做成「旧文档原样搬进 `docs/history/`」：归档不是去处，结论必须有新的落点，引用也要跟着改
- 只按 README 索引盘点存量文档：没被索引的文件永远处理不到，而它们往往最该处理
- 同一件事开第二份文档：先查「一份文档只有一个家」，有归属就合并进去
- 把 `*_api.md`、`*_module.md` 平铺在模块目录里：这是同一文档的副本，校验会报 `duplicate scope`
- 整理只搬运不收敛：`docs/` 超出 `budgets` 说明还在堆积，搬进 `docs/history/` 不等于处理

## 校验

`scripts/check_docs.py` 检查必填文件、必填章节、长度超限、相对链接、**发布边界**（已发布文件不得链接被 `.gitignore` 忽略的路径）、**重复归属**（`*_api.md` 之类不在唯一位置）、**文档预算**（`docs/` 下的文件数）、ADR 编号、残留占位符、**疑似凭据**。只用 Python 3.8+ 标准库，Windows / macOS / Linux 是同一份脚本。

```text
python3 "<skill 根>/scripts/check_docs.py" -root "<目标项目根>" -stage founding   # macOS / Linux
python  "<skill 根>/scripts/check_docs.py" -root "<目标项目根>" -stage founding   # Windows
```

`-stage` 三档，累计：`founding`（默认，按立项所需文件检查）、`milestone`（加 `docs/plan.md`）、`release`（加 `CHANGELOG.md`）。不确定就先用默认值：直接上 `release` 会给立项阶段的正常缺项刷 FAIL。

三种范围，互斥，选一个：

| 模式 | 校验对象 | 用在哪 |
|---|---|---|
| 本地（默认） | 磁盘上的全部文档，含被忽略的 `docs/` | 写文档时的自检 |
| `--published` | 只校验会随仓库发布的文件，被忽略的从必填清单剔除 | CI、验收克隆下来的仓库 |
| `--staged` | git 索引：这次提交真正会包含的文件 | 提交前、pre-commit |

`--staged` 读的是索引而不是 `.gitignore`，所以「已跟踪但被忽略」的文件照常校验；未跟踪的文档会报 `skip untracked`，工作区与索引内容不同会报 `note worktree differs`（校验的仍是工作区内容）。它不是仓库或无 git 时以 `2` 退出并说明原因。

`--inventory` 是只读报告：为每份文档标出角色（`entry` / `goal` / `architecture` / `api` / `process` …）、行数、是否入库，以及处置建议 `keep` / `merge` / `archive` / `review` 和目标位置。落在某个归属目录里的文档（例如 `docs/api/`、`docs/modules/`、根 `API.md`）直接算 `keep`，不看文件名是否匹配通配符；`merge` 的目标是该归属的第一个允许位置。它不移动、不删除任何文件。整理场景先跑它，把表格交给用户确认，再按批准的范围动手。

凭据扫描是**规则匹配，不是保证**：只匹配常见 Token、云访问密钥、私钥头、带口令的 URL、`password=` 之类的赋值，命中时只输出 `文件:行号` 和规则名，绝不回显原文；`<your-token>`、`xxx`、`example` 这类占位符放行。它不查 Git 历史、不扫被忽略的文件，也不承诺能识别全部秘密——真实凭据不要写进文档，改用环境变量。默认报 WARN，`--strict` 升为 FAIL。

退出码约定：`0` 通过、`1` 有 FAIL、`2` 用法或配置错误（`-root` 不存在、`checks.json` 缺失或语法坏、阶段名不认识、`--published` 与 `--staged` 同时给）。脚本不打印 traceback，错误一律一行 `error: ...`。文档按 UTF-8 → GB18030 依次尝试解码，UTF-8 BOM、CRLF、GBK 都能正确匹配章节。

扫描范围按模式不同：本地模式照常读取必填文件所在的本地文档目录（通常就是被忽略的 `docs/`），其他被忽略路径（归档、生成物、`study/` 这类研究目录）跳过，并打印 `skip  gitignored (not scanned)` 列出排除了哪些；`--published` 只扫会随仓库发布的文件。每次运行都会打印 `config <配置文件>` 和一行 `scan ...`，写明扫了几份、跳过几份，判断「没报警」是真没问题还是没扫到，看这几行。代码围栏里的示例链接和 `<!-- fill -->` 不算真链接、也不算未填占位符。没有 Python 时不要硬跑，按 `references/checklist.md` 人工核对。

阶段、章节、长度、文档预算、归属规则都在 `references/checks.json`，要加检查项就改那个文件，不改脚本。

### 项目适配

配置中，`files` 条目的 `checkIfPresent: true` 让校验器在文档出现后检查章节和长度。下游架构文档默认采用这条规则。如果项目把同一文件列入某个 `stages` 阶段，从该阶段起按必填处理。发布模式和暂存模式沿用各自的文件范围。

存量项目可用 `-config` 指向自己的配置：

```text
python "<skill 根>/scripts/check_docs.py" -root "<目标项目根>" -config "<skill 根>/references/checks-stock.json"
```

`references/checks-stock.json` 是现成起点：它 `extends` 基础配置，只放宽已有 README 和架构文档的长度上限，其他规则照旧。要更具体的调整，写一份新 JSON 并 `extends` 基础配置——只写差异项，`files` 按文件浅合并，其余键整键覆盖；`extends` 成环以 `2` 退出。

## 资源

- `references/templates/` — 9 份模板，按阶段门取用。指令模板使用 `AGENTS.template.md`，防止被误读为当前生效的 `AGENTS.md`
- `references/checklist.md` — 交付前逐条勾
- `references/checks.json` — 唯一规则源：阶段 → 文件集、必填章节、长度上限、凭据规则
- `references/checks-stock.json` — 存量项目起点配置：`extends` 基础规则，只放宽长度
- `scripts/check_docs.py` — 必填文件 / 必填章节 / 相对链接 / ADR 编号 / 占位符 / 发布边界 / 凭据
