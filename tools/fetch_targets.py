#!/usr/bin/env python3
"""Fetch every OPEN issue and PR in kubeedge/ianvs and keep those inside the
pretest Target Rule ranges (issues #348-846, PRs #133-851).

Writes evidence/targets.json.
"""
import json, subprocess, pathlib

def paged(kind):
    items, page = [], 1
    while True:
        out = subprocess.run(
            ["gh", "api", f"repos/kubeedge/ianvs/{kind}?state=open&per_page=100&page={page}"],
            capture_output=True, text=True, check=True).stdout
        batch = json.loads(out)
        if not batch:
            break
        items.extend(batch)
        page += 1
    return items

issues_and_prs = paged("issues")   # GitHub returns PRs inside /issues too
prs = paged("pulls")
pr_numbers = {p["number"] for p in prs}

targets = {"issues": [], "prs": []}
for it in issues_and_prs:
    n = it["number"]
    if n in pr_numbers or "pull_request" in it:
        continue
    if 348 <= n <= 846:
        targets["issues"].append({
            "number": n, "title": it["title"], "user": it["user"]["login"],
            "created": it["created_at"], "comments": it["comments"],
            "labels": [l["name"] for l in it["labels"]],
        })
for p in prs:
    n = p["number"]
    if 133 <= n <= 851:
        targets["prs"].append({
            "number": n, "title": p["title"], "user": p["user"]["login"],
            "created": p["created_at"], "draft": p["draft"],
        })

pathlib.Path("evidence/targets.json").write_text(json.dumps(targets, indent=1))
print(f"open in-range issues: {len(targets['issues'])}")
print(f"open in-range PRs   : {len(targets['prs'])}")
