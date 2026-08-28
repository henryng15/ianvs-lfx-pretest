# Task 1 — Root Problem Analysis

**Analysed commit:** `37a9c60` · all targets re-checked open and in range before posting.

## 1. Problem Definition

### 1.1 Selected Existing Issues

| Issue | Layer | Example(s) affected | Surface symptom |
|---|---|---|---|
| [#568](https://github.com/kubeedge/ianvs/issues/568) | Example | `cloud-edge-collaborative-inference-for-llm` | `edge_model.py:21` imports `LadeSpecDecLLM`, which is defined nowhere — hard `ImportError` |
| [#641](https://github.com/kubeedge/ianvs/issues/641) | Example | `Cloud_Robotics/cloud-edge-collaborative-inference_bench` | `cloud_model.py:23` exports `QwenSemanticSegmentation` in `__all__`; the module defines `CloudModel` |
| [#557](https://github.com/kubeedge/ianvs/issues/557) | **Ianvs Core** | every Example | `load_module()` keys `sys.modules` by bare basename, so a second file with the same name is silently never loaded |
| [#597](https://github.com/kubeedge/ianvs/issues/597) | **Ianvs Core** | none, in fact | `parse_kwargs()` discards keyword-only parameters |

Four issues, four different reported symptoms. Each has been treated as an isolated
defect. They are four readings of the same instrument.

### 1.2 Why identifying this as the root problem matters

An Ianvs Example is not a program that Ianvs calls. It is a set of **strings in YAML that
Ianvs turns into code at runtime**: a `url:` naming a file, a `name:` naming a class. The
framework's entire coupling to an Example passes through two lines:

```python
# core/testcasecontroller/metrics/metrics.py:172-175
load_module(url)
metric_func = ClassFactory.get_cls(type_name=ClassType.GENERAL, t_cls_name=name)
```

Nothing type-checks this. Nothing validates it at config-parse time. Nothing warns when
two Examples claim the same alias. The consequence is a repository where **the declared
interface and the resolved interface have drifted apart**, and where contributors cannot
tell which is which — because the framework gives no signal either way.

That matters more for Ianvs than for an ordinary framework. Ianvs is a *benchmarking*
tool. Its output is a leaderboard that people use to compare algorithms. A defect that
makes a run crash is cheap: someone notices. A defect that makes a run produce a
confident, wrong number is expensive, and this contract produces exactly that class of
defect (§3.2).

### 1.3 The Examples involved

- **`cloud-edge-collaborative-inference-for-llm`** — query-routing algorithms; `edge_model.py`
  carries a fatal undefined import *and* a dead `__all__`, seven lines apart.
- **`Cloud_Robotics/cloud-edge-collaborative-inference_bench`** — perception-reasoning;
  `cloud_model.py` exports a name that does not exist.
- **`imagenet/multiedge_inference_bench`**, **`MOT17/multiedge_inference_bench`**,
  **`robot-cityscapes-synthia`**, **`cityscapes-synthia`**, **`bdd`**, **`pcb-aoi`**,
  **`RoboDK Palletizing`**, **`cityscapes`**, **`robot`** — all carry malformed `__all__`
  and/or collide on module basenames.

## 2. Evidence

All commands below were executed against `37a9c60`. Scripts, raw output and re-run
instructions: [`henryng15/ianvs-lfx-pretest`](https://github.com/henryng15/ianvs-lfx-pretest).
Each probe imports the **unmodified** production helper — no stubs, no monkey-patching.

### E1 — `__all__` is declared 134 times, malformed 30 times, and load-bearing 0 times

`tools/probe_all_is_inert.py` → `evidence/probe_all_is_inert.txt`

```text
ianvs commit under test: 37a9c60

[1] star-imports in core/ : 0  -> none, as expected

[2] Core resolution sites using ClassFactory.get_cls: 3
    core/testcasecontroller/metrics/metrics.py:173
    core/testcasecontroller/algorithm/module/module.py:116
    core/testcasecontroller/algorithm/module/module.py:130
    Core references to __all__: NONE

[3] Example modules with a malformed __all__: 30
    ... 30 lines, every one marked "never star-imported" ...

========================================================================
  malformed __all__ declarations                 : 30
  of those, ever consumed by a star-import       : 0
  Core code paths that read __all__              : 0
========================================================================
```

`__all__` changes behaviour only under `from <module> import *`. Core never does that,
and no Example star-imports any of the 30 modules. **Impact:** 30 declarations across
10 Examples are free to say anything at all, and #641 is the visible tip of that.

![Executed terminal output — E1: __all__ census](https://raw.githubusercontent.com/henryng15/ianvs-lfx-pretest/e7685be/evidence/screenshots/shot-task1-e1.png)

### E2 — `parse_kwargs` is defined once and called never

`tools/probe_parse_kwargs_dead.py` → `evidence/probe_parse_kwargs_dead.txt`

```text
[1] Call sites of core.common.utils.parse_kwargs
    definitions : ['core/common/utils.py:46']
    invocations : NONE
    imports of the helper: NONE

[2] Sedna wheel
    Sedna defines its own parse_kwargs at : ['sedna/backend/base.py:47']
    Sedna call sites                      : 14
    Sedna imports from core.common.utils  : NO

[3] Reported behaviour (issue #597)
    parse_kwargs(positional, threshold=0.9) -> {'threshold': 0.9}
    parse_kwargs(kwonly,     threshold=0.9) -> {}
```

The defect #597 reports is real — confirmed by execution. Its blast radius is zero.
**Impact:** #597 states the bug causes hyperparameters to be silently dropped for
Examples. On this commit it cannot, because no Example reaches the function. Sedna,
which *does* filter hyperparameters this way, ships its own copy.

![Executed terminal output — E2: parse_kwargs call-site census](https://raw.githubusercontent.com/henryng15/ianvs-lfx-pretest/e7685be/evidence/screenshots/shot-task1-e2.png)

### E3 — the loader collision is reproducible on production code

`tools/probe_load_module.py` → `evidence/probe_load_module.txt`

```text
--- test case 1: load_module(example_A/testenv/accuracy.py) ---
  sys.modules['accuracy'].EXAMPLE_ID = example_A
  accuracy(None, None)               = 0.11

--- test case 2: load_module(example_B/testenv/accuracy.py) ---
  sys.modules['accuracy'].EXAMPLE_ID = example_A      <-- B's file, A's code
  accuracy(None, None)               = 0.11

  test case 2 got the SAME module object as test case 1 : True
  test case 2 actually loaded its own file              : False
  load_module() raised no error                        : True
```

This reproduces **existing issue #557** and is presented as corroborating evidence, not
as a discovery. What is new here is its measured scale:

| basename | distinct files carrying it |
|---|---|
| `basemodel.py` | **41** |
| `accuracy.py` | **13** |
| `acc.py` | **12** |
| `utils.py`, `train.py` | 10 each |

392 of 572 Example `.py` files share a basename with at least one other file.
`TestCaseController.run_testcases()` (`testcasecontroller.py:46-61`) runs every test case
sequentially **in one interpreter**, which is precisely the condition this needs.
**Impact:** a `benchmarkingjob.yaml` comparing two algorithms whose implementations are
both called `basemodel.py` benchmarks the first one twice and reports it as two rows.

### E4 — 31 of 87 testenv metric declarations cannot resolve

`tools/scan_metric_contract.py` → `evidence/census_metric_urls.txt`

| Outcome for a testenv metric entry declaring a `url:` | Count |
|---|---|
| resolves correctly | 56 |
| `url:` file **does not exist** | **28** |
| `url:` is an absolute developer path | **3** |
| `name:` not registered by the module at `url:` | 0 |

The 28 are directory-rename drift, e.g. `robot-cityscapes-synthia/.../testenv.yaml`
points at `./examples/class_increment_semantic_segmentation/...`, a directory that does
not exist. The 3 absolute paths are `/root/ianvs/project/ianvs-0.3.0/...` and
`/inspire/hdd/global_user/chaimingxu-240108540141/...`.

**Impact, and the reason this number is interesting:** the `name:`→registration column is
**0**. The half of the contract that Core resolves is intact. The half nothing checks —
the path — is broken 36 % of the time. That asymmetry *is* the root problem, measured.

## 3. Analysis

### 3.1 Is the root problem Example-specific, shared-dependency, or Core-related?

**Core-related, with Example-visible consequences.** The mechanism lives in three Core
functions — `core/common/utils.py:load_module()`, `metrics.py:get_metric_func()` and
`module/module.py:get_module_instance()`. No Example can fix it locally, and every
Example inherits it. But it is *not* a Core bug in the ordinary sense: each of those
functions does what it was written to do. What is missing is a **specification** of what
an Example is allowed to declare and when that declaration is checked.

### 3.2 Are the issues identical, related, or independent?

**Related, and the relationship is the finding.** Sort them by where they sit relative to
the resolution path:

| Issue | Position | Enforcement | Failure mode |
|---|---|---|---|
| #568 | **on** the path (a real Python import) | immediate | fatal `ImportError` — Example cannot start |
| #557 | **on** the path (module identity) | none | **silent wrong result** |
| #641 | **off** the path (`__all__`) | none | none — inert |
| #597 | **off** the path (unreachable code) | none | none — inert |

Issues #568 and #641 are near-identical in *form*: a module names a symbol that does not
exist. One kills the Example; the other does nothing. The difference is not severity of
the mistake — it is whether the declaration happens to lie on the resolution path.

That is why treating these as four independent bugs produces the pattern visible in the
open PR queue today (Task 2): #642 and #651 carefully repair the inert half, #598 and
#702 carefully repair unreachable code, and the one PR touching the live path (#558)
carries an unreviewed regression. Effort is flowing to the declarations that are easiest
to see, not the ones that are load-bearing.

### 3.3 Would fixing them separately cause duplicated changes or inconsistent behaviour?

It already has, and the duplication is measurable in the open queue:

- **#598 and #702** fix the *same* issue #597 in the *same* function, independently.
- **#729, #759 and #806** fix the *same* issue #728 in the *same* function, independently
  — and **#558 fixes it too**, incidentally, in its `finally:` block. Four PRs, one
  14-line function, no coordination.
- **#642 and #651** both correct `__all__`, in different Examples, by different
  conventions, neither aware of the other.

Inconsistent behaviour follows from the same cause. `load_module()` is the only place
module identity is decided; #558 changes that decision for directly loaded files only.
Modules those files import themselves still resolve by bare name (§Task 2, R4), so after
#558 the repository would have **two** module-identity rules operating at once.

## 4. Uniqueness

70 LFX Term 3 Discussions were published before this one. I fetched all of them with
their comment bodies and built a coverage map of every Issue/PR each cites
(`tools/fetch_discussions.py`, `tools/build_coverage.py`, `evidence/gap_analysis.txt`).
That audit is why this submission is not about `use_gpu`: that angle is held by
[#856](https://github.com/kubeedge/ianvs/discussions/856),
[#875](https://github.com/kubeedge/ianvs/discussions/875) and
[#928](https://github.com/kubeedge/ianvs/discussions/928), the earliest five days ahead of me.

Explicit comparison for every claim I make here:

| Claim | Prior art | What is new |
|---|---|---|
| `load_module()` collides on basenames | **Issue #557**; Discussions #878, #900, #903, #909 | Nothing. Used as shared evidence, credited, **not claimed**. |
| ClassFactory aliases collide across Examples | Discussion [#903](https://github.com/kubeedge/ianvs/discussions/903) (@Yash4616) | Nothing. Credited; my analysis takes it as established. |
| **Core never reads `__all__`, so `__all__` repairs are inert** | **none of the 70** | Full finding: code-path proof + 30-declaration census + 0 star-imports. |
| **`parse_kwargs` is unreachable, so #597/#598/#702 have zero Example impact** | one Discussion (#899) mentions the name; none makes this claim | Full finding, with call-site census and Sedna wheel inspection. |
| **The enforcement asymmetry is the root cause, not any single defect** | none | The framing itself, evidenced by the 31/87 vs 0/87 asymmetry in E4. |

The strongest single new item is in Task 2 — a demonstrated regression in #558 that none
of its three existing reviewers found — and it is stated there rather than duplicated here.

**Honest limitation.** #557 and its PR cluster are well-trodden ground; I claim no
novelty on the mechanism and cite the candidates who established it. My contribution is
the layer above: *why* four differently-shaped issues keep appearing, and why the
repository's current repair effort is landing mostly on declarations that do nothing.
