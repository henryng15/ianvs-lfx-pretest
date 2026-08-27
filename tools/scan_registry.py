#!/usr/bin/env python3
"""Census of the contract Ianvs Core actually resolves at runtime.

Core resolves a metric/module by matching a YAML `name:` string against the
Sedna ClassFactory registry key created by an @ClassFactory.register(...)
decorator. Nothing validates that the two sides agree until a benchmark run
reaches the lookup. This script parses both sides statically.
"""
import ast, pathlib, re, sys, json, collections

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "ianvs")
EX = ROOT / "examples"

# --- side A: what the Python modules register -------------------------------
registered = collections.defaultdict(list)   # alias -> [(file, lineno)]
decorated_funcs = collections.defaultdict(list)

for f in sorted(EX.rglob("*.py")):
    try:
        tree = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        continue
    for n in ast.walk(tree):
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for d in n.decorator_list:
            if not isinstance(d, ast.Call):
                continue
            fn = ast.unparse(d.func) if hasattr(ast, "unparse") else ""
            if "ClassFactory.register" not in fn:
                continue
            alias = None
            for kw in d.keywords:
                if kw.arg == "alias" and isinstance(kw.value, ast.Constant):
                    alias = kw.value.value
            key = alias or n.name
            registered[key].append((str(f.relative_to(ROOT)), n.lineno, alias is not None))

# --- side B: what the YAML configs ask for ----------------------------------
NAME_RE = re.compile(r"^\s*(?:-\s*)?name:\s*[\"']?([A-Za-z_][\w\-]*)[\"']?\s*$", re.M)
wanted = collections.defaultdict(list)
for y in sorted(EX.rglob("*.yaml")):
    txt = y.read_text(encoding="utf-8", errors="replace")
    for m in NAME_RE.finditer(txt):
        wanted[m.group(1)].append(str(y.relative_to(ROOT)))

print(f"distinct ClassFactory registration keys in examples : {len(registered)}")
print(f"distinct `name:` values requested by example YAMLs  : {len(wanted)}")

unresolved = {k: v for k, v in wanted.items() if k not in registered}
print(f"\n=== YAML `name:` values with NO matching registration in examples/ ===")
print(f"({len(unresolved)} of {len(wanted)})")
for k, v in sorted(unresolved.items()):
    print(f"  {k:<34} wanted by {len(v)} yaml(s), e.g. {v[0]}")

print(f"\n=== registration keys never requested by any YAML ===")
orphan = {k: v for k, v in registered.items() if k not in wanted}
print(f"({len(orphan)} of {len(registered)})")
for k, v in sorted(orphan.items())[:25]:
    print(f"  {k:<34} {v[0][0]}:{v[0][1]}")

pathlib.Path("evidence/registry_census.json").write_text(json.dumps(
    {"registered": {k: v for k, v in registered.items()},
     "wanted": dict(wanted), "unresolved": unresolved}, indent=1))
