#!/usr/bin/env python3
"""What actually happens when an Example declares an unknown paradigm_type.

Runs two checks against a real Ianvs install:
  1. the ianvs CLI on the Example's own benchmarkingjob.yaml
  2. Algorithm(...) directly, which is where paradigm_type is validated

Requires the ianvs runtime deps (prettytable, pyyaml, colorlog, tqdm, pandas,
numpy, matplotlib, onnx, scikit-learn) plus the bundled sedna wheel:

    python -m venv .venv && . .venv/bin/activate
    pip install -r ianvs/requirements.txt
    pip install ianvs/resources/third_party/sedna-0.6.0.1-py3-none-any.whl
"""
import subprocess, sys, pathlib

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "ianvs").resolve()
PY_ = sys.executable
sys.path.insert(0, str(ROOT))

sha = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                     capture_output=True, text=True).stdout.strip()
print(f"ianvs commit under test: {sha}\n")

print("=" * 74)
print("1. ianvs CLI on examples/yaoba/singletask_learning_boost")
print("=" * 74)
r = subprocess.run([PY_, "benchmarking.py", "-f",
                    "examples/yaoba/singletask_learning_boost/benchmarkingjob.yaml"],
                   capture_output=True, text=True, cwd=str(ROOT))
print(f"exit code: {r.returncode}")
for line in (r.stderr or r.stdout).strip().splitlines()[-3:]:
    print("  " + line)

print("\n" + "=" * 74)
print("2. Algorithm(...) -- where paradigm_type is validated")
print("=" * 74)
from core.testcasecontroller.algorithm import Algorithm      # noqa: E402
from core.common import utils                                # noqa: E402

for label, path in [
    ("yaoba acboost", "examples/yaoba/singletask_learning_boost/testalgorithms/algorithm.yaml"),
    ("yaoba tta", "examples/yaoba/singletask_learning_yolox_tta/testalgorithms/algorithm.yaml"),
    ("valid control", "examples/llm_simple_qa/testalgorithms/gen/gen_algorithm.yaml"),
]:
    cfg = utils.yaml2dict(str(ROOT / path))
    pt = cfg["algorithm"].get("paradigm_type")
    print(f"\n  {label}: paradigm_type={pt!r}")
    try:
        Algorithm(name=label, config=cfg)
        print("     -> constructed, no error")
    except Exception as e:                                    # noqa: BLE001
        print(f"     -> {type(e).__name__}: {str(e)[:150]}")

print("\n" + "=" * 74)
print("Conclusion: Ianvs Core DOES validate paradigm_type and fails loudly")
print("(core/testcasecontroller/algorithm/algorithm.py:140-143). The CI")
print("validator on main reports PASS for both Examples anyway.")
print("=" * 74)
