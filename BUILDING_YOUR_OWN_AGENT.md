# How to Build Your Own Cursor Agent

A step-by-step guide for building a Cursor AI agent from scratch, based on how this repository is structured.

---

## How Cursor Agents Work — The Three Building Blocks

Before diving into the steps, it helps to understand how Cursor composes agent behaviour:

| Building block | File location | What it does |
|---|---|---|
| **Rules** (`.mdc`) | `.cursor/rules/` | Passive context injected into the agent's prompt. Applied automatically based on `globs` patterns (e.g. all `*.java` files) or when `alwaysApply: true`. Think of them as standing instructions the agent always follows. |
| **Skills** (`SKILL.md`) | `.cursor/skills/<skill-name>/` | On-demand procedural instructions the agent reads and executes when invoked via `/skill-name` or when described in a prompt. A skill folder may also contain helper scripts (e.g. a Python script that calls an external API). |
| **Subagents** (`.md`) | `.cursor/agents/` | Specialist agents with their own isolated context that the parent agent can delegate work to. They can run in parallel, use a lighter model, or be restricted to read-only operations. |

```
.cursor/
├── rules/                    ← always-on context for matched file types
│   └── my-rule.mdc
├── skills/                   ← on-demand procedural knowledge + helper scripts
│   └── my-skill/
│       ├── SKILL.md
│       └── scripts/
│           └── my_helper.py
└── agents/                   ← specialist subagents with isolated context
    └── my-specialist.md
```

For **GitHub Copilot** the equivalent layout uses `.github/` instead of `.cursor/`, and the file extensions differ slightly, but the same conceptual split — rules, skills/prompts, agents — applies.

---

## Step 1 — Define Your Use Case and Identify Required External Access

Start by answering: _What should my agent do, and what systems does it need to talk to?_

Every external system your agent needs to read from or write to will become either:
- A **skill** (instructions + a helper script that calls the API), or
- A **secret** injected as an environment variable

**Examples:**
- Code review agent on Bitbucket → needs a `bitbucket-pr` skill with a Python script calling the Bitbucket REST API, plus `BITBUCKET_BASE_URL` and `BITBUCKET_TOKEN` secrets.
- Documentation assistant on Confluence → needs a Confluence skill + a `CONFLUENCE_BASE_URL` / `CONFLUENCE_TOKEN` secret.
- Ticket triage agent on Jira → needs a Jira skill + `JIRA_BASE_URL` / `JIRA_TOKEN` secret.

Write down the full list before writing a single file — it becomes your roadmap.

---

## Step 2 — Find or Create Helper Scripts for External Access

Your skill's `SKILL.md` tells the agent _what_ to do; a helper script does the actual API call.

**Option A — Reuse an existing script**

Check if a ready-made script already exists for your target system:
- Community or internal app stores (e.g. `https://cursor-appstore.hb-cicd-test.experianone.io/`)
- The `scripts/` folder inside existing skill directories in this repo (see `.cursor/skills/bitbucket-pr/scripts/bbpr.py` for a reference implementation)

Read the script briefly and locate where credentials are consumed — they are typically read from environment variables (`os.environ["MY_TOKEN"]`). Match those variable names when you create your Cursor secrets.

**Option B — Generate a new script with AI**

If no script exists, describe what you need in plain language and let the LLM generate it for you:

```
Write a Python CLI script that:
- Reads JIRA_BASE_URL and JIRA_TOKEN from environment variables
- Accepts --project, --issue, and --action as CLI flags
- Supports actions: get (fetch issue JSON), comment (post a comment), transition (move status)
- Authenticates with Bearer token
- Prints results to stdout as JSON
```

Iterate with the LLM until the script handles authentication, pagination, and error codes correctly. You do not need to start from scratch — paste a similar existing script and ask the LLM to adapt it.

---

## Step 3 — Add Secrets to Cursor

Go to **Cursor Dashboard → Cloud Agents → Secrets** and add the environment variables your helper scripts expect.

| Secret type | Scope |
|---|---|
| User-scoped | Available to all your agents across all repos |
| Team-scoped | Shared with all team members |
| Repo-scoped | Only available when working in that specific repository |

User secrets override team secrets when both are set. For sensitive tokens (PATs, API keys) always use secrets — never hardcode credentials in script files.

After adding secrets, they are automatically injected as environment variables when Cursor runs your agent. No code change is needed to pick them up.

---

## Step 4 — Create the Directory Structure and Let the LLM Do the Heavy Lifting

Start a new Cursor Agent conversation and give it a thorough description:

```
I want to build a Cursor agent that reviews Jira tickets for completeness before a sprint starts.

Use case:
- Fetch a Jira ticket by ID
- Check that the ticket has: title, description, acceptance criteria, story points, and an assignee
- Flag any missing fields as [BLOCKER], [MAJOR], or [MINOR]
- Post a comment back to the Jira ticket summarising the findings

External access needed:
- Jira Cloud REST API
- Secrets: JIRA_BASE_URL, JIRA_TOKEN

Please create the full .cursor/ directory structure including:
- A skill (SKILL.md + helper Python script) for fetching and commenting on Jira tickets
- A rule (.mdc) defining the completeness checklist and severity labels
- A subagent (.md) that orchestrates the review logic
```

The LLM will generate the skeleton. Your job at this point is to review the structure — not every word — and check that:
- Each `SKILL.md` has a frontmatter `name:` that matches its folder name exactly (Cursor uses this to register the `/skill-name` command)
- Each subagent `.md` has YAML frontmatter with at least `name:` and `description:`
- Each rule `.mdc` has frontmatter with `description:`, `alwaysApply:`, and optionally `globs:`

---

## Step 5 — Understand the File Formats

### Rule (`.mdc`)

```
---
description: What this rule does and when it applies.
alwaysApply: false
globs: "**/*.java"        ← omit if not file-type-specific
---

# Rule Title

## Section
- Checklist item or instruction
```

- `globs` causes the rule to be injected automatically when the agent opens a matching file.
- `alwaysApply: true` injects it into every conversation regardless of file type.
- Rules are **passive**: the agent reads them as standing instructions; they do not invoke any scripts.

### Skill (`SKILL.md`)

```
---
name: my-skill            ← must match the folder name exactly
description: One-line description shown in the / command menu.
---

# Skill Title

## Prerequisites
List any required secrets or tools.

## Instructions
Step-by-step instructions the agent will follow when this skill is invoked.
Include exact shell commands the agent should run, e.g.:

  python3 .cursor/skills/my-skill/scripts/helper.py get --id 123
```

- Invoked with `/my-skill` in Agent chat, or automatically when a rule or subagent mentions the skill name.
- The agent reads the `SKILL.md` and then **executes** the steps — including running shell commands.
- Helper scripts live alongside `SKILL.md` in the same folder (e.g. `scripts/helper.py`).

### Subagent (`.md`)

```
---
name: my-specialist
description: Short description so the parent agent knows when to delegate here.
model: inherit            ← or "fast" for lightweight tasks
readonly: false           ← set true to prevent the agent from writing files or running commands
---

You are a specialist in ...

## Instructions
What this agent does and how it structures its output.
```

- Subagents have **isolated context** — they do not automatically share the parent's conversation history. You must pass relevant context explicitly when invoking them.
- They can run **in parallel** for large tasks (the parent launches multiple subagents simultaneously).
- Use `model: fast` for validation or summarisation tasks to reduce cost; use `model: inherit` for deep analysis.

---

## Step 6 — Iterate: Try, Review, Refine

1. **Try it**: In Cursor Agent chat, describe your use case and invoke the agent.
2. **Review the output**: Is the structure correct? Did it call the right scripts? Did the findings match your expectations?
3. **Refine with the LLM**: Paste the output back and ask the LLM to improve specific parts:
   - "The skill is calling the wrong API endpoint — update the script to use `/rest/api/2/issue/{id}`"
   - "The findings format is inconsistent — align it with the template in the rule file"
   - "The subagent is not posting comments back to Jira — add that step at the end of its instructions"
4. **Repeat** until you are satisfied.

You almost never need to manually edit the generated files character-by-character. Describe what is wrong in plain language and let the LLM fix it.

---

## Quick Reference — File Checklist

| What you need | File to create | Key requirement |
|---|---|---|
| Standing instructions for a file type | `.cursor/rules/my-rule.mdc` | `globs:` in frontmatter |
| Always-on instructions | `.cursor/rules/my-rule.mdc` | `alwaysApply: true` |
| On-demand procedural steps | `.cursor/skills/my-skill/SKILL.md` | `name:` matches folder name |
| External API helper | `.cursor/skills/my-skill/scripts/helper.py` | Reads credentials from env vars |
| Specialist agent | `.cursor/agents/my-specialist.md` | `name:` and `description:` in frontmatter |
| API credentials | Cursor Dashboard → Cloud Agents → Secrets | Never hardcode in files |

---

## Copilot vs Cursor — Directory Mapping

| Concept | Cursor path | GitHub Copilot path |
|---|---|---|
| Rules | `.cursor/rules/*.mdc` | `.github/copilot-instructions.md` (single file) |
| Skills | `.cursor/skills/<name>/SKILL.md` | `.github/prompts/*.prompt.md` |
| Subagents | `.cursor/agents/*.md` | `.github/agents/*.md` (if supported) |

The concepts are the same; only the paths and file extensions differ.

---

## Real-World Example from This Repository

This repository is a complete working example of the above pattern built for Bitbucket Java PR review:

| Component | File | Purpose |
|---|---|---|
| Skill | `.cursor/skills/bitbucket-pr/SKILL.md` | Fetches PR diff and metadata via `bbpr.py` |
| Helper script | `.cursor/skills/bitbucket-pr/scripts/bbpr.py` | Python CLI wrapping the Bitbucket REST API |
| Skill | `.cursor/skills/java-review/SKILL.md` | Full Java review checklist |
| Subagent | `.cursor/agents/java-code-reviewer.md` | Orchestrates the full review pipeline |
| Subagent | `.cursor/agents/security-scanner.md` | Specialist OWASP/CWE vulnerability scan |
| Subagent | `.cursor/agents/review-verifier.md` | Validates review completeness |
| Rule | `.cursor/rules/pr-review-process.mdc` | Severity labels, finding format, approval logic |
| Rule | `.cursor/rules/java-code-standards.mdc` | Java naming, structure, error handling |
| Secrets | Cursor Dashboard | `BITBUCKET_BASE_URL`, `BITBUCKET_TOKEN` |

Study this structure and adapt it to your own domain.
