# Install

English | [简体中文](INSTALL.zh-CN.md)

This repository is itself a skill package, but *where* it goes depends on your agent — there is no universal path. Ordered from strongest integration to weakest.

## 1. Agents that support SKILL.md

`<name>/SKILL.md` is the portable form; tools differ only in which directory they scan:

| Tool | Project-level | User-level |
|---|---|---|
| DSH | `.dsh/skills/`, `.agents/skills/` | `~/.dsh/skills/`, `~/.agents/skills/` |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Codex CLI / ChatGPT | see its skills settings | same |
| Cross-tool convention | `.agents/skills/` | `~/.agents/skills/` |

Install into the cross-tool location; DSH picks it up directly and most tools can be linked to it:

```bash
git clone <repo-url> .agents/skills/project-docs
```

Tools that only read their own directory: link it (on Windows this needs developer mode or admin rights):

```bash
ln -s ../../.agents/skills/project-docs .claude/skills/project-docs
```

## 2. Agents without skill support

No directory change needed; two options:

1. Add a pointer in the project's `AGENTS.md` or rules file: the doc workflow lives in `.agents/skills/project-docs/SKILL.md`.
2. Paste the contents of `SKILL.md` into the conversation.

## 3. No agent at all

The repo degrades to templates plus a checklist; `git clone` it anywhere:

- `references/templates/` — 9 document templates, copy and fill in
- `references/checklist.md` — tick through it before delivery
- `scripts/check_docs.py` — run it with Python 3.8+, or review by hand without it

## Updating and pinning

```bash
git -C <project>/.agents/skills/project-docs pull   # update to latest
git clone --branch <tag> <repo> ...                 # pin (meaningful once tags exist)
```

## Two gotchas

- The directory name must match the frontmatter `name` (`project-docs`). Two same-name bundles under one skill root collide; rank or scan order decides which one wins.
- Add the directory to the project's `.gitignore`, or the project gains a nested `.git` repository. If it must be versioned, use a submodule — do not commit it directly.
