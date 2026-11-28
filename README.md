# buildhelper

English | [简体中文](README.zh-CN.md)

buildhelper helps you and your coding agent agree on a project's goals, documentation and working rules. At kickoff, record the intended outcome. For each milestone, describe one workflow someone can try, how to verify it, and which changes belong in the same commit. Start with the documents your project already has.

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
scripts/                     check_docs.py validator and its tests (Python 3.8+, stdlib only)
```

## Repository boundaries

- The root [AGENTS.md](AGENTS.md) guides buildhelper maintainers. Keep your project's existing instructions. When creating a new `AGENTS.md`, adapt the [project template](references/templates/AGENTS.template.md).
- buildhelper keeps its development notes (`docs/`), trial runs (`temp/`) and local configuration (`.env`, `.env.*`) on the maintainer's machine. A placeholder-only `.env.example` can be shared.
- Your project uses its own `.gitignore`. Choose which goals, plans and decisions to share in `docs/`. For a local skill installation inside the project, ignore just the installation directory as shown in the [installation guide](INSTALL.md).

## Validate

- Published surface, as a fresh clone sees it: `python scripts/check_docs.py -root . -stage release --published`
- Local doc set including `docs/`: `python scripts/check_docs.py -root . -stage founding`
- What a commit would contain: add `--staged`; make placeholders and secrets fail: add `--strict`
- Existing projects: use `-config <skill>/references/checks-stock.json` directly — no copy, since `extends` resolves from the config's own directory; project rules go in a separate config that extends it
- One home per document: `--inventory` lists every file with a role and a keep/merge/archive proposal; `scopes` and the `docs/` budget live in `references/checks.json`
- Stages accumulate (`founding`, `milestone`, `release`); exit `0` pass, `1` findings, `2` usage error. Without Python, use `references/checklist.md`.

License: MIT (see [LICENSE](LICENSE)).
