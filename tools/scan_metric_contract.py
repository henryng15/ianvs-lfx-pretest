#!/usr/bin/env python3
"""Check the exact contract Core resolves for testenv metrics.

core/testcasecontroller/metrics/metrics.py:get_metric_func() does:
    if url:  load_module(url); ClassFactory.get_cls(ClassType.GENERAL, name)
    else:    getattr(metrics_module, name.lower() + "_func")

So for every metric entry that declares a `url`, the module at that url must
register `name` via @ClassFactory.register(..., alias=name) -- or the run dies
at lookup time. This compares both sides statically.
"""
import ast, pathlib, sys, yaml, json

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "ianvs")
BUILTIN = {"samples_transfer_ratio", "f1_score", "accuracy", "task_avg_acc",
           "matrix", "bwt", "fwt", "compute_loss"}

def registered_names(pyfile: pathlib.Path):
    """Aliases the module at `pyfile` registers with ClassFactory."""
    out = set()
    try:
        tree = ast.parse(pyfile.read_text(encoding="utf-8", errors="replace"))
    except (SyntaxError, OSError):
        return None
    for n in ast.walk(tree):
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for d in n.decorator_list:
            if isinstance(d, ast.Call) and "ClassFactory.register" in ast.unparse(d.func):
                alias = next((kw.value.value for kw in d.keywords
                              if kw.arg == "alias" and isinstance(kw.value, ast.Constant)), None)
                out.add(alias or n.name)
    return out

rows, missing_file, mismatch, abs_paths, ok = [], [], [], [], 0
for y in sorted((ROOT / "examples").rglob("testenv*.yaml")):
    try:
        cfg = yaml.safe_load(y.read_text(encoding="utf-8", errors="replace")) or {}
    except yaml.YAMLError as e:
        rows.append((y, "YAML-PARSE-ERROR", str(e)[:80])); continue
    metrics = (cfg.get("testenv") or {}).get("metrics") or []
    for m in metrics:
        if not isinstance(m, dict):
            continue
        name, url = m.get("name"), m.get("url")
        if not url:
            continue
        if url.startswith("/"):
            abs_paths.append((str(y.relative_to(ROOT)), name, url)); continue
        p = (ROOT / url.lstrip("./")) if url.startswith(("./", "examples/")) else (y.parent / url)
        try:
            exists = p.exists()
        except OSError:
            exists = False
        if not exists:
            missing_file.append((str(y.relative_to(ROOT)), name, url)); continue
        reg = registered_names(p)
        if reg is None:
            mismatch.append((str(y.relative_to(ROOT)), name, url, "unparseable")); continue
        if name in reg:
            ok += 1
        else:
            mismatch.append((str(y.relative_to(ROOT)), name, str(p.relative_to(ROOT)),
                             f"module registers {sorted(reg) or '<nothing>'}"))

print(f"metric entries with a url that resolve OK      : {ok}")
print(f"metric entries with an ABSOLUTE developer path : {len(abs_paths)}")
for r in abs_paths:
    print(f"   {r[0]}\n      name={r[1]!r} url={r[2]!r}")
print(f"metric entries whose url FILE DOES NOT EXIST   : {len(missing_file)}")
for r in missing_file:
    print(f"   {r[0]}\n      name={r[1]!r} url={r[2]!r}")
print(f"\nmetric entries whose NAME IS NOT REGISTERED    : {len(mismatch)}")
for r in mismatch:
    print(f"   {r[0]}\n      name={r[1]!r} -> {r[2]}  ({r[3]})")
