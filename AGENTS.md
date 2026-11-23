# AGENTS.md — buildhelper

## 命令

```powershell
# 校验文档骨架。退出码 0 通过 / 1 有 FAIL / 2 用法或配置错误
python scripts\check_docs.py -root . -stage founding
# 阶段累计：milestone 加 docs/plan.md，release 加 CHANGELOG.md
# 发布物 / 提交内容 / 存量项目长度放宽
python scripts\check_docs.py -root . -stage release --published
python scripts\check_docs.py -root . --staged
python scripts\check_docs.py -root . -config references\checks-stock.json
# 反例：空目录 founding 应 exit 1；release 缺 CHANGELOG 应 exit 1；未知阶段应 exit 2；--published 与 --staged 同给应 exit 2
# 单元测试只能在 CI 跑；本地想验证行为用 python temp\verify_batch2.py（见环境事实）
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

## 环境事实

- Windows 11 + PowerShell 5.1；有 `python`（3.15）和 `git`，没有 `pnpm`，没有 `rg`
- 校验脚本是 Python：`python scripts\check_docs.py -root .`；`.ps1` 已删除，不要再写 `powershell -File`
- `Get-Content` 默认按 ANSI 解码，读 UTF-8 中文会乱码（行数也会数错）；读文件必须带 `-Encoding UTF8`
- 沙箱内 `git clone <本地路径>` 会失败（msys sh 起不来，`0xC0000022`）；要检查提交内容就用 `git archive` 导出，真实 clone 留给沙箱外的终端（2026-11-21 实测）
- 单元测试 `python scripts/test_check_docs.py` 在本机沙箱内必定失败，原因不是测试写错：`tempfile` 用 `os.mkdir(..., 0o700)` 建目录，沙箱令牌随后无法列举该目录（`PermissionError: [WinError 5]`，实测 `os.mkdir(r'temp\m700', 0o700)` 后 `os.listdir` 立即失败，`0o777` 正常）；另外 git 对象文件是只读的，`shutil.rmtree` 删不掉。它由 CI 运行，本地不要据此判断测试坏了（2026-11-23 实测）
- 本地验证校验器行为用 `python temp\verify_batch2.py`：它用 `os.makedirs` 建夹具、直接驱动 CLI，覆盖 `--staged` / 凭据 / `extends` / 存量配置，结果应与 CI 的单元测试一致
- 确实要在本机跑整套 unittest 时用本机临时包装（不入库）：`temp\run_unittest.py` 把 `tempfile.TemporaryDirectory` 换成 `%TEMP%` 下 0o777 目录，并把夹具放在仓库外（否则 `--staged` 的「非 Git 仓库」用例会被仓库本身命中）；17 个用例实测 OK（2026-11-23）
- 项目根：`C:\Users\ottol\myproject\buildhelper`（git 仓库）
- 仓库根即 skill 根（ADR-004）：`SKILL.md`、`references/`、`scripts/` 直接在根；装到 `.dsh/skills/` 或跨工具的 `.agents/skills/`，本机尚未安装到任何 agent
- 文档写入白名单：`README.md`、`CHANGELOG.md`、`AGENTS.md`、`SKILL.md`、`docs/**`、`references/**`、`scripts/**`

## 完成定义

- 改 `SKILL.md`、模板、`checks.json` 或 `check_docs.py` 后，必须跑三档 `-stage` 并贴实际输出：正常 `0`、空目录 `1`、坏配置或未知阶段 `2`
- 改校验器后还要跑 `--published`、`--staged`、`--strict` 与 `-config references\checks-stock.json`，再加 `python temp\verify_batch2.py` 应全 PASS
- 新增检查项时同时给正例（应 0 FAIL）和反例（应非 0）
- 文档与实现不一致时先改文档

## 文档指针

- 目标与范围：`docs/goal.md`（仅本地）
- 架构：`docs/architecture.md`（仅本地）
- 计划与 DoD：`docs/plan.md`（仅本地）
- 决策：`docs/adr/`（仅本地）
