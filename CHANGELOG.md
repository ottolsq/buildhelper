# 变更日志

> 只记对外可见的变化：新增、变更、修复、移除。破坏性变更标 **BREAKING**。

## 未发布

### 新增

- CI 增加一步：运行 `scripts/test_check_docs.py`（stdlib unittest，不引入 pytest）。
- `SKILL.md` 增加「存量整理」流程：递归盘点（不依赖 README 索引）→ 四类标注（保留/合并/仅本地/删除）→ 指明合并去处与引用更新 → 等确认 → 复验。仅在用户明确要求时进入。
- `references/checklist.md` 增加存量整理清单。

### 变更

- 文档以英文为主：`README.md`、`INSTALL.md` 改为英文，中文版移到 `README.zh-CN.md`、`INSTALL.zh-CN.md`。
- 本地模式改为同时扫描本地文档目录：被 `.gitignore` 忽略、但属于必填文件所在目录（通常是 `docs/`）的文档仍参与链接与占位符检查；其他被忽略路径继续跳过。
- 每次运行都打印一行 `scan ...`，说明实际扫描份数与跳过份数。

### 修复

- 必填章节按 Markdown `#` 标题的层级和名称校验，不再把正文、代码块或注释中的示例当成章节。
- `--published` 不再检查被忽略的本地 ADR；发布边界识别 `docs/drafts/` 等带目录层级的忽略规则。
- 代码围栏内的示例链接不再误报断链；围栏内的占位符标记也不算未填。
- 发布边界告警只在「发布文件链接到被忽略路径」时触发，本地文档之间互链不再误报。

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
