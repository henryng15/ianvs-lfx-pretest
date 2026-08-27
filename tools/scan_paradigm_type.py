#!/usr/bin/env python3
"""Check every Example's declared `paradigm_type` against core's ParadigmType enum.

core/testcasecontroller/algorithm/algorithm.py:109-127 and
core/testcasecontroller/algorithm/paradigm/base.py:95-152 dispatch on this string
through a chain of `if` comparisons with no `else`, so an unrecognised value
matches nothing and the call returns None -- silently.
"""
import ast, pathlib, re, sys

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "ianvs").resolve()

tree = ast.parse((ROOT / "core/common/constant.py").read_text())
enum = {n.value.value
        for cls in tree.body if isinstance(cls, ast.ClassDef) and cls.name == "ParadigmType"
        for n in cls.body
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant)}
print(f"ParadigmType admits {len(enum)} values: {sorted(enum)}\n")

declared, bad = {}, {}
for y in (ROOT / "examples").rglob("*.yaml"):
    for m in re.finditer(r'paradigm_type:\s*"?([\w\-]+)"?', y.read_text(errors="replace")):
        declared.setdefault(m.group(1), []).append(str(y.relative_to(ROOT)))
        if m.group(1) not in enum:
            bad.setdefault(m.group(1), []).append(str(y.relative_to(ROOT)))

print(f"distinct paradigm_type values declared by Examples : {len(declared)}")
print(f"of those, NOT admitted by ParadigmType             : {len(bad)}")
for k, v in sorted(bad.items()):
    print(f"\n  {k!r} -> dispatch falls through, returns None")
    for f in v:
        print(f"      {f}")
