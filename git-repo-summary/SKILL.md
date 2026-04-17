---
summary: "Summarize a git repo by churn, bug hotspots, ownership, velocity, and firefighting signals."
read_when:
  - Auditing a repository quickly.
  - Deciding which files and team risks to inspect first.
---
# Git Repo Summary

Origin: adapted from https://piechowski.io/post/git-commands-before-reading-code/

Purpose: summarize a git repo fast by looking at churn, bug hotspots, ownership concentration, commit velocity, and revert/hotfix patterns.

Input:
- Optional repo path. Default: current directory.
- Optional window. Default: `1 year ago`.

Workflow:
1. Confirm target is a git repo. If not, stop and say so.
2. Run these commands in the target repo.

```bash
WINDOW="${WINDOW:-1 year ago}"

git log --format=format: --name-only --since="$WINDOW" | sort | uniq -c | sort -nr | head -20

git shortlog -sn --no-merges

git shortlog -sn --no-merges --since="6 months ago"

git log -i -E --grep="fix|bug|broken" --name-only --format='' | sort | uniq -c | sort -nr | head -20

git log -i -E --grep="fix|bug|broken" --since="$WINDOW" --name-only --format='' | sort | uniq -c | sort -nr | head -20

git log --format='%ad' --date=format:'%Y-%m' | sort | uniq -c

git log --oneline --since="$WINDOW" | grep -iE 'revert|hotfix|emergency|rollback' || true
```

3. For each of the top 5 churn files, also run:

```bash
FILE="path/to/file"

git log --since="$WINDOW" --format='%an' -- "$FILE" | sort | uniq -c | sort -nr | head -10
```

4. For each of the top 5 churn files, check for likely paired tests. Use existing repo conventions first. If unclear, try common patterns:

```bash
FILE="path/to/file"
BASENAME="$(basename "$FILE")"
STEM="${BASENAME%.*}"

rg -n --glob '*test*' --glob '*spec*' --glob '*Test*' --glob '*Spec*' "$STEM" .
git log --since="$WINDOW" --name-only --format='' -- "$FILE"
```

Interpretation:
- `Git repo summary`: use these sections together to build a fast risk and maintenance summary of the repo.
- `What changes the most`: top 20 files by churn in the last year.
- Call out the top 5. Treat files with both high churn and obvious ownership fear as likely drag, not automatically bad design.
- `Who built this`: rank contributors by commit count.
- Flag bus factor risk if one contributor is roughly 60%+ of commits.
- Compare all-time shortlog vs 6-month shortlog. If the historical top contributor is missing from recent activity, flag it.
- Note if many historical contributors exist but only a few are active recently.
- `Where bugs cluster`: compare bug-keyword hotspot files against churn hotspots.
- Files on both lists are highest-risk: frequently changed and frequently fixed.
- `Recent breakage only`: compare the `$WINDOW` bug-hotspot list against the all-time bug-hotspot list.
- If a file is hot in both recent bugs and recent churn, raise it above files that are only historically noisy.
- `Ownership per hotspot`: for each top churn file, identify who touched it most in the last year.
- If one file has many editors with no clear owner, call out shared-ownership risk.
- If one person dominates a hotspot file, call out key-person risk.
- `Test pairing`: check whether hotspot files have obvious nearby tests and whether those tests also changed during the window.
- If hotspot app code changes repeatedly without test churn, flag weak regression coverage.
- `Is this project accelerating or dying`: scan monthly commit counts for sustained decline, sudden drops, batch-release spikes, or a steady cadence.
- `How often is the team firefighting`: count and quote notable `revert`, `hotfix`, `emergency`, or `rollback` commits from the last year.

Caveats:
- High churn can mean active development, not dysfunction.
- Bug hotspot output depends on commit message quality.
- Squash-merge workflows can distort authorship; say that explicitly if commit history suggests it.
- Missing firefight keywords can mean weak commit messages, not necessarily stability.

Output:
1. `Summary`
   - 3 to 6 bullets: overall health, biggest risk, bus factor, momentum, deploy stability.
2. `Top Risk Files`
   - Table: `file | churn rank | bug rank | why it matters`
   - Focus on the top 5 churn files, especially overlap with bug hotspots.
   - Add `recent bug rank`, `top owner`, and `test pairing` columns when possible.
3. `Team Signals`
   - Top contributors overall.
   - Top contributors in last 6 months.
   - Bus factor / maintainer turnover notes.
   - For each top risk file, note whether ownership is concentrated or diffuse.
4. `Velocity`
   - Short read on commit trend by month.
5. `Firefighting`
   - Count of revert/hotfix-style commits in the window.
   - Quote a few representative commit subjects.
6. `Read Next`
   - Recommend the first 3 files or areas to inspect next and why.

Rules:
- Show the exact commands used.
- Include concrete numbers, not vague claims.
- Prefer short, direct bullets.
- If a section has weak signal because history is sparse or commit messages are poor, say that plainly.
