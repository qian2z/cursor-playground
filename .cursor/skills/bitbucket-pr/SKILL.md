---
name: bitbucket-pr
description: Fetches and parses a Bitbucket pull request — including its diff, file list, description, and metadata — to prepare context for a code review. Use this skill at the start of any Bitbucket PR review workflow.
---

# Bitbucket PR Skill

This skill retrieves a Bitbucket pull request from the internal Bitbucket Server / Data Center instance (configured via `$BITBUCKET_BASE_URL`) and prepares all information needed for a code review. It uses the `bbpr.py` helper script located at `.cursor/skills/bitbucket-pr/scripts/bbpr.py`.

## Prerequisites

The following Cursor Secrets must be configured (Cursor Dashboard → Cloud Agents → Secrets):

| Variable | Description |
|---|---|
| `BITBUCKET_BASE_URL` | Base URL of the Bitbucket Server instance (e.g. the Experian internal Bitbucket at `code.experian.local`) |
| `BITBUCKET_TOKEN` | Personal Access Token (PAT) with repository-read and pull-request-read scope |

> `BITBUCKET_USERNAME` is **not** required. The script authenticates using a Bearer token (`Authorization: Bearer <BITBUCKET_TOKEN>`).

## Understanding Project Key and Repository Slug

Every Bitbucket Server URL follows this pattern:

```
$BITBUCKET_BASE_URL/projects/{PROJECT_KEY}/repos/{REPO_SLUG}/pull-requests/{PR_ID}/overview
```

**Example URL** (using the Experian Bitbucket host):

```
$BITBUCKET_BASE_URL/projects/DASA/repos/powercurve/pull-requests/22170/overview
```

Concretely this looks like: `<host>/projects/DASA/repos/powercurve/pull-requests/22170/overview` where the host is your `BITBUCKET_BASE_URL`.

Breaking this down:

| URL segment | Value | Meaning |
|---|---|---|
| `projects/DASA` | `DASA` | **Project key** — the short, uppercase identifier for the Bitbucket project |
| `repos/powercurve` | `powercurve` | **Repository slug** — the repository name exactly as it appears in the URL |
| `pull-requests/22170` | `22170` | **PR ID** |

So for the URL above: `--project DASA --repo powercurve --pr 22170`.

The script can **auto-detect** the project key and repo slug from the git remote URL when the remote points to `code.experian.local`. It also auto-detects the current branch.

## When to Use

- Use this skill at the beginning of every Bitbucket PR review session.
- Invoke with `/bitbucket-pr` or ask "review Bitbucket PR #\<number\> in \<PROJECT_KEY\>/\<repo-slug\>".
- Always run this skill before calling any reviewer subagent.

## Instructions

1. **Collect** (or read from context):
   - The Bitbucket **project key** (e.g. `DASA`) — found between `/projects/` and `/repos/` in the PR URL
   - The **repository slug** (e.g. `powercurve`) — found between `/repos/` and `/pull-requests/` in the PR URL
   - The **pull request ID** (e.g. `22170`)

2. **Run the script to fetch PR metadata:**
   ```bash
   python3 .cursor/skills/bitbucket-pr/scripts/bbpr.py get \
     --project DASA \
     --repo powercurve \
     --pr 22170
   ```
   This calls:
   ```
   GET $BITBUCKET_BASE_URL/rest/api/1.0/projects/{projectKey}/repos/{repoSlug}/pull-requests/{prId}
   ```

3. **Fetch the PR diff:**
   ```bash
   python3 .cursor/skills/bitbucket-pr/scripts/bbpr.py diff \
     --project DASA \
     --repo powercurve \
     --pr 22170 \
     --context-lines 10
   ```
   This calls:
   ```
   GET $BITBUCKET_BASE_URL/rest/api/1.0/projects/{projectKey}/repos/{repoSlug}/pull-requests/{prId}/diff?contextLines=10
   ```

4. **Fetch existing reviewer comments** (to avoid duplicating known feedback):
   ```bash
   python3 .cursor/skills/bitbucket-pr/scripts/bbpr.py comments \
     --project DASA \
     --repo powercurve \
     --pr 22170
   ```
   Use `--unresolved` to show only open, unresolved threads. Use `--raw` for JSON output.

5. **Summarize the PR context** in a structured block before proceeding with review:
   ```
   ## PR Context
   - PR Title: <title>
   - Author: <author>
   - Source Branch: <source> → Target Branch: <target>
   - Description: <description>
   - Changed Files (<count>):
     - <file1> (+<additions> -<deletions>)
     - <file2> ...
   - Existing Comments: <count> (summarize key unresolved ones)
   ```

6. **Pass the diff and metadata** to the `java-code-reviewer` subagent or begin applying review rules directly.

## All Available Script Commands

All commands accept `--project` and `--repo` (both auto-detected from the git remote when inside a repo on the Experian Bitbucket instance).

| Command | Purpose | Key flags |
|---|---|---|
| `get` | Fetch PR metadata as JSON | `--pr <id>` |
| `diff` | Print unified diff of the PR | `--pr <id>`, `--context-lines <n>` (default 10) |
| `comments` | List all comments/activities | `--pr <id>`, `--unresolved`, `--raw` |
| `reply` | Post a reply to an existing comment thread | `--pr <id>`, `--comment-id <id>`, `--text <text>` |
| `create` | Open a new pull request | `--title <t>`, `--from <branch>`, `--to <branch>` (default `main`), `--description`, `--description-file`, `--reviewer`, `--no-default-reviewers` |
| `list` | List PRs in a repo | `--state OPEN\|MERGED\|DECLINED` (default `OPEN`) |
| `add-reviewer` | Add reviewer(s) to an existing PR | `--pr <id>`, `--reviewer <username>` (repeatable) |
| `approve` | Approve a PR | `--pr <id>` |
| `unapprove` | Remove your approval | `--pr <id>` |
| `merge` | Merge a PR | `--pr <id>` |
| `decline` | Decline a PR | `--pr <id>` |

### Example — create a PR with auto-detected project/repo

```bash
python3 .cursor/skills/bitbucket-pr/scripts/bbpr.py create \
  --title "feat: add payment retry logic" \
  --to main
```

### Example — create a PR with explicit project/repo

```bash
python3 .cursor/skills/bitbucket-pr/scripts/bbpr.py create \
  --project DASA \
  --repo powercurve \
  --from feature/my-branch \
  --to main \
  --title "feat: add payment retry logic" \
  --description-file pr_description.md
```

## Posting Review Comments (Optional)

To post inline comments back to Bitbucket after the review, use the `reply` command for threaded responses, or call the REST API directly:

```
POST $BITBUCKET_BASE_URL/rest/api/1.0/projects/{projectKey}/repos/{repoSlug}/pull-requests/{prId}/comments
Authorization: Bearer {BITBUCKET_TOKEN}
Content-Type: application/json

{
  "text": "<comment text>",
  "anchor": {
    "line": <line number>,
    "lineType": "ADDED",
    "fileType": "TO",
    "path": "<file path>"
  }
}
```

Only post comments for `[BLOCKER]` and `[CRITICAL]` findings by default. Ask the user if they want `[MAJOR]` findings posted as well.

## Error Handling

- **401/403** — Check that `BITBUCKET_TOKEN` is set correctly and has repository-read + PR-read permissions.
- **404** — Confirm the project key, repo slug, and PR ID. The project key is always uppercase (e.g. `DASA`). The repo slug matches the URL exactly (e.g. `powercurve`).
- **Large diff (>500 changed files)** — Ask the user to specify which files or packages to focus on.
