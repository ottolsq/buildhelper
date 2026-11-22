# 接入方式

[English](INSTALL.md) | 简体中文

这个仓库本身就是一个 skill 包，但「装到哪」取决于你用哪个 agent——没有一条路径是通用的。下面按从强到弱排。

## 一、支持 SKILL.md 的 agent

`<name>/SKILL.md` 是通用形态，各工具只是扫描的目录不同：

| 工具 | 项目级 | 用户级 |
|---|---|---|
| DSH | `.dsh/skills/`、`.agents/skills/` | `~/.dsh/skills/`、`~/.agents/skills/` |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Codex CLI / ChatGPT | 见其 skills 设置 | 同上 |
| 跨工具约定 | `.agents/skills/` | `~/.agents/skills/` |

默认装到跨工具约定的位置，DSH 直接识别，多数工具也能链过去：

```bash
git clone <repo-url> .agents/skills/project-docs
```

只认自己目录的工具，把它链过去即可（Windows 需要开发者模式或管理员权限）：

```bash
ln -s ../../.agents/skills/project-docs .claude/skills/project-docs
```

## 二、不支持 skill 的 agent

不用改目录结构，两种办法：

1. 在项目根的 `AGENTS.md` 或规则文件里加一行指针，让 agent 自己去读：文档流程见 `.agents/skills/project-docs/SKILL.md`。
2. 直接把 `SKILL.md` 的内容贴进对话。

## 三、没有 agent

仓库退化成一套模板 + 一份清单，`git clone` 到任意目录都行：

- `references/templates/` — 9 份文档模板，复制后填
- `references/checklist.md` — 交付前逐条勾
- `scripts/check_docs.py` — 有 Python 3.8+ 就跑，没有就人工核对

## 更新与锁版本

```bash
git -C <项目>/.agents/skills/project-docs pull   # 更新到最新
git clone --branch <tag> <repo> ...             # 锁版本（打了 tag 之后才有意义）
```

## 两个坑

- 目录名必须与 frontmatter 的 `name` 一致（`project-docs`）。同一 skill 根下两个同名目录会撞名，靠 rank 或扫描顺序决定谁生效。
- 装进项目后把该目录写进 `.gitignore`，否则项目里会多一个嵌套 `.git` 仓库。想让它进版本库，就用 submodule，别直接提交。
