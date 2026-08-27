#!/usr/bin/env python3
"""Create the pretest Discussion and post the five Task comments into it.

Idempotency: writes evidence/posted.json. If that file already records a
discussion id, the script refuses to create a second one -- the pretest scores
only the most recent Discussion per candidate, so a duplicate is costly.
"""
import json, pathlib, subprocess, sys, time

REPO_ID = "R_kgDOHpN2fQ"
CATEGORY_ID = "DIC_kwDOHpN2fc4Cxnwo"          # Show and tell
TITLE = ("LFX 2026 Term 3 Example Restoration: problem analysis of Ianvs's "
         "unenforced Example interface contract")
STATE = pathlib.Path("evidence/posted.json")


def gql(query, **variables):
    cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
    for k, v in variables.items():
        cmd += ["-f", f"{k}={v}"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"GraphQL failed:\n{r.stderr}\n{r.stdout}")
    out = json.loads(r.stdout)
    if "errors" in out:
        raise SystemExit(f"GraphQL errors: {out['errors']}")
    return out["data"]


CREATE = """
mutation($repo: ID!, $cat: ID!, $title: String!, $body: String!) {
  createDiscussion(input: {repositoryId: $repo, categoryId: $cat,
                           title: $title, body: $body}) {
    discussion { id number url }
  }
}"""

COMMENT = """
mutation($did: ID!, $body: String!) {
  addDiscussionComment(input: {discussionId: $did, body: $body}) {
    comment { id url }
  }
}"""

TASKS = [
    ("Task 1", "submission/01-task1.md"),
    ("Task 2", "submission/02-task2.md"),
    ("Task 3", "submission/03-task3.md"),
    ("Task 4", "submission/04-task4.md"),
    ("Bonus",  "submission/05-bonus.md"),
]


def main():
    state = json.loads(STATE.read_text()) if STATE.exists() else {}

    if "discussion" not in state:
        body = pathlib.Path("submission/00-discussion-body.md").read_text()
        d = gql(CREATE, repo=REPO_ID, cat=CATEGORY_ID, title=TITLE,
                body=body)["createDiscussion"]["discussion"]
        state["discussion"] = d
        STATE.write_text(json.dumps(state, indent=1))
        print(f"created discussion #{d['number']} -> {d['url']}")
    else:
        print(f"discussion already exists: {state['discussion']['url']}")

    state.setdefault("comments", {})
    for label, path in TASKS:
        if label in state["comments"]:
            print(f"  {label}: already posted -> {state['comments'][label]['url']}")
            continue
        body = pathlib.Path(path).read_text()
        c = gql(COMMENT, did=state["discussion"]["id"],
                body=body)["addDiscussionComment"]["comment"]
        state["comments"][label] = c
        STATE.write_text(json.dumps(state, indent=1))
        print(f"  {label}: posted -> {c['url']}")
        time.sleep(8)          # pace, so a burst is not read as spam

    print("\nAll links:")
    print(" ", state["discussion"]["url"])
    for label, _ in TASKS:
        print(f"  {label}: {state['comments'][label]['url']}")


if __name__ == "__main__":
    main()
