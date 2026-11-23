# buildhelper

English | [简体中文](README.zh-CN.md)

Turn "which documents a project needs, when to write them, and how to keep them from rotting" into a workflow an agent can execute. Not a document generator — a constraint layer: what to produce at which stage, fill gaps only, and validate what you wrote. Current: 0.2.0, clone and use.

## Install

There is no universal path — it depends on your agent. DSH reads `.dsh/skills/` and `.agents/skills/`, Claude Code reads `.claude/skills/`, and with no agent at all the repo still works as a template library.

```powershell
git clone <repo-url> .agents/skills/project-docs
```

`.agents/skills/` is the cross-tool convention. Other agents, no-agent use, updating and pinning: see [INSTALL.md](INSTALL.md).

## Layout

```
SKILL.md                     workflow, stage gates, anti-patterns
references/                  checks.json, checks-stock.json, checklist, 9 templates
scripts/check_docs.py        validator (Python 3.8+, stdlib only)
scripts/test_check_docs.py   unit tests for the validator
docs/                        this project's docs (local, not published)
```

## Validate

- Published surface, as a fresh clone sees it: `python scripts/check_docs.py -root . -stage release --published`
- Local doc set including `docs/`: `python scripts/check_docs.py -root . -stage founding`
- What a commit would contain: add `--staged`; make placeholders and secrets fail: add `--strict`
- Existing projects: `-config references/checks-stock.json` relaxes page-length limits only
- One home per document: `--inventory` lists every file with a role and a keep/merge/archive proposal; `scopes` and the `docs/` budget live in `references/checks.json`
- Stages accumulate (`founding`, `milestone`, `release`); exit `0` pass, `1` findings, `2` usage error. Without Python, use `references/checklist.md`.

## Docs

The doc set (goal, architecture, plan, ADRs, phase and test records) stays local by design and is not published — intentional, not missing (ADR-007). Install details in [INSTALL.md](INSTALL.md).

License: MIT (see [LICENSE](LICENSE)).
