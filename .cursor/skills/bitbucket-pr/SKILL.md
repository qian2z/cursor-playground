---
name: bitbucket-pr
description: Fetches and parses a Bitbucket pull request — including its diff, file list, description, and metadata — to prepare context for a code review. Use this skill at the start of any Bitbucket PR review workflow.
---

# Bitbucket PR Skill

This skill retrieves a Bitbucket pull request and prepares all information needed for a code review.

## Prerequisites

The following environment variables must be set (add them as Cursor Secrets):

| Variable | Description |
|---|---|
| `BITBUCKET_BASE_URL` | Base URL of your Bitbucket instance (e.g. `https://bitbucket.example.com` for Server/Data Center, or `https://api.bitbucket.org/2.0` for Cloud) |
| `BITBUCKET_USERNAME` | Your Bitbucket username or service account |
| `BITBUCKET_TOKEN` | Bitbucket personal access token (PAT) or app password with repository read + PR read scope |

## When to Use

- Use this skill at the beginning of every Bitbucket PR review session.
- Invoke with `/bitbucket-pr` or ask "review Bitbucket PR #<number> in <project>/<repo>".
- Always run this skill before calling any reviewer subagent.

## Instructions

1. **Ask the user** (or read from context) for:
   - The Bitbucket project key (e.g. `PROJ`)
   - The repository slug (e.g. `my-service`)
   - The pull request ID (e.g. `42`)

2. **Fetch PR metadata** using the Bitbucket REST API:
   ```
   GET {BITBUCKET_BASE_URL}/rest/api/1.0/projects/{projectKey}/repos/{repoSlug}/pull-requests/{prId}
   ```
   For Bitbucket Cloud:
   ```
   GET {BITBUCKET_BASE_URL}/repositories/{workspace}/{repoSlug}/pullrequests/{prId}
   ```
   Headers: `Authorization: Bearer {BITBUCKET_TOKEN}` (Server) or `Basic {base64(user:token)}` (Cloud)

3. **Fetch the PR diff**:
   ```
   GET {BITBUCKET_BASE_URL}/rest/api/1.0/projects/{projectKey}/repos/{repoSlug}/pull-requests/{prId}/diff
   ```
   For Bitbucket Cloud:
   ```
   GET {BITBUCKET_BASE_URL}/repositories/{workspace}/{repoSlug}/pullrequests/{prId}/diff
   ```

4. **Fetch the changed file list**:
   ```
   GET {BITBUCKET_BASE_URL}/rest/api/1.0/projects/{projectKey}/repos/{repoSlug}/pull-requests/{prId}/changes
   ```

5. **Fetch existing reviewer comments** (to avoid duplicating known feedback):
   ```
   GET {BITBUCKET_BASE_URL}/rest/api/1.0/projects/{projectKey}/repos/{repoSlug}/pull-requests/{prId}/activities
   ```

6. **Summarize the PR context** in a structured block:
   ```
   ## PR Context
   - PR Title: <title>
   - Author: <author>
   - Source Branch: <source> → Target Branch: <target>
   - Description: <description>
   - Changed Files (<count>):
     - <file1> (+<additions> -<deletions>)
     - <file2> ...
   - Existing Comments: <count> (summarize key ones)
   ```

7. **Pass the diff and metadata** to the `java-code-reviewer` subagent or instruct the agent to begin applying the review rules.

## Posting Review Comments (Optional)

To post inline comments back to Bitbucket after the review:

```
POST {BITBUCKET_BASE_URL}/rest/api/1.0/projects/{projectKey}/repos/{repoSlug}/pull-requests/{prId}/comments
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

- If credentials fail (401/403), prompt the user to check `BITBUCKET_TOKEN` and repository permissions.
- If the PR is not found (404), confirm the project key, repo slug, and PR ID with the user.
- If the diff is too large (>500 changed files), ask the user to specify which files or packages to focus on.
