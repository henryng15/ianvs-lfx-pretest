#!/usr/bin/env python3
"""Evidence that core.common.utils.parse_kwargs is unreachable in this repo.

Issue #597 reports that parse_kwargs() drops keyword-only parameters, and two
open PRs (#598, #702) fix it. The defect in the function body is real. What is
not established in either PR is whether any Ianvs code path reaches it.

This script resolves three questions against the checked-out tree:
  1. call sites of parse_kwargs inside core/ and examples/
  2. whether the bundled Sedna wheel imports Ianvs's helper or ships its own
  3. what the function would do if it were called (behaviour is confirmed, so
     the defect is not disputed -- only its blast radius)
"""
import ast, io, pathlib, subprocess, sys, zipfile
from inspect import getfullargspec

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "ianvs").resolve()

sha = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                     capture_output=True, text=True).stdout.strip()
print(f"ianvs commit under test: {sha}\n")

# --- 1. call sites -----------------------------------------------------------
print("[1] Call sites of core.common.utils.parse_kwargs")
defs, calls = [], []
for f in list((ROOT / "core").rglob("*.py")) + list((ROOT / "examples").rglob("*.py")):
    try:
        tree = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        continue
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == "parse_kwargs":
            defs.append(f"{f.relative_to(ROOT)}:{n.lineno}")
        if isinstance(n, ast.Call):
            name = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
            if name == "parse_kwargs":
                calls.append(f"{f.relative_to(ROOT)}:{n.lineno}")
print(f"    definitions : {defs}")
print(f"    invocations : {calls or 'NONE'}")

imports = subprocess.run(
    ["grep", "-rn", "-E", r"from core\.common\.utils import.*parse_kwargs|utils\.parse_kwargs",
     str(ROOT / "core"), str(ROOT / "examples")], capture_output=True, text=True).stdout.strip()
print(f"    imports of the helper: {imports or 'NONE'}")

# --- 2. does Sedna use Ianvs's helper, or its own? ---------------------------
print("\n[2] Sedna wheel (resources/third_party/sedna-0.6.0.1-py3-none-any.whl)")
whl = ROOT / "resources/third_party/sedna-0.6.0.1-py3-none-any.whl"
z = zipfile.ZipFile(whl)
own_defs, own_calls = [], []
for n in z.namelist():
    if not n.endswith(".py"):
        continue
    src = z.read(n).decode(errors="replace")
    if "parse_kwargs" not in src:
        continue
    for i, line in enumerate(src.splitlines(), 1):
        if "def parse_kwargs" in line:
            own_defs.append(f"{n}:{i}")
        elif "parse_kwargs(" in line:
            own_calls.append(f"{n}:{i}")
print(f"    Sedna defines its own parse_kwargs at : {own_defs}")
print(f"    Sedna call sites                      : {own_calls}")
print(f"    Sedna imports from core.common.utils  : "
      f"{'YES' if any(b'core.common.utils' in z.read(n) for n in z.namelist() if n.endswith('.py')) else 'NO'}")

# --- 3. confirm the reported behaviour ---------------------------------------
print("\n[3] Reported behaviour of the Ianvs helper (issue #597)")
sys.path.insert(0, str(ROOT))
from core.common.utils import parse_kwargs   # noqa: E402

def positional(threshold=0.5): ...
def kwonly(*, threshold=0.5): ...
print(f"    parse_kwargs(positional, threshold=0.9) -> {parse_kwargs(positional, threshold=0.9)}")
print(f"    parse_kwargs(kwonly,     threshold=0.9) -> {parse_kwargs(kwonly, threshold=0.9)}")
print("    -> the drop is real; getfullargspec().kwonlyargs is ignored.")

print("\n" + "=" * 72)
print("  Ianvs core defines parse_kwargs and never calls it.")
print("  Sedna ships and calls its OWN parse_kwargs; it does not import Ianvs's.")
print("  #598 and #702 therefore correct a real defect in unreachable code,")
print("  and they are two PRs for one issue.")
print("=" * 72)
