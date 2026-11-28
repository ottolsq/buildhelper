# buildhelper

[English](README.md) | 简体中文

buildhelper 帮你和编码 agent 约定项目目标、文档和工作方式。立项时先写清最终想看到的效果，每个阶段再选一段能实际试用的流程，写清怎样验证、哪些改动可以一起提交。已有项目从现有文档开始，只补缺项。

## 安装

没有通用路径，取决于你的 agent：DSH 认 `.dsh/skills/` 与 `.agents/skills/`，Claude Code 认 `.claude/skills/`，完全没有 agent 也能当模板库用。

```powershell
git clone <repo-url> .agents/skills/project-docs
```

跨工具约定是 `.agents/skills/`。其它工具的接法、无 agent 的用法、更新与锁版本见 [接入方式](INSTALL.zh-CN.md)。

## 结构

```
SKILL.md                    流程、阶段门、反模式
references/                 checks.json、checks-stock.json、checklist、9 份模板
scripts/                    校验器 check_docs.py 及其单元测试（Python 3.8+，仅标准库）
```

## 仓库边界

- 根目录的 [AGENTS.md](AGENTS.md) 供 buildhelper 维护者使用。下游项目保留已有协作约定，新建 `AGENTS.md` 时参考[下游项目模板](references/templates/AGENTS.template.md)。
- buildhelper 的维护记录（`docs/`）、试验材料（`temp/`）和本机配置（`.env`、`.env.*`）留在本地。只含占位值的 `.env.example` 可以共享。
- 下游项目沿用自己的 `.gitignore`，从 `docs/` 中选择要共享的目标、计划和设计决定。若仅供本机使用，只忽略 skill 的具体安装目录，示例见[安装说明](INSTALL.zh-CN.md)。

## 校验

- 新克隆后校验发布文件：`python scripts/check_docs.py -root . -stage release --published`
- 校验含 `docs/` 的本地文档集：`python scripts/check_docs.py -root . -stage founding`
- 校验这次提交真正包含的文档：加 `--staged`；占位符与疑似凭据直接判失败：加 `--strict`
- 存量项目：`-config <skill>/references/checks-stock.json` 直接使用，不要复制（`extends` 按配置文件所在目录解析）；项目自己的规则另写配置 `extends` 它
- 一份文档只有一个家：`--inventory` 列出每份文档的角色与 keep/merge/archive 建议；归属规则与 `docs/` 预算在 `references/checks.json`
- 阶段累计（`founding` → `milestone` → `release`）；退出码 `0` 通过、`1` 有 FAIL、`2` 用法或配置错误。没有 Python 时按 `references/checklist.md` 人工核对。

许可：MIT（见 [LICENSE](LICENSE)）。
