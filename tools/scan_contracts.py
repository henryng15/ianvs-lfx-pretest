#!/usr/bin/env python3
"""Static census of third-party contract surfaces across Ianvs Examples.

Three questions, answered by parsing every Example .py with ast (no imports,
no deps, no GPU):
  1. How many modules declare a malformed __all__ (string instead of sequence,
     or naming something the module never defines)?
  2. How many modules import symbols from `transformers` at module scope?
  3. How many Example requirements files exist, and how many pin versions?
"""
import ast, pathlib, collections, sys, re, json

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "ianvs")
EX = ROOT / "examples"

bad_all, all_ok, tf_imports, parse_err = [], 0, [], []

for f in sorted(EX.rglob("*.py")):
    try:
        tree = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError as e:
        parse_err.append((f, e))
        continue

    defined = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(n.name)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    defined.add(t.id)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                defined.add((a.asname or a.name).split(".")[0])

    for n in tree.body:
        if isinstance(n, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "__all__" for t in n.targets):
            v = n.value
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                bad_all.append((f, n.lineno, "STRING not sequence", v.value))
            elif isinstance(v, (ast.List, ast.Tuple)):
                names = [e.value for e in v.elts
                         if isinstance(e, ast.Constant) and isinstance(e.value, str)]
                missing = [x for x in names if x not in defined]
                if missing:
                    bad_all.append((f, n.lineno, "names not defined in module", missing))
                else:
                    all_ok += 1

    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("transformers"):
            tf_imports.append((f, n.lineno, n.module, [a.name for a in n.names]))

print(f"Example .py files parsed : {len(list(EX.rglob('*.py')))}  (syntax errors: {len(parse_err)})")
print(f"__all__ declarations OK  : {all_ok}")
print(f"__all__ declarations BAD : {len(bad_all)}")
for f, ln, why, what in bad_all:
    print(f"   {f.relative_to(ROOT)}:{ln}  [{why}] {what}")

print(f"\nmodule-scope `from transformers...` imports: {len(tf_imports)} "
      f"in {len({t[0] for t in tf_imports})} files")
byfile = collections.Counter(str(t[0].relative_to(ROOT)) for t in tf_imports)
for f, c in byfile.most_common(12):
    print(f"   {c:>2}  {f}")

reqs = sorted(EX.rglob("requirements*.txt"))
pinned = unpinned = 0
for r in reqs:
    for line in r.read_text(errors="replace").splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        if re.search(r"[=<>~!]=|[<>]", line):
            pinned += 1
        else:
            unpinned += 1
print(f"\nExample requirements files: {len(reqs)}")
print(f"   constrained requirement lines : {pinned}")
print(f"   UNCONSTRAINED requirement lines: {unpinned}")
