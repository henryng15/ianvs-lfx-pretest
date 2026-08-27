#!/usr/bin/env python3
"""Post the target-specific comments: a formal review on each PR, a comment on
each issue. Records every permalink in evidence/posted_targets.json and skips
anything already posted, so the script is safe to re-run.
"""
import json, pathlib, subprocess, sys, time

PRS    = [558, 651, 642, 598, 702, 617, 569, 739, 632, 540]
ISSUES = [557, 597, 641, 568]
STATE  = pathlib.Path("evidence/posted_targets.json")
REPO   = "kubeedge/ianvs"


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"failed: {' '.join(cmd)}\n{r.stderr}\n{r.stdout}")
    return r.stdout.strip()


def latest_review_url(pr):
    """Permalink of henryng15's most recent review on this PR."""
    out = run(["gh", "api", f"repos/{REPO}/pulls/{pr}/reviews"])
    mine = [r for r in json.loads(out) if r["user"]["login"] == "henryng15"]
    return mine[-1]["html_url"] if mine else None


def main():
    state = json.loads(STATE.read_text()) if STATE.exists() else {}

    for pr in PRS:
        key = f"pr-{pr}"
        if key in state:
            print(f"  {key}: already posted -> {state[key]}"); continue
        body = pathlib.Path(f"submission/reviews/{key}.md")
        run(["gh", "pr", "review", str(pr), "-R", REPO, "--comment",
             "--body-file", str(body)])
        url = latest_review_url(pr) or f"https://github.com/{REPO}/pull/{pr}"
        state[key] = url
        STATE.write_text(json.dumps(state, indent=1))
        print(f"  {key}: review posted -> {url}")
        time.sleep(10)

    for iss in ISSUES:
        key = f"issue-{iss}"
        if key in state:
            print(f"  {key}: already posted -> {state[key]}"); continue
        body = pathlib.Path(f"submission/reviews/{key}.md")
        url = run(["gh", "issue", "comment", str(iss), "-R", REPO,
                   "--body-file", str(body)])
        state[key] = url
        STATE.write_text(json.dumps(state, indent=1))
        print(f"  {key}: comment posted -> {url}")
        time.sleep(10)

    print("\n=== all target links ===")
    for k in [f"pr-{p}" for p in PRS] + [f"issue-{i}" for i in ISSUES]:
        print(f"  {k:<12} {state[k]}")


if __name__ == "__main__":
    main()
