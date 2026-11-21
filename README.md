# buildhelper

把「一个项目该有哪些文档、什么时候写、怎么不烂」变成 agent 能直接执行的流程。不是文档生成器，而是一层约束：什么时候该产出什么、只补缺不重写、写完怎么校验。当前是原型：克隆即可用，未发布。

## 安装

```powershell
git clone <repo-url> <你的项目>\.dsh\skills\project-docs
```

克隆完即可用：`.dsh/skills` 只发现一层，`project-docs/SKILL.md` 就是入口。目标项目记得把 `.dsh/` 写进 `.gitignore`，否则会多出一个嵌套仓库。

## 结构

```
SKILL.md                 流程、阶段门、反模式
references/              checklist、checks.json、9 份模板
scripts/check-docs.ps1   校验脚本（纯 ASCII）
docs/                    本项目的目标、架构、计划、ADR
```

## 校验

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-docs.ps1 -Root .
```

退出码 0 才算通过；FAIL 必须修完再报告，WARN 要逐条判断。

## 文档

| 文档 | 内容 |
|---|---|
| [目标与范围](docs/goal.md) | 为什么做、不做什么 |
| [技术架构](docs/architecture.md) | 四层结构与边界 |

计划、ADR、阶段记录属于本地过程文档，不随仓库发布（见 `.gitignore`）。

许可：未定。
