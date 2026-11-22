# buildhelper

把「一个项目该有哪些文档、什么时候写、怎么不烂」变成 agent 能直接执行的流程。不是文档生成器，而是一层约束：什么时候该产出什么、只补缺不重写、写完怎么校验。当前是原型：克隆即可用，未发布。

## 安装

没有通用路径，取决于你的 agent：DSH 认 `.dsh/skills/` 与 `.agents/skills/`，Claude Code 认 `.claude/skills/`，完全没有 agent 也能当模板库用。

```powershell
git clone <repo-url> .agents/skills/project-docs
```

跨工具约定是 `.agents/skills/`。其它工具的接法、无 agent 的用法、更新与锁版本见 [接入方式](docs/install.md)。

## 结构

```
SKILL.md                流程、阶段门、反模式
references/             checks.json、checklist、9 份模板
scripts/check_docs.py   校验脚本（Python 3.8+，仅标准库）
docs/                   本项目的目标与架构
```

## 校验

`python scripts\check_docs.py -root . -stage founding`（macOS/Linux 用 `python3`；`-stage` 取 founding / milestone / release，累计）。退出码 `0` 通过、`1` 有 FAIL、`2` 用法或配置错误；没有 Python 时按 `references/checklist.md` 人工核对。

## 文档

| 文档 | 内容 |
|---|---|
| [目标与范围](docs/goal.md) | 为什么做、不做什么 |
| [技术架构](docs/architecture.md) | 四层结构与边界 |

计划、ADR、阶段记录属于本地过程文档，不随仓库发布（见 `.gitignore`）。

许可：MIT（见 [LICENSE](LICENSE)）。
