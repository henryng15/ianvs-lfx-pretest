#!/usr/bin/env python3
"""Update already-posted Discussion comments in place with their current source.

Editing preserves the permalink, so links already recorded stay valid.
"""
import json, pathlib, subprocess, sys, time

STATE = json.loads(pathlib.Path("evidence/posted.json").read_text())
MAP = {
    "Task 1": "submission/01-task1.md",
    "Task 2": "submission/02-task2.md",
    "Task 3": "submission/03-task3.md",
    "Task 4": "submission/04-task4.md",
    "Bonus":  "submission/05-bonus.md",
}
UPDATE = """
mutation($id: ID!, $body: String!) {
  updateDiscussionComment(input: {commentId: $id, body: $body}) {
    comment { url updatedAt }
  }
}"""


def gql(query, **variables):
    cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
    for k, v in variables.items():
        cmd += ["-f", f"{k}={v}"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"failed:\n{r.stderr}\n{r.stdout}")
    out = json.loads(r.stdout)
    if "errors" in out:
        raise SystemExit(f"errors: {out['errors']}")
    return out["data"]


targets = sys.argv[1:] or list(MAP)
for label in targets:
    body = pathlib.Path(MAP[label]).read_text()
    c = gql(UPDATE, id=STATE["comments"][label]["id"],
            body=body)["updateDiscussionComment"]["comment"]
    print(f"  {label}: updated ({len(body)} chars) -> {c['url']}")
    time.sleep(5)
