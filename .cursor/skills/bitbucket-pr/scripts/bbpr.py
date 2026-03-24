#!/usr/bin/env python3

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))
import cursor_utils

BB_BASE_URL = "https://code.experian.local"


def get_token():
    config = cursor_utils.read_mcp_config()
    return cursor_utils.get_token(
        config,
        "bitbucket.headers.Authorization",
        "mcpServers.experian-mcp-bitbucket.headers.Authorization",
    )


def api_call(method, endpoint, data=None):
    url = f"{BB_BASE_URL}/rest/api/1.0{endpoint}"
    headers = cursor_utils.auth_header(get_token())
    return cursor_utils.api_request(method, url, headers=headers, data=data)


def detect_repo_info():
    try:
        remote_url = cursor_utils.run_git("remote", "get-url", "origin")
    except SystemExit:
        return None, None
    m = re.search(
        r"code\.experian\.local[:/]+[^/]+/([^/]+)/([^/.]+)(?:\.git)?$", remote_url
    )
    if m:
        return m.group(1), m.group(2)
    m = re.search(r"code\.experian\.local[:/]+([^/]+)/([^/.]+)(?:\.git)?$", remote_url)
    if m:
        return m.group(1), m.group(2)
    return None, None


def detect_branch():
    try:
        return cursor_utils.run_git("rev-parse", "--abbrev-ref", "HEAD")
    except SystemExit:
        return ""


def get_current_user():
    try:
        email = cursor_utils.run_git("config", "user.email")
        return email.split("@")[0] if "@" in email else email
    except SystemExit:
        return ""


def fetch_default_reviewers(project, repo, from_ref, to_ref):
    try:
        repo_info = api_call("GET", f"/projects/{project}/repos/{repo}")
        repo_id = repo_info.get("id")
        if not repo_id:
            return []
        url = (
            f"{BB_BASE_URL}/rest/default-reviewers/1.0/projects/{project}/repos/{repo}"
            f"/reviewers?sourceRepoId={repo_id}&targetRepoId={repo_id}"
            f"&sourceRefId={from_ref}&targetRefId={to_ref}"
        )
        headers = cursor_utils.auth_header(get_token())
        resp = cursor_utils.api_request("GET", url, headers=headers)
        if not isinstance(resp, list):
            return []
        me = get_current_user()
        return [
            {"user": {"name": r.get("name", r.get("slug", ""))}}
            for r in resp
            if r.get("slug") != me and r.get("name") != me
        ]
    except Exception:
        return []


def cmd_create(args):
    project = args.project or detected_project
    repo = args.repo or detected_repo
    from_branch = args.from_branch or detected_branch
    to_branch = args.to or "main"
    title = args.title
    description = args.description or ""
    if args.description_file:
        if not os.path.isfile(args.description_file):
            cursor_utils.die(f"Description file not found: {args.description_file}")
        with open(args.description_file, encoding="utf-8") as f:
            description = f.read()
    elif description:
        description = description.encode().decode("unicode_escape")

    if not project:
        cursor_utils.die("--project required (could not auto-detect)")
    if not repo:
        cursor_utils.die("--repo required (could not auto-detect)")
    if not from_branch:
        cursor_utils.die("--from required (not in a git repo?)")
    if not title:
        cursor_utils.die("--title is required")

    reviewers = []
    if not args.no_default_reviewers:
        cursor_utils.info("Fetching default reviewers...")
        reviewers = fetch_default_reviewers(
            project, repo, f"refs/heads/{from_branch}", f"refs/heads/{to_branch}"
        )
        cursor_utils.info(f"  Found {len(reviewers)} default reviewer(s)")
    for r in args.reviewer or []:
        reviewers.append({"user": {"name": r}})
    seen = set()
    unique = []
    for r in reviewers:
        name = r["user"]["name"]
        if name not in seen:
            seen.add(name)
            unique.append(r)
    reviewers = unique
    cursor_utils.info(f"  Total reviewers: {len(reviewers)}")

    payload = {
        "title": title,
        "description": description,
        "fromRef": {
            "id": f"refs/heads/{from_branch}",
            "repository": {"slug": repo, "project": {"key": project}},
        },
        "toRef": {
            "id": f"refs/heads/{to_branch}",
            "repository": {"slug": repo, "project": {"key": project}},
        },
        "reviewers": reviewers,
    }
    response = api_call(
        "POST", f"/projects/{project}/repos/{repo}/pull-requests", data=payload
    )
    pr_id = response.get("id")
    if pr_id:
        pr_url = response.get("links", {}).get("self", [{}])[0].get("href", "")
        state = response.get("state", "")
        print()
        print("Pull request created successfully!")
        print(f"  PR:        #{pr_id}")
        print(f"  Title:     {title}")
        print(f"  Branch:    {from_branch} -> {to_branch}")
        print(f"  State:     {state}")
        print(f"  Reviewers: {len(reviewers)}")
        print(f"  URL:       {pr_url}")
        print()
        print("Reviewers:")
        for r in response.get("reviewers", []):
            u = r.get("user", {})
            print(f"  - {u.get('displayName', '')} ({u.get('name', '')})")
    else:
        cursor_utils.die(f"Failed to create pull request\n{json.dumps(response, indent=2)}")


def cmd_list(args):
    project = args.project or detected_project
    repo = args.repo or detected_repo
    state = args.state or "OPEN"
    if not project:
        cursor_utils.die("--project required")
    if not repo:
        cursor_utils.die("--repo required")
    response = api_call(
        "GET", f"/projects/{project}/repos/{repo}/pull-requests?state={state}&limit=25"
    )
    values = response.get("values", [])
    count = response.get("size", len(values))
    print(f"Found {count} pull request(s) ({state}):")
    print()
    for pr in values:
        pr_id = pr.get("id", "")
        pr_state = pr.get("state", "")
        title = pr.get("title", "")
        from_ref = pr.get("fromRef", {}).get("displayId", "")
        to_ref = pr.get("toRef", {}).get("displayId", "")
        href = pr.get("links", {}).get("self", [{}])[0].get("href", "")
        print(f"  #{pr_id} [{pr_state}] {title}")
        print(f"       {from_ref} -> {to_ref}")
        print(f"       {href}")
        print()


def cmd_get(args):
    project = args.project or detected_project
    repo = args.repo or detected_repo
    pr_id = args.pr
    if not pr_id:
        cursor_utils.die("--pr is required")
    if not project:
        cursor_utils.die("--project required")
    if not repo:
        cursor_utils.die("--repo required")
    response = api_call("GET", f"/projects/{project}/repos/{repo}/pull-requests/{pr_id}")
    author = response.get("author", {}).get("user", {}).get("displayName", "")
    from_ref = response.get("fromRef", {}).get("displayId", "")
    to_ref = response.get("toRef", {}).get("displayId", "")
    reviewers = [
        {"name": r.get("user", {}).get("displayName", ""), "status": r.get("status", "")}
        for r in response.get("reviewers", [])
    ]
    created = response.get("createdDate")
    if created:
        from datetime import datetime

        created = datetime.fromtimestamp(created / 1000).strftime("%Y-%m-%dT%H:%M:%S")
    updated = response.get("updatedDate")
    if updated:
        from datetime import datetime

        updated = datetime.fromtimestamp(updated / 1000).strftime("%Y-%m-%dT%H:%M:%S")
    url = response.get("links", {}).get("self", [{}])[0].get("href", "")
    out = {
        "id": response.get("id"),
        "title": response.get("title"),
        "state": response.get("state"),
        "author": author,
        "from": from_ref,
        "to": to_ref,
        "reviewers": reviewers,
        "created": created,
        "updated": updated,
        "url": url,
    }
    print(json.dumps(out, indent=2))


def cmd_add_reviewer(args):
    project = args.project or detected_project
    repo = args.repo or detected_repo
    pr_id = args.pr
    reviewers = args.reviewer or []
    if not project:
        cursor_utils.die("--project required")
    if not repo:
        cursor_utils.die("--repo required")
    if not pr_id:
        cursor_utils.die("--pr is required")
    if not reviewers:
        cursor_utils.die("--reviewer is required")
    current = api_call("GET", f"/projects/{project}/repos/{repo}/pull-requests/{pr_id}")
    version = current.get("version")
    existing = current.get("reviewers", [])
    seen = {r.get("user", {}).get("name") for r in existing}
    for r in reviewers:
        if r not in seen:
            existing.append({"user": {"name": r}})
            seen.add(r)
    payload = {
        "title": current.get("title"),
        "description": current.get("description"),
        "version": version,
        "reviewers": existing,
        "fromRef": {
            "id": current.get("fromRef", {}).get("id"),
            "repository": {
                "slug": current.get("fromRef", {}).get("repository", {}).get("slug"),
                "project": {
                    "key": current.get("fromRef", {})
                    .get("repository", {})
                    .get("project", {})
                    .get("key")
                },
            },
        },
        "toRef": {
            "id": current.get("toRef", {}).get("id"),
            "repository": {
                "slug": current.get("toRef", {}).get("repository", {}).get("slug"),
                "project": {
                    "key": current.get("toRef", {})
                    .get("repository", {})
                    .get("project", {})
                    .get("key")
                },
            },
        },
    }
    response = api_call(
        "PUT", f"/projects/{project}/repos/{repo}/pull-requests/{pr_id}", data=payload
    )
    if response.get("id"):
        print(f"Reviewers updated for PR #{pr_id}")
        for r in response.get("reviewers", []):
            u = r.get("user", {})
            status = r.get("status", "")
            print(f"  - {u.get('displayName', '')} [{status}]")
    else:
        cursor_utils.die(f"Failed to update reviewers\n{json.dumps(response, indent=2)}")


def cmd_merge(args):
    project = args.project or detected_project
    repo = args.repo or detected_repo
    pr_id = args.pr
    if not project:
        cursor_utils.die("--project required")
    if not repo:
        cursor_utils.die("--repo required")
    if not pr_id:
        cursor_utils.die("--pr is required")
    current = api_call("GET", f"/projects/{project}/repos/{repo}/pull-requests/{pr_id}")
    version = current.get("version")
    response = api_call(
        "POST",
        f"/projects/{project}/repos/{repo}/pull-requests/{pr_id}/merge?version={version}",
    )
    if response.get("state") == "MERGED":
        url = response.get("links", {}).get("self", [{}])[0].get("href", "")
        print(f"Pull request #{pr_id} merged successfully!")
        print(f"  URL: {url}")
    else:
        cursor_utils.die(f"Failed to merge PR #{pr_id}\n{json.dumps(response, indent=2)}")


def cmd_decline(args):
    project = args.project or detected_project
    repo = args.repo or detected_repo
    pr_id = args.pr
    if not project:
        cursor_utils.die("--project required")
    if not repo:
        cursor_utils.die("--repo required")
    if not pr_id:
        cursor_utils.die("--pr is required")
    current = api_call("GET", f"/projects/{project}/repos/{repo}/pull-requests/{pr_id}")
    version = current.get("version")
    response = api_call(
        "POST",
        f"/projects/{project}/repos/{repo}/pull-requests/{pr_id}/decline?version={version}",
    )
    if response.get("state") == "DECLINED":
        print(f"Pull request #{pr_id} declined.")
    else:
        cursor_utils.die(f"Failed to decline PR #{pr_id}\n{json.dumps(response, indent=2)}")


def cmd_approve(args):
    project = args.project or detected_project
    repo = args.repo or detected_repo
    pr_id = args.pr
    if not project:
        cursor_utils.die("--project required")
    if not repo:
        cursor_utils.die("--repo required")
    if not pr_id:
        cursor_utils.die("--pr is required")
    current = api_call("GET", f"/projects/{project}/repos/{repo}/pull-requests/{pr_id}")
    version = current.get("version")
    response = api_call(
        "POST",
        f"/projects/{project}/repos/{repo}/pull-requests/{pr_id}/approve?version={version}",
    )
    if response.get("id"):
        print(f"Pull request #{pr_id} approved.")
    else:
        cursor_utils.die(f"Failed to approve PR #{pr_id}\n{json.dumps(response, indent=2)}")


def cmd_unapprove(args):
    project = args.project or detected_project
    repo = args.repo or detected_repo
    pr_id = args.pr
    if not project:
        cursor_utils.die("--project required")
    if not repo:
        cursor_utils.die("--repo required")
    if not pr_id:
        cursor_utils.die("--pr is required")
    current = api_call("GET", f"/projects/{project}/repos/{repo}/pull-requests/{pr_id}")
    version = current.get("version")
    url = f"{BB_BASE_URL}/rest/api/1.0/projects/{project}/repos/{repo}/pull-requests/{pr_id}/approve?version={version}"
    headers = cursor_utils.auth_header(get_token())
    cursor_utils.api_request("DELETE", url, headers=headers, data=None)
    print(f"Approval removed from PR #{pr_id}.")


def cmd_comments(args):
    project = args.project or detected_project
    repo = args.repo or detected_repo
    pr_id = args.pr
    if not pr_id:
        cursor_utils.die("--pr is required")
    if not project:
        cursor_utils.die("--project required")
    if not repo:
        cursor_utils.die("--repo required")
    response = api_call(
        "GET", f"/projects/{project}/repos/{repo}/pull-requests/{pr_id}/activities?limit=1000"
    )
    me = get_current_user()
    comments = []
    for act in response.get("values", []):
        if act.get("action") != "COMMENTED":
            continue
        c = act.get("comment", {})
        anchor = c.get("anchor")
        anchor_obj = None
        if anchor:
            anchor_obj = {
                "path": anchor.get("path"),
                "line": anchor.get("line"),
                "line_type": anchor.get("lineType"),
                "file_type": anchor.get("fileType"),
                "src_path": anchor.get("srcPath"),
            }
        replies = []
        for rc in c.get("comments", []):
            replies.append(
                {
                    "id": rc.get("id"),
                    "author": rc.get("author", {}).get("slug"),
                    "author_display": rc.get("author", {}).get("displayName"),
                    "text": rc.get("text"),
                    "created": rc.get("createdDate"),
                }
            )
        from datetime import datetime

        created_ts = c.get("createdDate")
        created_str = (
            datetime.fromtimestamp(created_ts / 1000).strftime("%Y-%m-%dT%H:%M:%S")
            if created_ts
            else ""
        )
        updated_ts = c.get("updatedDate")
        updated_str = (
            datetime.fromtimestamp(updated_ts / 1000).strftime("%Y-%m-%dT%H:%M:%S")
            if updated_ts
            else ""
        )
        has_author_reply = any(r.get("author") == me for r in replies)
        comments.append(
            {
                "id": c.get("id"),
                "author": c.get("author", {}).get("slug"),
                "author_display": c.get("author", {}).get("displayName"),
                "text": c.get("text"),
                "created": created_str,
                "updated": updated_str,
                "severity": c.get("severity", "NORMAL"),
                "state": c.get("state", "OPEN"),
                "thread_resolved": c.get("threadResolved", False),
                "anchor": anchor_obj,
                "replies": replies,
                "has_author_reply": has_author_reply,
            }
        )
    comments.sort(key=lambda x: x.get("created", ""))

    if args.unresolved:
        comments = [c for c in comments if not c["thread_resolved"] and c["author"] != me]

    if args.raw:
        for c in comments:
            for r in c.get("replies", []):
                if "created" in r and isinstance(r["created"], (int, float)):
                    from datetime import datetime

                    r["created"] = (
                        datetime.fromtimestamp(r["created"] / 1000).strftime(
                            "%Y-%m-%dT%H:%M:%S"
                        )
                        if r["created"]
                        else ""
                    )
        print(json.dumps(comments, indent=2))
        return

    count = len(comments)
    if args.unresolved:
        print(f"Unresolved comments on PR #{pr_id}: {count}")
    else:
        print(f"All comments on PR #{pr_id}: {count}")
    print()

    for c in comments:
        resolved_tag = " [RESOLVED]" if c["thread_resolved"] else ""
        print(
            f"--- Comment #{c['id']} by {c['author_display']} (@{c['author']}) [{c['state']}] ---{resolved_tag}"
        )
        print(f"  Created: {c['created']}")
        if c.get("anchor"):
            a = c["anchor"]
            line_part = f" (line {a.get('line')}, {a.get('line_type') or ''})" if a.get("line") else ""
            print(f"  File: {a.get('path', '')}{line_part}")
        else:
            print("  Type: General comment")
        print(f"  Severity: {c['severity']}")
        print(f"  Text: {c['text']}")
        replies = c.get("replies", [])
        if replies:
            print(f"  Replies ({len(replies)}):")
            for r in replies:
                created = r.get("created", "")
                if isinstance(created, (int, float)):
                    from datetime import datetime

                    created = (
                        datetime.fromtimestamp(created / 1000).strftime("%Y-%m-%dT%H:%M:%S")
                        if created
                        else ""
                    )
                print(f"    - @{r.get('author', '')} ({created}): {r.get('text', '')}")
        else:
            print("  Replies: none")
        if c.get("has_author_reply"):
            print("  ✓ You have replied")
        else:
            print("  ✗ You have NOT replied")
        print()


def cmd_reply(args):
    project = args.project or detected_project
    repo = args.repo or detected_repo
    pr_id = args.pr
    comment_id = args.comment_id
    text = args.text
    if not pr_id:
        cursor_utils.die("--pr is required")
    if not comment_id:
        cursor_utils.die("--comment-id is required")
    if not text:
        cursor_utils.die("--text is required")
    if not project:
        cursor_utils.die("--project required")
    if not repo:
        cursor_utils.die("--repo required")
    payload = {"text": text, "parent": {"id": int(comment_id)}}
    response = api_call(
        "POST",
        f"/projects/{project}/repos/{repo}/pull-requests/{pr_id}/comments",
        data=payload,
    )
    reply_id = response.get("id")
    if reply_id:
        print("Reply posted successfully!")
        print(f"  Reply ID:  #{reply_id}")
        print(f"  Parent:    #{comment_id}")
        print(f"  Text:      {text}")
    else:
        cursor_utils.die(f"Failed to post reply\n{json.dumps(response, indent=2)}")


def cmd_diff(args):
    project = args.project or detected_project
    repo = args.repo or detected_repo
    pr_id = args.pr
    context_lines = args.context_lines or 10
    if not pr_id:
        cursor_utils.die("--pr is required")
    if not project:
        cursor_utils.die("--project required")
    if not repo:
        cursor_utils.die("--repo required")
    response = api_call(
        "GET",
        f"/projects/{project}/repos/{repo}/pull-requests/{pr_id}/diff?contextLines={context_lines}",
    )
    for d in response.get("diffs", []):
        src_obj = d.get("source", {})
        dst_obj = d.get("destination", {})
        src = src_obj.get("toString", src_obj.get("path", "/dev/null"))
        dst = dst_obj.get("toString", dst_obj.get("path", "/dev/null"))
        print(f"--- {src}")
        print(f"+++ {dst}")
        print()
        for h in d.get("hunks", []):
            sl = h.get("sourceLine", 0)
            ss = h.get("sourceSpan", 0)
            dl = h.get("destinationLine", 0)
            ds = h.get("destinationSpan", 0)
            print(f"@@ -{sl},{ss} +{dl},{ds} @@")
            for seg in h.get("segments", []):
                seg_type = seg.get("type", "")
                prefix = "-" if seg_type == "REMOVED" else "+" if seg_type == "ADDED" else " "
                for line in seg.get("lines", []):
                    print(f"{prefix}{line.get('line', '')}")
        print()


def main():
    global detected_project, detected_repo, detected_branch
    detected_project, detected_repo = detect_repo_info()
    detected_branch = detect_branch()

    parser = argparse.ArgumentParser(prog="bbpr.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_p = subparsers.add_parser("create")
    create_p.add_argument("--project")
    create_p.add_argument("--repo")
    create_p.add_argument("--from", dest="from_branch")
    create_p.add_argument("--to", default="main")
    create_p.add_argument("--title", required=True)
    create_p.add_argument("--description", default="")
    create_p.add_argument("--description-file")
    create_p.add_argument("--reviewer", action="append")
    create_p.add_argument("--no-default-reviewers", action="store_true")
    create_p.set_defaults(func=cmd_create)

    list_p = subparsers.add_parser("list")
    list_p.add_argument("--project")
    list_p.add_argument("--repo")
    list_p.add_argument("--state", default="OPEN")
    list_p.set_defaults(func=cmd_list)

    get_p = subparsers.add_parser("get")
    get_p.add_argument("--project")
    get_p.add_argument("--repo")
    get_p.add_argument("--pr", required=True)
    get_p.set_defaults(func=cmd_get)

    add_reviewer_p = subparsers.add_parser("add-reviewer")
    add_reviewer_p.add_argument("--project")
    add_reviewer_p.add_argument("--repo")
    add_reviewer_p.add_argument("--pr", required=True)
    add_reviewer_p.add_argument("--reviewer", action="append")
    add_reviewer_p.set_defaults(func=cmd_add_reviewer)

    merge_p = subparsers.add_parser("merge")
    merge_p.add_argument("--project")
    merge_p.add_argument("--repo")
    merge_p.add_argument("--pr", required=True)
    merge_p.set_defaults(func=cmd_merge)

    decline_p = subparsers.add_parser("decline")
    decline_p.add_argument("--project")
    decline_p.add_argument("--repo")
    decline_p.add_argument("--pr", required=True)
    decline_p.set_defaults(func=cmd_decline)

    approve_p = subparsers.add_parser("approve")
    approve_p.add_argument("--project")
    approve_p.add_argument("--repo")
    approve_p.add_argument("--pr", required=True)
    approve_p.set_defaults(func=cmd_approve)

    unapprove_p = subparsers.add_parser("unapprove")
    unapprove_p.add_argument("--project")
    unapprove_p.add_argument("--repo")
    unapprove_p.add_argument("--pr", required=True)
    unapprove_p.set_defaults(func=cmd_unapprove)

    comments_p = subparsers.add_parser("comments")
    comments_p.add_argument("--project")
    comments_p.add_argument("--repo")
    comments_p.add_argument("--pr", required=True)
    comments_p.add_argument("--unresolved", action="store_true")
    comments_p.add_argument("--raw", action="store_true")
    comments_p.set_defaults(func=cmd_comments)

    reply_p = subparsers.add_parser("reply")
    reply_p.add_argument("--project")
    reply_p.add_argument("--repo")
    reply_p.add_argument("--pr", required=True)
    reply_p.add_argument("--comment-id", required=True)
    reply_p.add_argument("--text", required=True)
    reply_p.set_defaults(func=cmd_reply)

    diff_p = subparsers.add_parser("diff")
    diff_p.add_argument("--project")
    diff_p.add_argument("--repo")
    diff_p.add_argument("--pr", required=True)
    diff_p.add_argument("--context-lines", type=int, default=10)
    diff_p.set_defaults(func=cmd_diff)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
