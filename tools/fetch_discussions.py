#!/usr/bin/env python3
"""Fetch every LFX 2026 Term 3 pretest Discussion from kubeedge/ianvs.

Writes evidence/discussions.json: number, title, author, timestamps, body, and
the body of every comment. Used to build the prior-art coverage map.
"""
import json, subprocess, sys, pathlib

Q = """
query($cursor: String) {
  repository(owner: "kubeedge", name: "ianvs") {
    discussions(first: 25, after: $cursor, orderBy: {field: CREATED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number title createdAt updatedAt url
        category { name }
        author { login }
        bodyText
        comments(first: 20) {
          totalCount
          nodes { author { login } createdAt bodyText url }
        }
      }
    }
  }
}
"""

def gh_graphql(cursor=None):
    cmd = ["gh", "api", "graphql", "-f", f"query={Q}"]
    if cursor:
        cmd += ["-F", f"cursor={cursor}"]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    return json.loads(out)["data"]["repository"]["discussions"]

def main():
    nodes, cursor = [], None
    while True:
        page = gh_graphql(cursor)
        nodes.extend(page["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
    out = pathlib.Path("evidence/discussions.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(nodes, indent=1))
    print(f"fetched {len(nodes)} discussions -> {out}")

if __name__ == "__main__":
    main()
