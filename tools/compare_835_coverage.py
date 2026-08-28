#!/usr/bin/env python3
"""Compare PR #835's config path check against the census in tools/scan_metric_contract.py.

#835 walks benchmarkingjob*.yaml -> testenv -> algorithm and checks that each
referenced path exists, with a 47-entry allowlist of already-broken references.
This measures two things it cannot report:

  1. testenv*.yaml files that no benchmarkingjob*.yaml reaches -- never visited.
  2. broken metric urls that are neither reachable nor allowlisted.
"""
import pathlib, re, sys, yaml

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "ianvs").resolve()
EX = ROOT / "examples"
ALLOW = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else None


def load(p):
    try:
        return yaml.safe_load(p.read_text(encoding="utf-8", errors="replace")) or {}
    except yaml.YAMLError:
        return {}


def resolve(raw, source):
    if raw.startswith("/"):
        return pathlib.Path(raw)
    if raw.startswith(("./examples", "examples")):
        return ROOT / raw.lstrip("./")
    return source.parent / raw


# --- what #835 would visit: testenv files reachable from a benchmarkingjob ----
jobs = [p for p in EX.rglob("*.yaml") if p.name.startswith("benchmarkingjob")]
reachable = set()
for j in jobs:
    cfg = load(j).get("benchmarkingjob") or {}
    te = cfg.get("testenv")
    if isinstance(te, str):
        try:
            r = resolve(te, j).resolve()
            if r.exists():
                reachable.add(r)
        except OSError:
            pass

all_testenv = {p.resolve() for p in EX.rglob("testenv*.yaml")}
unreached = sorted(all_testenv - reachable)

print(f"benchmarkingjob*.yaml files            : {len(jobs)}")
print(f"testenv*.yaml files in the repository  : {len(all_testenv)}")
print(f"  reachable from a benchmarkingjob     : {len(reachable)}")
print(f"  NEVER VISITED by #835's walk         : {len(unreached)}")

# --- broken metric urls inside the never-visited files ------------------------
hidden = []
for p in unreached:
    metrics = (load(p).get("testenv") or {}).get("metrics") or []
    for i, m in enumerate(metrics):
        if not isinstance(m, dict):
            continue
        url = m.get("url")
        if not url:
            continue
        try:
            ok = resolve(url, p).exists()
        except OSError:
            ok = False
        if not ok:
            hidden.append((p.relative_to(ROOT), i, m.get("name"), url))

print(f"\nbroken metric urls inside never-visited testenv files: {len(hidden)}")
for f, i, name, url in hidden:
    print(f"  {f}\n      metrics[{i}] name={name!r} url={url}")
