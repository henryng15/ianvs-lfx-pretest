#!/usr/bin/env python3
"""Build the prior-art coverage map from evidence/discussions.json.

For every LFX 2026 Term 3 pretest Discussion, extract the Issue/PR numbers it
cites, then invert that into "which target is claimed by whom". Targets are
scored by how many rival candidates already cite them.
"""
import json, re, collections, pathlib

ISSUE_RE = re.compile(r"#(\d{3,4})\b")
LFX_RE = re.compile(r"LFX 2026 Term 3|Term 3", re.I)

data = json.loads(pathlib.Path("evidence/discussions.json").read_text())
lfx = [d for d in data if LFX_RE.search(d["title"] or "")]

claims = {}      # discussion number -> set of cited target numbers
by_target = collections.defaultdict(set)

for d in lfx:
    text = (d["bodyText"] or "")
    for c in d["comments"]["nodes"]:
        text += "\n" + (c["bodyText"] or "")
    nums = {int(n) for n in ISSUE_RE.findall(text)}
    # keep only plausible target range
    nums = {n for n in nums if 133 <= n <= 900}
    claims[d["number"]] = nums
    for n in nums:
        by_target[n].add(d["number"])

pathlib.Path("evidence/coverage.json").write_text(json.dumps({
    "discussions": {str(k): sorted(v) for k, v in claims.items()},
    "by_target": {str(k): sorted(v) for k, v in by_target.items()},
}, indent=1))

print(f"LFX discussions parsed: {len(lfx)}")
print(f"distinct targets cited : {len(by_target)}")
print()
print("=== most-contested targets (cited by N rival discussions) ===")
for tgt, ds in sorted(by_target.items(), key=lambda kv: -len(kv[1]))[:30]:
    print(f"  #{tgt:<4} claimed by {len(ds):>2} discussions: {sorted(ds)[:8]}")
