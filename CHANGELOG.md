# 变更日志

> 只记对外可见的变化：新增、变更、修复、移除。破坏性变更标 **BREAKING**。

## 未发布

### 新增

- 发布边界检查：已发布的文件如果链接到被 `.gitignore` 忽略的路径，报 WARN（ADR-007）
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
