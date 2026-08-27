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
