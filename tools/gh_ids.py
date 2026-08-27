#!/usr/bin/env python3
"""Fetch the node id of kubeedge/ianvs and its discussion category ids."""
import json, subprocess
Q = '{ repository(owner:"kubeedge", name:"ianvs"){ id discussionCategories(first:20){ nodes{ id name } } } }'
out = subprocess.run(["gh", "api", "graphql", "-f", f"query={Q}"],
                     capture_output=True, text=True, check=True).stdout
d = json.loads(out)["data"]["repository"]
print("repositoryId:", d["id"])
for n in d["discussionCategories"]["nodes"]:
    print(f"  {n['name']:<24} {n['id']}")
