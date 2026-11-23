# 变更日志

> 只记对外可见的变化：新增、变更、修复、移除。破坏性变更标 **BREAKING**。

## 0.3.0 — 2026-11-23

### 新增

- `--inventory`：只读盘点，为每份文档标出角色、行数、是否入库，以及 `keep` / `merge` / `archive` / `review` 处置建议和目标位置；不移动、不删除文件。
- `scopes`：同一类文档只能有一个家，`*_api.md`、`*_module.md` 出现在 `docs/api`、`docs/architecture.md` 之外时报 `duplicate scope`。
- `budgets`：`docs/` 下未归档的文档数超出预算时报 WARN；`adr/`、`history/`、`postmortems/` 不计入。
- `SKILL.md` 增加「三种调用场景」（开工 / 中期 / 收尾整理）与「一份文档只有一个家」归属表。
- `references/checklist.md` 增加 inventory 与归属、预算条目。
- CI 增加一步：运行 `scripts/test_check_docs.py`（stdlib unittest，不引入 pytest）。
- `--staged`：以 git 索引为准校验「这次提交会包含的文档」，已跟踪但被忽略的文件照常检查，未跟踪文件报 `skip`；与 `--published` 互斥。
- 凭据扫描：内置 GitHub Token、AWS 访问密钥、私钥头、带口令 URL、`password=` 赋值等规则；命中只报文件、行号与规则名，不回显原文；占位符放行，`--strict` 时升为 FAIL。
- 配置 `extends`：项目配置只写差异项即可继承基础规则，成环按配置错误退出。
- `references/checks-stock.json`：存量项目起点配置，只放宽既有 README 与架构文档的长度上限。
- `SKILL.md` 增加「存量整理」流程：递归盘点（不依赖 README 索引）→ 四类标注（保留/合并/仅本地/删除）→ 指明合并去处与引用更新 → 等确认 → 复验。仅在用户明确要求时执行。
- `references/checklist.md` 增加存量整理清单。
- `--inventory` 把落在归属目录里的文档（`docs/api/`、`docs/modules/`、根 `API.md`）直接判为 `keep`，不再因为文件名不匹配通配符而落到 `review`；`scopes.api` 的允许位置增加根 `API.md`，`merge` 目标仍是归属的第一个位置。

### 变更

- 文档以英文为主：`README.md`、`INSTALL.md` 改为英文，中文版移到 `README.zh-CN.md`、`INSTALL.zh-CN.md`。
- 本地模式改为同时扫描本地文档目录：被 `.gitignore` 忽略、但属于必填文件所在目录（通常是 `docs/`）的文档仍参与链接与占位符检查；其他被忽略路径继续跳过。
- 每次运行都打印 `config <配置文件>` 和一行 `scan ...`，说明用的是哪份配置、实际扫描份数与跳过份数。
- `-root` 可以指向仓库子目录，`--staged` 会把索引路径映射回该子目录。

### 修复

- 必填章节按 Markdown `#` 标题的层级和名称校验，不再把正文、代码块或注释中的示例当成章节。
- `--published` 不再检查被忽略的本地 ADR；发布边界识别 `docs/drafts/` 等带目录层级的忽略规则。
- 代码围栏内的示例链接不再误报断链；围栏内的占位符标记也不算未填。
- 发布边界告警只在「发布文件链接到被忽略路径」时触发，本地文档之间互链不再误报。
- `--staged` 不再把外层仓库的索引当成项目自己的：`-root` 是子目录时按前缀过滤索引路径。
- 凭据扫描的占位符判断改为看「命中的值」本身，`ghp_xxx…` 这类占位符不会因为替换后变成合法长度而误报。

## 0.2.0 — 2026-11-22

### 新增

- 发布边界检查：已发布的文件如果链接到被 `.gitignore` 忽略的路径，报 WARN（ADR-007）
- 容器工作区提示：根目录没有 `README` 但子目录自带 `.git` 时，提示改为对子项目跑 `-root`
- `--published`：只校验发布物，把 `.gitignore` 忽略的文件从必填清单里剔除（克隆里没有 `docs/`）
- CI：ubuntu（3.8 / 3.12）、windows、macos 四组合跑正反用例

### 变更

- 扫描跳过目标 `.gitignore` 忽略的路径（支持目录、通配符、根锚定；不支持 `!` 取反）
- **BREAKING**：`docs/` 整体改为本地，不随仓库发布；安装文档从 `docs/install.md` 移到根 `INSTALL.md`（ADR-007）

## 0.1.0 — 2026-11-22

### 新增

- `SKILL.md`：阶段门（立项 / 里程碑开始 / 里程碑结束 / 发版 / 复盘）、执行顺序、反模式
- `references/templates/`：9 份文档模板（README、goal、architecture、plan、phase、test-records、adr、postmortem、AGENTS）
- `references/checks.json`：唯一规则源（阶段 → 文件集、必填章节、长度上限）
- `scripts/check_docs.py`：校验器，退出码 `0` 通过 / `1` 有 FAIL / `2` 用法或配置错误
- `docs/install.md`：skill 型 agent、非 skill 型 agent、完全无 agent 三种接入方式

### 变更

- 校验器从 Windows PowerShell 换成 Python，跨平台且误用不再抛栈（ADR-005）
- 规则迁入 `checks.json` v2，新增 `-stage` 累计语义与长度 WARN（ADR-006）
- 仓库根即 skill 根，克隆到 `.agents/skills/` 或 `.dsh/skills/` 即可用（ADR-004）

### 修复

- 模板 README 与 architecture 提前链接尚未产生的文件，导致立项即断链
- 模板命名 `test-record.md` 与 `SKILL.md` 里的 `test-records.md` 不一致
