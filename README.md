# Bitbucket Java PR Review Agent

A complete Cursor agent setup for automated Java code review of Bitbucket pull requests. This repository contains all rules, skills, and subagents needed to conduct thorough, multi-dimensional Java code reviews covering MVC architecture, OSGi services, Effective Java principles, and SonarQube quality gates.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                  Cursor Agent (parent)                   │
│                                                         │
│  Skills (one-shot, invoked on demand):                  │
│  ┌──────────────┐  ┌─────────────┐  ┌───────────────┐  │
│  │ bitbucket-pr │  │ java-review │  │ sonarqube-java│  │
│  └──────────────┘  └─────────────┘  └───────────────┘  │
│  ┌──────────────┐  ┌─────────────┐  ┌───────────────┐  │
│  │effective-java│  │ osgi-review │  │  mvc-review   │  │
│  └──────────────┘  └─────────────┘  └───────────────┘  │
│                                                         │
│  Subagents (isolated context, parallelizable):          │
│  ┌──────────────────────┐  ┌───────────────────────┐   │
│  │  java-code-reviewer  │  │    security-scanner   │   │
│  │  (orchestrator)      │  │    (BLOCKER hunter)   │   │
│  └──────────────────────┘  └───────────────────────┘   │
│  ┌──────────────────────┐  ┌───────────────────────┐   │
│  │     osgi-reviewer    │  │     mvc-reviewer      │   │
│  └──────────────────────┘  └───────────────────────┘   │
│  ┌──────────────────────┐                               │
│  │    review-verifier   │                               │
│  └──────────────────────┘                               │
│                                                         │
│  Rules (always-on context for .java files):             │
│  - java-code-standards.mdc                              │
│  - effective-java-principles.mdc                        │
│  - sonarqube-java.mdc                                   │
│  - osgi-services.mdc                                    │
│  - mvc-patterns.mdc                                     │
│  - pr-review-process.mdc                                │
└─────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
.cursor/
├── rules/                          # MDC rules — applied as context for .java files
│   ├── java-code-standards.mdc     # Core Java naming, structure, error handling
│   ├── effective-java-principles.mdc  # All 90 items from Effective Java (Bloch)
│   ├── sonarqube-java.mdc          # SonarQube bugs, vulnerabilities, code smells
│   ├── osgi-services.mdc           # OSGi DS annotations, lifecycle, bundle hygiene
│   ├── mvc-patterns.mdc            # MVC layer rules, controller/service/repo design
│   └── pr-review-process.mdc       # Review process, severity labels, output format
│
├── agents/                         # Subagents — specialized AI agents with isolated context
│   ├── java-code-reviewer.md       # Primary orchestrator — runs full review pipeline
│   ├── security-scanner.md         # Security vulnerability specialist (OWASP, CWE)
│   ├── osgi-reviewer.md            # OSGi component specialist
│   ├── mvc-reviewer.md             # MVC architecture specialist
│   └── review-verifier.md          # QA agent — validates review completeness
│
└── skills/                         # Skills — on-demand procedural knowledge packages
    ├── bitbucket-pr/               # Fetch PR diff and metadata from Bitbucket API
    │   └── SKILL.md
    ├── java-review/                # Full Java review checklist (all dimensions)
    │   └── SKILL.md
    ├── sonarqube-java/             # Focused SonarQube static analysis pass
    │   └── SKILL.md
    ├── effective-java/             # Focused Effective Java items review
    │   └── SKILL.md
    ├── osgi-review/                # Focused OSGi component review
    │   └── SKILL.md
    └── mvc-review/                 # Focused MVC architecture review
        └── SKILL.md
```

---

## Setup

### 1. Prerequisites

- **Cursor** version 2.4 or later (subagents and skills require 2.4+)
- A Bitbucket account (Cloud or Server/Data Center)
- A Bitbucket personal access token (PAT) with **repository read** and **PR read** scopes

### 2. Add Secrets to Cursor

Go to **Cursor Dashboard → Cloud Agents → Secrets** and add:

| Secret Name | Value |
|---|---|
| `BITBUCKET_BASE_URL` | Your Bitbucket base URL (see below) |
| `BITBUCKET_USERNAME` | Your Bitbucket username or service account |
| `BITBUCKET_TOKEN` | Your Bitbucket PAT / app password |

**Base URL by deployment type:**
- Bitbucket Server / Data Center: `https://bitbucket.yourcompany.com`
- Bitbucket Cloud: `https://api.bitbucket.org/2.0`

### 3. Clone This Repository

```bash
git clone https://github.com/qian2z/cursor-playground.git
cd cursor-playground
```

Open the directory in Cursor. The rules, skills, and subagents will be automatically discovered.

### 4. Verify Setup

In Cursor Agent chat, run:
```
/bitbucket-pr
```
You should see the skill description appear. If you see no skills, go to **Cursor Settings → Rules** to confirm skills are loaded from `.cursor/skills/`.

---

## Usage

### Basic: Review a Bitbucket PR

In Cursor Agent chat:
```
Review Bitbucket PR #42 in project MYPROJ, repository my-java-service
```

Or using the skill directly:
```
/bitbucket-pr
```
The agent will ask for the project key, repository slug, and PR ID, then fetch the diff and start the full review.

### Full Review Pipeline (Automatic)

When you ask the agent to review a PR, it will:

1. **`bitbucket-pr` skill** — Fetch PR metadata and diff from Bitbucket API
2. **`java-code-reviewer` subagent** — Orchestrate the full review
3. **Parallel subagents** (for large PRs):
   - `security-scanner` — Scan for OWASP/CWE vulnerabilities
   - `osgi-reviewer` — Check `@Component` classes
   - `mvc-reviewer` — Check controllers/services/repositories
4. **`review-verifier` subagent** — Validate review completeness
5. Aggregate and output the final report with recommendation
6. **Post inline comments** — All `[BLOCKER]`, `[CRITICAL]`, and `[MAJOR]` findings are automatically posted as inline comments anchored to the exact file and line in the Bitbucket PR

### Focused Reviews (Skills)

For targeted analysis, invoke skills directly:

| Command | What it does |
|---|---|
| `/bitbucket-pr` | Fetch PR context from Bitbucket |
| `/java-review` | Full Java review on current files |
| `/sonarqube-java` | SonarQube-focused static analysis |
| `/effective-java` | Effective Java items deep dive |
| `/osgi-review` | OSGi component compliance check |
| `/mvc-review` | MVC layer architecture check |

### Posting Inline Comments Manually

You can also trigger inline comment posting at any time:

```
Post the review findings for PR #42 as inline comments on the PR
```

Or post a specific finding directly:

```
Post the BLOCKER findings from the last review as inline comments on PR #42 in MYPROJ/my-java-service
```

### Explicit Subagent Invocation

```
/java-code-reviewer review the diff I just pasted
/security-scanner scan OrderController.java for vulnerabilities
/osgi-reviewer check UserServiceImpl.java
/review-verifier verify this review report
```

---

## Review Dimensions

Every PR review covers these 9 dimensions:

| Dimension | Rules Applied | Subagent |
|---|---|---|
| Architecture & Design | `mvc-patterns.mdc` | `mvc-reviewer` |
| Security | `sonarqube-java.mdc` | `security-scanner` |
| Bugs & Correctness | `java-code-standards.mdc`, `sonarqube-java.mdc` | `java-code-reviewer` |
| OSGi Services | `osgi-services.mdc` | `osgi-reviewer` |
| MVC Architecture | `mvc-patterns.mdc` | `mvc-reviewer` |
| Effective Java | `effective-java-principles.mdc` | `java-code-reviewer` |
| SonarQube | `sonarqube-java.mdc` | `java-code-reviewer` |
| Test Quality | `java-code-standards.mdc` | `java-code-reviewer` |
| Performance | `java-code-standards.mdc` | `java-code-reviewer` |

---

## Severity Scale

| Label | Meaning | Action |
|---|---|---|
| `[BLOCKER]` | Bug, security vulnerability, data loss, OSGi contract violation | Must fix before merge |
| `[CRITICAL]` | Core design rule violation | Should fix before merge |
| `[MAJOR]` | Significant code smell, Effective Java violation | Fix strongly recommended |
| `[MINOR]` | Style, naming, optional improvement | At author's discretion |
| `[INFO]` | Positive feedback, informational note | No action required |

### Recommendation Logic

| Condition | Recommendation |
|---|---|
| No BLOCKERs, no CRITICALs, ≤3 MAJORs | **APPROVE** |
| Any BLOCKER, or >1 CRITICAL | **REQUEST CHANGES** |
| Clarification needed | **COMMENT** |

---

## Rules Reference

### `java-code-standards.mdc`
Applied to all `*.java` files. Covers:
- Naming conventions (classes, methods, variables, constants)
- Class and method structure
- Error handling and exception design
- Immutability and null handling
- Generics, collections, thread safety

### `effective-java-principles.mdc`
Applied to all `*.java` files. Covers all 90 items from *Effective Java* (Bloch, 3rd ed.), grouped by chapter.

### `sonarqube-java.mdc`
Applied to all `*.java` files. Covers:
- Bugs: null dereferences, resource leaks, equals/hashCode, wait/notify
- Vulnerabilities: SQL/command/XML injection, hardcoded credentials, weak crypto
- Code smells: cognitive complexity, dead code, duplicate strings, empty catch blocks
- Security hotspots: sensitive data in logs, reflection, cookie flags

### `osgi-services.mdc`
Applied to all `*.java` files. Covers:
- `@Component`, `@Reference`, `@Activate`, `@Deactivate`, `@Modified` usage
- Cardinality, policy, and dynamic reference patterns
- Bundle hygiene (exports, imports, no Require-Bundle)
- Lifecycle thread safety

### `mvc-patterns.mdc`
Applied to all `*.java` files. Covers:
- Strict layer boundary enforcement
- Controller design (stateless, no business logic, correct HTTP codes)
- Service layer (transactions, business logic ownership)
- Repository layer (parameterized queries, pagination)
- DTO design and mapping
- Constructor injection only

### `pr-review-process.mdc`
Review process governance:
- 9 review dimensions and order
- Severity label definitions
- Finding format template
- Approval criteria
- Review Summary format

---

## Extending the Setup

### Adding a New Rule
Create a new `.mdc` file in `.cursor/rules/`:
```
---
description: <when this rule applies>
globs: "**/*.java"
alwaysApply: false
---

# Rule Title
...
```

### Adding a New Skill
Create a folder in `.cursor/skills/` with a `SKILL.md`:
```
.cursor/skills/my-skill/SKILL.md
```
The folder name must match the `name` field in the frontmatter.

### Adding a New Subagent
Create a `.md` file in `.cursor/agents/`:
```
.cursor/agents/my-specialist.md
```
Include YAML frontmatter with `name`, `description`, and optionally `model` and `readonly`.

---

## Inline Comment Posting & Agent Signature

Every finding posted by the agent as an inline Bitbucket PR comment carries a machine-generated signature:

```
---
*Posted by Cursor AI Review Agent*
```

This is appended **automatically** by the `bbpr.py comment` script — you do not need to add it manually. It lets human reviewers instantly distinguish agent-generated feedback from human review comments.

### What Gets Posted Automatically

| Severity | Posted by default? |
|---|---|
| `[BLOCKER]` | Always |
| `[CRITICAL]` | Always |
| `[MAJOR]` | Always |
| `[MINOR]` | Only when explicitly requested |
| `[INFO]` | Only when explicitly requested |

### bbpr.py `comment` Command

```bash
python3 .cursor/skills/bitbucket-pr/scripts/bbpr.py comment \
  --project MYPROJ \
  --repo my-java-service \
  --pr 42 \
  --file "src/main/java/com/example/OrderService.java" \
  --line 87 \
  --line-type ADDED \
  --severity NORMAL \
  --text "[CRITICAL] OrderService.java:87 — SQL injection risk via string concatenation

Problem: ...
Suggested: ...
Behaviour Impact: ...
Reference: SonarQube S2077"
```

**Options:**

| Flag | Description | Default |
|---|---|---|
| `--file` | Relative path of the file to anchor the comment to | (general comment if omitted) |
| `--line` | Line number in the diff to anchor the comment to | (general comment if omitted) |
| `--line-type` | `ADDED`, `REMOVED`, or `CONTEXT` | `ADDED` |
| `--file-type` | `TO` (new file) or `FROM` (old file) | `TO` |
| `--severity` | `NORMAL` or `BLOCKER` | `NORMAL` |

---

## Bitbucket API Reference

### Bitbucket Server / Data Center (REST API 1.0)
```
GET  /rest/api/1.0/projects/{projectKey}/repos/{repoSlug}/pull-requests/{prId}
GET  /rest/api/1.0/projects/{projectKey}/repos/{repoSlug}/pull-requests/{prId}/diff
GET  /rest/api/1.0/projects/{projectKey}/repos/{repoSlug}/pull-requests/{prId}/changes
POST /rest/api/1.0/projects/{projectKey}/repos/{repoSlug}/pull-requests/{prId}/comments
```

### Bitbucket Cloud (REST API 2.0)
```
GET  /2.0/repositories/{workspace}/{repoSlug}/pullrequests/{prId}
GET  /2.0/repositories/{workspace}/{repoSlug}/pullrequests/{prId}/diff
POST /2.0/repositories/{workspace}/{repoSlug}/pullrequests/{prId}/comments
```

Authentication:
- Server/Data Center: `Authorization: Bearer <PAT>`
- Cloud: `Authorization: Basic <base64(username:app_password)>`

---

## FAQ

**Q: The bitbucket-pr skill returns a 401 error.**
A: Check that `BITBUCKET_TOKEN` is set correctly in Cursor Secrets and has `repository-read` and `pullrequest-read` permissions.

**Q: The skills are not showing up in the `/` menu.**
A: Confirm Cursor version 2.4+. Check Settings → Rules to see if skills are discovered. Ensure each skill folder name matches the `name` field in its `SKILL.md` frontmatter.

**Q: The review is too slow for large PRs.**
A: The `java-code-reviewer` subagent automatically launches parallel subagents for PRs with >10 changed files. For very large PRs, ask the agent to focus on specific packages or files.

**Q: Can I use this without Bitbucket (e.g., with GitHub)?**
A: The `java-review`, `sonarqube-java`, `effective-java`, `osgi-review`, and `mvc-review` skills work on any Java code. Only `bitbucket-pr` is Bitbucket-specific. You can adapt it to GitHub by changing the API endpoints.

**Q: Does the agent post comments back to Bitbucket automatically?**
A: Yes. After completing the review, the agent automatically posts all `[BLOCKER]`, `[CRITICAL]`, and `[MAJOR]` findings as inline comments anchored to the exact file and line in the PR. Each comment is signed with `--- *Posted by Cursor AI Review Agent*` so human reviewers can distinguish agent feedback from human comments. `[MINOR]` and `[INFO]` findings are only posted when you explicitly request it.

**Q: How are agent-posted comments identified?**
A: Every comment posted by the agent ends with the signature `--- *Posted by Cursor AI Review Agent*`. This is appended automatically by the `bbpr.py comment` script and cannot be missed or accidentally omitted.

**Q: Can I post comments for only specific severities?**
A: Yes. Ask the agent: "Post only the BLOCKER findings as inline comments on PR #42" or "Post all findings including MINOR on PR #42."
