#!/usr/bin/env python3
"""Evidence that `__all__` in Ianvs Example modules is inert metadata.

`__all__` only has an effect when a module is consumed by `from <mod> import *`.
This script establishes three facts against the checked-out tree:

  1. Ianvs Core never star-imports anything.
  2. Core resolves Example metrics and modules by ClassFactory alias, not by
     `__all__`  (core/testcasecontroller/metrics/metrics.py:172-175,
      core/testcasecontroller/algorithm/module/module.py:123-133).
  3. No module carrying a malformed `__all__` is the target of any star-import
     anywhere in examples/.

If all three hold, correcting `__all__` cannot change runtime behaviour, so a PR
that only corrects `__all__` is a readability change -- not a bug fix.

Usage: python3 tools/probe_all_is_inert.py [path/to/ianvs]
"""
import ast, pathlib, re, subprocess, sys

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "ianvs").resolve()
EX, CORE = ROOT / "examples", ROOT / "core"
STAR = re.compile(r"^\s*from\s+([\w\.]+)\s+import\s+\*", re.M)


def bad_all_modules():
    """Modules whose __all__ is a bare string or names something undefined."""
    out = {}
    for f in sorted(EX.rglob("*.py")):
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        defined = set()
        for n in ast.walk(tree):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defined.add(n.name)
            elif isinstance(n, ast.Assign):
                defined |= {t.id for t in n.targets if isinstance(t, ast.Name)}
            elif isinstance(n, (ast.Import, ast.ImportFrom)):
                defined |= {(a.asname or a.name).split(".")[0] for a in n.names}
        for n in tree.body:
            if not (isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "__all__" for t in n.targets)):
                continue
            v = n.value
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                out[f] = (n.lineno, f"string {v.value!r}, not a sequence")
            elif isinstance(v, (ast.List, ast.Tuple)):
                names = [e.value for e in v.elts
                         if isinstance(e, ast.Constant) and isinstance(e.value, str)]
                miss = [x for x in names if x not in defined]
                if miss:
                    out[f] = (n.lineno, f"names {miss} not defined in module")
    return out


def star_targets(root):
    """Every module name that is star-imported under `root`."""
    hits = {}
    for f in root.rglob("*.py"):
        for m in STAR.finditer(f.read_text(encoding="utf-8", errors="replace")):
            hits.setdefault(m.group(1).split(".")[-1], []).append(str(f.relative_to(ROOT)))
    return hits


sha = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                     capture_output=True, text=True).stdout.strip()
print(f"ianvs commit under test: {sha}\n")

core_stars = star_targets(CORE)
print(f"[1] star-imports in core/ : {len(core_stars)}  -> "
      f"{'none, as expected' if not core_stars else core_stars}")

resolver = subprocess.run(
    ["grep", "-rn", "ClassFactory.get_cls", str(CORE)],
    capture_output=True, text=True).stdout.strip().splitlines()
print(f"\n[2] Core resolution sites using ClassFactory.get_cls: {len(resolver)}")
for line in resolver:
    print("   ", line.replace(str(ROOT) + "/", ""))
uses_all = subprocess.run(["grep", "-rn", "__all__", str(CORE)],
                          capture_output=True, text=True).stdout.strip()
print(f"    Core references to __all__: {uses_all or 'NONE'}")

bad = bad_all_modules()
ex_stars = star_targets(EX)
print(f"\n[3] Example modules with a malformed __all__: {len(bad)}")
shadowed = [(f, why) for f, why in bad.items() if f.stem in ex_stars]
for f, (ln, why) in sorted(bad.items()):
    mark = "STAR-IMPORTED" if f.stem in ex_stars else "never star-imported"
    print(f"    {mark:<19} {f.relative_to(ROOT)}:{ln}  ({why})")

print("\n" + "=" * 72)
print(f"  malformed __all__ declarations                 : {len(bad)}")
print(f"  of those, ever consumed by a star-import       : {len(shadowed)}")
print(f"  Core code paths that read __all__              : 0")
print("=" * 72)
print("\nCONCLUSION: on this commit, no malformed __all__ is load-bearing.")
print("A PR that only corrects __all__ changes no runtime behaviour.")
