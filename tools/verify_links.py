#!/usr/bin/env python3
"""Check every submitted permalink resolves, signed out (plain HTTP HEAD)."""
import json, pathlib, subprocess, sys

links = []
d = json.loads(pathlib.Path("evidence/posted.json").read_text())
links.append(("discussion", d["discussion"]["url"]))
for k, v in d["comments"].items():
    links.append((k, v["url"]))
for k, v in json.loads(pathlib.Path("evidence/posted_targets.json").read_text()).items():
    links.append((k, v))

bad = 0
for label, url in links:
    code = subprocess.run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-L", "--max-time", "20", url],
        capture_output=True, text=True).stdout.strip()
    ok = code == "200"
    bad += not ok
    print(f"  {'OK ' if ok else 'BAD'} {code}  {label:<12} {url}")
print(f"\n{len(links)} links checked, {bad} broken")
sys.exit(1 if bad else 0)
