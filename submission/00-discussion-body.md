# LFX 2026 Term 3 Example Restoration: problem analysis of Ianvs's unenforced Example interface contract

**Candidate:** henryng15
**Analysed commit:** `kubeedge/ianvs@37a9c60` (Merge PR #771, 2026-08-21)
**Root Problem anchored in:** #557, #597, #641, #568
**Mandatory PR set:** **#558** (critical, Ianvs Core), #651, #642, #598, #702

---

## The root problem in one file

`examples/cloud-edge-collaborative-inference-for-llm/testalgorithms/query-routing/edge_model.py`
declares its interface three times in seven lines. Ianvs treats each one completely differently:

```python
# line 21
from models import HuggingfaceLLM, APIBasedLLM, VllmLLM, EagleSpecDecModel, LadeSpecDecLLM
#                                                                          ^^^^^^^^^^^^^^
#   not defined anywhere in the repository  ->  ImportError, FATAL       (issue #568)

# line 25
__all__ = ["BaseModel"]
#          ^^^^^^^^^^^
#   not defined anywhere in this module     ->  no effect whatsoever     (this analysis)

# line 27
@ClassFactory.register(ClassType.GENERAL, alias="EdgeModel")
#                                               ^^^^^^^^^^^
#   the ONLY name Ianvs actually resolves   ->  authoritative, unvalidated
```

Three name declarations. One is fatal, one is silently dead, one is authoritative —
and nothing in the framework tells a contributor which is which.

> **Root Problem.** Ianvs has no enforced contract between the interface an Example
> *declares* and the interface Ianvs *resolves*. An Example declares itself through a
> config `url:` path, a config `name:` string, and Python module metadata (`__all__`,
> function signatures). Core resolves exactly one of those — the `name:` string, matched
> against a `ClassFactory` alias — validates none of them, and does so only when a
> benchmark run reaches the module. Everything off that path drifts unnoticed;
> everything on it fails late and without diagnosis.

This is not a stylistic complaint. It has a measurable cost that this submission
quantifies, reproduces, and traces into five open PRs — **three of which do not change
runtime behaviour at all**, while the one that does introduces an unreported regression.

---

## Task index

| Task | Comment |
|---|---|
| Task 1 — Root Problem Analysis | see comment 1 |
| Task 2 — Multi-PR Code Review | see comment 2 |
| Task 3 — Repair Boundary Analysis | see comment 3 |
| Task 4 — Restoration Path Design | see comment 4 |
| Bonus — Supplementary Review Coverage | see comment 5 |

## Evidence and verification boundary at a glance

Every probe below runs **unmodified production code** from the analysed commit and needs
no GPU, no dataset, no API key and no network. All are re-runnable from
[`henryng15/ianvs-lfx-pretest`](https://github.com/henryng15/ianvs-lfx-pretest).

| Evidence | Kind | Result |
|---|---|---|
| `__all__` is inert across 30 declarations | executed static census + code-path proof | 0 of 30 are load-bearing |
| `parse_kwargs` is unreachable | executed AST census + wheel inspection | 0 call sites in repo |
| #558 leaves transitive imports colliding | **executed differential test, main vs PR head** | Example B runs Example A's helper; wrong value |
| #558 removes pickle recoverability | **executed differential test, main vs PR head** | recoverable -> unrecoverable (latent; no shipped Example triggers it) |
| loader basename collision (#557) | executed reproduction of an existing issue | reproduced |
| testenv metric `url:` census | executed static resolution of every metric entry | 31 of 87 unresolvable |

**Boundary.** Full end-to-end benchmark runs for the affected Examples are *not*
claimed. `robot-cityscapes-synthia` cannot be run at all — its `testenv.yaml:5` points at
`/home/QXY/dataset/mdil-ss/...` and the repository publishes no download URL for
`mdil-ss.zip`. Where a claim is static, it is labelled static. No unexecuted check is
described as passed.

---

## Appendix — self-contained reproductions

Full tooling, raw output and progress notes:
[`github.com/henryng15/ianvs-lfx-pretest`](https://github.com/henryng15/ianvs-lfx-pretest).
The two checks below are inlined so nothing in this submission depends on that link.
Both need only a clone of Ianvs at `37a9c60` and a Python 3 with `PyYAML`.

### A1 — `__all__` is not read by Ianvs (Task 1 E1, Task 2 R2)

```bash
cd /path/to/ianvs && git rev-parse --short HEAD     # expect 37a9c60
grep -rn "__all__" core/            | wc -l         # expect 0
grep -rnE "^\s*from .* import \*" core/ | wc -l     # expect 0
grep -rn "ClassFactory.get_cls" core/               # the real resolution path
```

```python
# how many Example modules with a malformed __all__ are ever star-imported
import ast, pathlib, re
EX = pathlib.Path("examples")
star = {m.group(1).split(".")[-1]
        for f in EX.rglob("*.py")
        for m in re.finditer(r"^\s*from\s+([\w\.]+)\s+import\s+\*",
                             f.read_text(errors="replace"), re.M)}
bad = []
for f in EX.rglob("*.py"):
    try: t = ast.parse(f.read_text(errors="replace"))
    except SyntaxError: continue
    for n in t.body:
        if isinstance(n, ast.Assign) and any(
                getattr(x, "id", None) == "__all__" for x in n.targets):
            if isinstance(n.value, ast.Constant):        # a string, not a sequence
                bad.append(f)
print("malformed __all__:", len(bad),
      "| of those star-imported:", sum(f.stem in star for f in bad))
```

### A2 — PR #558 removes pickle recoverability (Task 2 R4b)

```bash
cd /path/to/ianvs
git fetch --depth=1 origin pull/558/head:pr-558
```

```python
# run once per ref; `ref` selects which load_module implementation is exercised
import pickle, subprocess, sys, tempfile, pathlib, textwrap
ref = sys.argv[1]                                    # "main" or "pr-558"
wd = pathlib.Path(tempfile.mkdtemp())
subprocess.run(["git", "worktree", "add", "-q", "--detach", str(wd/"t"), ref], check=True)
src = wd/"ex"; src.mkdir()
(src/"taskdef.py").write_text(
    "class TaskDefinitionByDomain:\n"
    "    def __init__(self, d): self.d = d\n")
sys.path.insert(0, str(wd/"t"))
from core.common.utils import load_module
load_module(str(src/"taskdef.py"))
mod = next(m for n, m in sys.modules.items() if n.startswith("taskdef"))
print("__module__ recorded by pickle:", mod.TaskDefinitionByDomain.__module__)
pickle.dump(mod.TaskDefinitionByDomain("Cityscapes"), open(wd/"ti.pkl", "wb"))
# now, in a FRESH interpreter, with the source dir on sys.path:
#   sys.path.insert(0, "<wd>/ex"); pickle.load(open("<wd>/ti.pkl","rb"))
#   main    -> loads
#   pr-558  -> ModuleNotFoundError: No module named 'taskdef_<md5>'
```

Observed: `main` records `taskdef` and reloads; `pr-558` records
`taskdef_<md5 of the absolute path>`, which names no file on disk, so no `sys.path`
manipulation recovers it. The md5 also changes with the checkout directory.
