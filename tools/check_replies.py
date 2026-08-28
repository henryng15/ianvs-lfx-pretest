#!/usr/bin/env python3
"""Report any activity on our posted targets that arrived after we posted."""
import json, pathlib, subprocess

MINE = "henryng15"
CUT = "2026-08-27T05:00:00Z"          # just before our posting run
PRS = [558, 651, 642, 598, 702, 617, 569, 739, 632, 540]
ISSUES = [557, 597, 641, 568]


def api(path):
    return json.loads(subprocess.run(["gh", "api", path], capture_output=True,
                                     text=True).stdout or "[]")


def show(kind, num):
    rows = []
    for c in api(f"repos/kubeedge/ianvs/issues/{num}/comments?per_page=100"):
        rows.append(("comment", c["user"]["login"], c["created_at"], c["html_url"], c["body"]))
    if kind == "pr":
        for r in api(f"repos/kubeedge/ianvs/pulls/{num}/reviews?per_page=100"):
            rows.append(("review", r["user"]["login"], r.get("submitted_at") or "",
                         r["html_url"], r.get("body") or ""))
        for r in api(f"repos/kubeedge/ianvs/pulls/{num}/comments?per_page=100"):
            rows.append(("inline", r["user"]["login"], r["created_at"], r["html_url"], r["body"]))
    new = [r for r in rows if r[2] > CUT and r[1] != MINE and r[1] != "kubeedge-bot"]
    tag = f"{kind.upper()} #{num}"
    if not new:
        print(f"  {tag:<12} no new activity")
        return []
    print(f"\n  ***** {tag}: {len(new)} NEW *****")
    for kindx, who, when, url, body in new:
        print(f"    [{who}] {kindx} {when}\n    {url}")
        for line in body.strip().splitlines()[:45]:
            print("      " + line)
        print()
    return new


found = []
for n in PRS:
    found += show("pr", n)
for n in ISSUES:
    found += show("issue", n)
print(f"\n=== total new items: {len(found)} ===")
