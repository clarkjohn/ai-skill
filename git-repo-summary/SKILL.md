---
summary: "Summarize a git repo by churn, bug hotspots, ownership, velocity, and firefighting signals."
read_when:
  - Auditing a repository quickly.
  - Deciding which files and team risks to inspect first.
---
# Git Repo Summary

Origin: adapted from https://piechowski.io/post/git-commands-before-reading-code/

Purpose: summarize a git repo fast by churn, bug hotspots, ownership, velocity, and firefighting.

Default path:
1. Run the bundled helper first.

```bash
scripts/git_repo_summary [repo] --window "1 year ago"
```

2. If the user wants machine-readable output:

```bash
scripts/git_repo_summary [repo] --format json
```

Use raw `git` commands only when:
- the helper output looks wrong
- the user asks for the underlying commands
- you need a repo-specific follow-up not covered by the helper

Interpretation:
- Prioritize files high in both churn and recent bug rank.
- Concentrated ownership = key-person risk.
- Diffuse ownership on a hotspot = shared-ownership drag.
- Test pairing is best-effort only; do not overclaim.
- Missing bug or firefight signal can be a commit-message problem, not a stability signal.
- Squash merges can distort authorship; say that when history suggests it.

Output:
1. `Summary`
2. `Top Risk Files`
3. `Team Signals`
4. `Velocity`
5. `Firefighting`
6. `Read Next`

Rules:
- Prefer helper output over hand-built shell pipelines.
- Include concrete counts.
- Keep `Read Next` to 3 files or areas.
- Show raw commands only on request or when you used non-default investigation.
