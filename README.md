# git-archaeologist

**Uncover *why* your code exists — not just what it does.**

`git-archaeologist` is a CLI tool that mines your git history, commit messages, pull requests, and linked issues to generate a narrative explanation of *why* a piece of code was written. Powered by the OpenAI API.

```
$ git-arch why src/auth/tokens.py:verify_token
```

> *"This function was introduced in commit `a3f12c` on 2021-08-14 to address CVE-2021-44228. The original implementation used MD5 for token signing, which was flagged in a security audit (PR #234). The `HMAC-SHA256` switch happened three weeks later after a coordinated incident with the platform team. The rate-limiting wrapper around line 48 was added in early 2022 after a brute-force attempt was detected in production logs (closes #891)..."*

[![CI](https://github.com/git-archaeologist/git-archaeologist/actions/workflows/ci.yml/badge.svg)](https://github.com/git-archaeologist/git-archaeologist/actions)
[![PyPI](https://img.shields.io/pypi/v/git-archaeologist)](https://pypi.org/project/git-archaeologist/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![codecov](https://codecov.io/gh/git-archaeologist/git-archaeologist/branch/main/graph/badge.svg)](https://codecov.io/gh/git-archaeologist/git-archaeologist)

---

## The problem

You're staring at a function you didn't write. The variable is named `_legacy_compat_flag`. There's a comment that says `# DO NOT REMOVE`. Git blame shows eight different authors over four years. The commit messages say things like "fix" and "update stuff".

You have no idea why this code exists or what disaster it was preventing.

`git log`, `git blame`, and `grep` give you *what* changed. `git-archaeologist` tells you *why*.

---

## Features

- **Narrative explanation** — A prose explanation of the code's history, decisions, and context
- **Key decision extraction** — Surfaces architectural choices with evidence from commit history
- **PR and issue linking** — Automatically correlates commits to pull request bodies and closed issues
- **Line-range targeting** — Analyze specific lines, functions, or entire files
- **Multiple output formats** — Rich terminal output, Markdown, or JSON for piping
- **Contributor archaeology** — Shows who shaped the code over time, weighted by contribution

---

## Installation

```bash
pip install git-archaeologist
```

Set your OpenAI API key:

```bash
export OPENAI_API_KEY=sk-...
```

---

## Usage

### Explain a file

```bash
git-arch why src/payments/processor.py
```

### Explain specific lines

```bash
git-arch why src/payments/processor.py:45-120
```

### Go deep (more commit history)

```bash
git-arch why src/payments/processor.py --depth 200
```

### Output as Markdown (for documentation or sharing)

```bash
git-arch why src/payments/processor.py --format markdown > why-processor.md
```

### Output as JSON (for scripts or integrations)

```bash
git-arch why src/payments/processor.py --format json | jq '.key_decisions'
```

### Analyze a repo that isn't your CWD

```bash
git-arch why src/core/engine.py --repo /path/to/other/repo
```

### Show evolution timeline for a file

```bash
git-arch timeline src/payments/processor.py
```

---

## Example output

```
╭──────────────────────────────────── git-archaeologist ─────────────────────────────────────╮
│                          src/auth/tokens.py:verify_token                                    │
│                              47 commits analyzed                                            │
╰────────────────────────────────────────────────────────────────────────────────────────────╯

──────────────────────── Timeline ────────────────────────
  Simple JWT verification in 2020, full rewrite after a CVE in mid-2021,
  incremental hardening through 2022-2023.

──────────────────────── Historical Narrative ────────────────────────

This function was first introduced on 2020-03-12 as a thin wrapper around
PyJWT's `decode()`. At the time the service handled fewer than 1,000 requests
per day and security requirements were minimal.

Everything changed in August 2021. CVE-2021-44228 and an internal security
audit (documented in PR #234) revealed that the token signing scheme was using
MD5-derived keys. Over a two-week incident sprint, the team replaced the
implementation with HMAC-SHA256, added key rotation support, and introduced
the `_clock_skew_tolerance` parameter to handle clock drift in distributed
deployments.

The rate-limiting wrapper added in commit `b9a44f` (January 2022) followed
a specific incident: a credential-stuffing attack described in issue #891
revealed that the verification endpoint had no throttling. The 50ms artificial
delay and IP-based rate limiter were added as a stopgap; a proper API gateway
rule replaced them in March 2022, but the delay was kept after load tests
showed no significant performance impact.

──────────────────────── Key Decisions ────────────────────────
  ▸ Switched from MD5 to HMAC-SHA256 signing (PR #234, Aug 2021 CVE response)
  ▸ Added clock-skew tolerance for distributed deployment (PR #241)
  ▸ Retained artificial 50ms delay after CVE stopgap was superseded (perf tested, no impact)
  ▸ Kept legacy token format support for backwards compatibility with mobile clients v1.x

──────────────────────── Contributors ────────────────────────
  Alice Chen, Bob Martinez, Fatima Al-Hassan, Dev Patel

  First introduced    2020-03-12
  Last modified       2023-11-04
  Total commits       47
```

---

## How it works

1. **Target parsing** — Resolves your `file:line` or `file:start-end` target
2. **Git mining** — Runs `git log -L` (line-level history) or `git log --follow` (file-level), extracting commit SHAs, messages, diffs, PR numbers, and issue references
3. **Context assembly** — Correlates commits to PR bodies and issue numbers extracted from commit messages
4. **LLM synthesis** — Sends the structured history to the OpenAI API with a prompt tuned for archaeological reasoning, not just summarization
5. **Structured output** — Parses the response into narrative, timeline, and key decisions; renders it in your chosen format

The tool uses `gpt-4o` by default. You can use `--model gpt-4o-mini` for faster, cheaper runs at the cost of depth.

---

## Why this needs the OpenAI API

`git-archaeologist` is fundamentally a *reasoning* tool, not a retrieval one. The raw git history for a file can span dozens of commits, thousands of lines of diff, and references to external PRs and issues. Extracting *why* decisions were made from that signal requires natural language understanding that cannot be replicated with pattern matching or search alone.

We use the OpenAI API (specifically `gpt-4o`) for:

- **Historical synthesis**: Connecting a 2021 security commit to the CVE it was responding to, even when the commit message just says "security hardening"
- **Decision archaeology**: Identifying *why* code that looks redundant was kept, by cross-referencing PR discussion language
- **Timeline narration**: Constructing a coherent story from dozens of disconnected commits in chronological order
- **Implicit knowledge extraction**: Surfacing tribal knowledge embedded in commit messages, PR comments, and issue bodies

The quality of analysis degrades significantly with smaller models. Monthly API costs for a typical OSS project (analyzing a few files per day) run ~$5-15/month, which is a meaningful barrier for volunteer-maintained projects.

---

## Roadmap

- [ ] GitHub API integration for richer PR/issue body fetching
- [ ] GitLab support
- [ ] `git-arch blame` — AI-narrated git blame (per-line historical context)
- [ ] `git-arch compare` — Explain the difference between two versions of a function
- [ ] Pre-commit hook mode — Auto-generate archaeological context in commit messages
- [ ] VS Code extension

---

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions.

```bash
git clone https://github.com/git-archaeologist/git-archaeologist
cd git-archaeologist
pip install -e ".[dev]"
pytest
```

---

## License

MIT — see [LICENSE](LICENSE).
