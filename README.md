# buildhelper

把「一个项目该有哪些文档、什么时候写、怎么不烂」变成 agent 能直接执行的流程。不是文档生成器，而是一层约束：什么时候该产出什么、只补缺不重写、写完怎么校验。当前是原型：克隆即可用，未发布。

## 安装

落点相同，选一种：

```powershell
git clone <repo-url> <项目>\.dsh\skills\project-docs   # 自己跑
```

或者把仓库地址给 agent，让它执行同一条命令。目录名必须是 `project-docs`：`.dsh/skills` 只发现一层，入口是 `project-docs/SKILL.md`。

已安装则更新：`git -C <项目>\.dsh\skills\project-docs pull`。目标项目把 `.dsh/` 写进 `.gitignore`，否则会多一个嵌套仓库。

## 结构

```
SKILL.md                流程、阶段门、反模式
references/             checks.json、checklist、9 份模板
scripts/check_docs.py   校验脚本（Python 3.8+，仅标准库）
docs/                   本项目的目标与架构
```

## 校验

`python scripts\check_docs.py -root .`（macOS/Linux 用 `python3`）。退出码 `0` 通过、`1` 有 FAIL、`2` 用法或配置错误；没有 Python 时按 `references/checklist.md` 人工核对。

## 文档

| 文档 | 内容 |
|---|---|
| [目标与范围](docs/goal.md) | 为什么做、不做什么 |
| [技术架构](docs/architecture.md) | 四层结构与边界 |

计划、ADR、阶段记录属于本地过程文档，不随仓库发布（见 `.gitignore`）。

许可：未定。
