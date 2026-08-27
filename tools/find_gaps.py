#!/usr/bin/env python3
"""Cross the open-target list with the rival coverage map to find the targets
that no (or almost no) other candidate has claimed."""
import json, pathlib

cov = json.loads(pathlib.Path("evidence/coverage.json").read_text())["by_target"]
tg = json.loads(pathlib.Path("evidence/targets.json").read_text())
claim_count = {int(k): len(v) for k, v in cov.items()}

def report(kind, rows):
    free = [(r, claim_count.get(r["number"], 0)) for r in rows]
    free.sort(key=lambda x: (x[1], -x[0]["number"]))
    unclaimed = [f for f in free if f[1] == 0]
    thin = [f for f in free if f[1] == 1]
    print(f"\n{'='*78}\n{kind}: {len(rows)} open in range | "
          f"UNCLAIMED={len(unclaimed)} | claimed-once={len(thin)}\n{'='*78}")
    for r, c in free[:70]:
        print(f"  #{r['number']:<4} rivals={c}  {r['title'][:88]}")

report("OPEN ISSUES (#348-846)", tg["issues"])

tg2 = json.loads(pathlib.Path("evidence/targets.json").read_text())
rows = [r for r in tg2["prs"] if not r["draft"]]
free = [(r, claim_count.get(r["number"], 0)) for r in rows]
free.sort(key=lambda x: (x[1], -x[0]["number"]))
print(f"\n{'='*78}\nOPEN NON-DRAFT PRs (#133-851): {len(rows)} | "
      f"UNCLAIMED={sum(1 for f in free if f[1]==0)}\n{'='*78}")
for r, c in free[:60]:
    print(f"  #{r['number']:<4} rivals={c}  {r['title'][:88]}")
