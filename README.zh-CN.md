# buildhelper

[English](README.md) | 简体中文

把「一个项目该有哪些文档、什么时候写、怎么不烂」变成 agent 能直接执行的流程。不是文档生成器，而是一层约束：什么时候该产出什么、只补缺不重写、写完怎么校验。当前 0.2.0：克隆即可用。

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
scripts/check_docs.py       校验脚本（Python 3.8+，仅标准库）
scripts/test_check_docs.py  校验脚本的单元测试
docs/                       本项目文档（本地，不发布）
```

## 校验

- 新克隆后校验发布文件：`python scripts/check_docs.py -root . -stage release --published`
- 校验含 `docs/` 的本地文档集：`python scripts/check_docs.py -root . -stage founding`
- 校验这次提交真正包含的文档：加 `--staged`；占位符与疑似凭据直接判失败：加 `--strict`
- 存量项目：`-config references/checks-stock.json` 只放宽长度上限
- 阶段累计（`founding` → `milestone` → `release`）；退出码 `0` 通过、`1` 有 FAIL、`2` 用法或配置错误。没有 Python 时按 `references/checklist.md` 人工核对。

## 文档

文档集（目标、架构、计划、ADR、阶段与测试记录）默认只留本地，不随仓库发布——这是设计，不是缺失（ADR-007）。安装与接入见 [接入方式](INSTALL.zh-CN.md)。

许可：MIT（见 [LICENSE](LICENSE)）。
