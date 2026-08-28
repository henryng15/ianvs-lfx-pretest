#!/usr/bin/env python3
"""Run the validator that already ships on main and summarise its verdicts.

.github/workflows/validator/ landed with PR #771 (merge commit 37a9c60) and is
wired into static_code_requirement_cicd.yaml. This runs it unmodified over the
Examples this submission discusses.
"""
import json, pathlib, subprocess, sys

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "ianvs").resolve()
EXAMPLES = [
    "examples/yaoba/singletask_learning_boost",
    "examples/yaoba/singletask_learning_yolox_tta",
    "examples/robot-cityscapes-synthia/lifelong_learning_bench/semantic-segmentation",
    "examples/MOT17/multiedge_inference_bench/pedestrian_tracking",
    "examples/Cloud_Robotics/cloud-edge-collaborative-inference_bench/perception-reasoning",
]

print(f"validator: {ROOT}/.github/workflows/validator/validation_runner.py")
print(f"commit   : {subprocess.run(['git','-C',str(ROOT),'rev-parse','--short','HEAD'],capture_output=True,text=True).stdout.strip()}\n")

for ex in EXAMPLES:
    r = subprocess.run(
        [sys.executable, ".github/workflows/validator/validation_runner.py", "--static",
         "--example", ex, "--inventory",
         ".github/workflows/validator/data/example_inventory.yaml", "--format", "json"],
        capture_output=True, text=True, cwd=str(ROOT))
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        print(f"  {ex}\n      (no inventory entry)"); continue
    for e in data.get("examples", []):
        errs = [c["name"] for c in e["checks"] if c["status"] == "ERROR"]
        warns = [c["name"] for c in e["checks"] if c["status"] == "WARNING"]
        verdict = "PASS" if e["passed"] else "FAIL"
        print(f"  [{verdict}] {ex}\n         inventory name : {e['name']}")
        print(f"         ERROR checks   : {errs or 'none'}")
        print(f"         WARNING checks : {len(warns)}")
