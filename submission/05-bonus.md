# Bonus — Supplementary Review Coverage

Five additional open PRs, none in my Task 2 mandatory set, none authored by me, all open
and non-draft, all within `#133`–`#851`, all verified against `37a9c60`.
**Four of the five have no review at all.** Every finding below was checked by running or
reading the code, and each is cross-posted to its own PR as target-specific content.

| PR | Head | Existing reviews | Recommendation | Finding in one line |
|---|---|---|---|---|
| [#617](https://github.com/kubeedge/ianvs/pull/617) | `aba3a41` | **0** | accepted as it is | Deletion is correct — and it makes permanent the fact that **two shipped Examples can never run** |
| [#569](https://github.com/kubeedge/ianvs/pull/569) | `84c441f` | 1 | minor revision | Fixes the fatal wrong name on line 21 and leaves the inert wrong name on line 25 |
| [#739](https://github.com/kubeedge/ianvs/pull/739) | `900ae72` | **0** | minor revision | Its own comment states a constraint the change does not encode |
| [#632](https://github.com/kubeedge/ianvs/pull/632) | `ef4d9ec` | **0** | accepted as it is | Correct — here is the proof of deadness the PR does not provide |
| [#540](https://github.com/kubeedge/ianvs/pull/540) | `a49061f` | 2 | minor revision | Silently substitutes a hand-rolled attention implementation into a *performance* benchmark |

---

## Cross-target finding — the same defect on a fifth contract surface

Reviewing **#617** surfaced an instance of the Task 1 Root Problem that I had not
measured, on a surface I had not examined: `paradigm_type`.

#617 deletes `singletask_learning_active_boost.py` and `singletask_learning_tta.py` from
Core as unused. That is correct — but *why* they are unused is the interesting part:

```text
ParadigmType (core/common/constant.py:33-44) admits exactly 7 values:
  singletasklearning · incrementallearning · multiedgeinference · lifelonglearning
  federatedlearning  · federatedclassincrementallearning · jointinference

Declared by shipped Examples but absent from that enum:
  'singletasklearning_tta'      examples/yaoba/singletask_learning_yolox_tta/testalgorithms/algorithm.yaml:6
  'singletasklearning_acboost'  examples/yaoba/singletask_learning_boost/testalgorithms/algorithm.yaml:5
```

`base.py:95-152` and `algorithm.py:109-127` dispatch through seven `if` comparisons with
**no `else`**. An unrecognised `paradigm_type` matches none of them and the function
returns `None` — no exception, no log line, no validation at config-parse time.

This is the identical pattern Task 1 documents for `url:`, `name:` and `__all__`, now on
a fourth declaration surface and a **fifth** distinct one if module identity is counted.
`examples/yaoba/singletask_learning_boost` and `examples/yaoba/singletask_learning_yolox_tta`
are therefore not merely un-run — they are **unrunnable**, and have been since the enum
and the YAML diverged. Nothing in the repository reports it.

**Consequence for #617 specifically:** the PR is right to delete the dead Core files, but
it should say what it is really doing — retiring two Examples — rather than describing it
as a cleanup of "unused paradigm files". Either the two `yaoba` Examples get their enum
entries back, or they should be retired explicitly and their READMEs marked. Silently
deleting the only code that could ever have served them is the one option that leaves no
trace.

---

## Individual reviews

### #617 — `cleanup(core): remove unused paradigm files tightly coupled to examples`

**Verification.** Both deleted files define classes (`SingleTaskLearningACBoost`,
`SingleTaskLearningTTA`) referenced by **0** other files in `core/` or `examples/`, and
by no `ParadigmType` member. Both also import *upward* from `examples.yaoba...` into
`core/` — a layering inversion that alone justifies the removal.

**Recommendation: accepted as it is**, with the cross-target note above added to the PR
description so the Example-retirement consequence is on the record.

### #569 — `fix: remove undefined LadeSpecDecLLM import from edge_model`

**Verification.** `LadeSpecDecLLM` appears exactly twice in the repository
(`edge_model.py:21` and `:77`), both **uses**, zero definitions —
so #568 is real and this fix resolves it. The removed `values:` entry was
already absent from `test_queryrouting.yaml`, and `EagleSpecDec` there is commented out,
so no reachable configuration is lost.

**Finding.** After this PR, `edge_model.py` still reads:

```python
# line 21 (fixed by this PR)
from models import HuggingfaceLLM, APIBasedLLM, VllmLLM, EagleSpecDecModel

# line 25 (untouched)
__all__ = ["BaseModel"]      # this module defines EdgeModel, not BaseModel
```

Two names that do not exist, four lines apart. This PR removes the one that raises and
leaves the one that does not — which is exactly right as engineering triage, and exactly
the asymmetry Task 1 describes. Worth one extra line in the same PR.

**Second point.** Issue #568 asks for "a missing/optional speculative-decoding backend"
to be handled. This PR *deletes* the backend rather than making it optional. Given the
class was never implemented, deletion is defensible — but it diverges from the issue's
stated expectation and the PR should say so, so the issue can be closed accurately.

**Recommendation: minor revision.** No coding effort — a description note plus, ideally,
the one-line `__all__` correction.

### #739 — `fix(examples): remove protobuf<=3.20.3 pin conflicting with core onnx`

**Verification.** `run_ianvs.sh` does not exist anywhere under
`examples/industrialEI/` (`find` returns nothing), so removing the comment referencing it
is correct.

**Finding.** The PR replaces `protobuf<=3.20.3` with a bare, unconstrained `protobuf`,
while its own added comment states:

> must stay compatible with onnx (installed by core ianvs), which requires `protobuf>=4.25.1`

The constraint is written in a comment and not in the requirement. A resolver may still
select protobuf 3.x here — the very situation the PR exists to prevent. If the stated
bound is correct, encode it: `protobuf>=4.25.1`.

**Compounding.** The root `requirements.txt:7` pins `onnx` with **no** version at all, so
which protobuf onnx demands is itself unpinned. Documenting a floor derived from an
unpinned dependency is fragile. Repository-wide, 302 of 536 Example requirement lines
carry no version constraint.

**Recommendation: minor revision** — change one line to `protobuf>=4.25.1`.

### #632 — `cleanup: remove dead code in JointInference.set_config()`

The PR replaces

```python
source = self.dataset.test_url if hasattr(self.dataset, 'test_url') else self.dataset.test_data_info
```

with `self.dataset.test_url` directly. It asserts the fallback is dead but provides no
evidence, and a reviewer cannot accept "removes a defensive branch" on assertion alone.

**Verification supplied.** `core/testenvmanager/dataset/dataset.py:46` sets
`self.test_url: str = ""` unconditionally in `__init__`, so `hasattr(self.dataset,
'test_url')` is **always** `True` on any `Dataset` instance. Lines 168-175 then assign it
from `test_index`, `test_data` or `test_data_info`, or raise `NotImplementedError`. The
`else` branch is therefore unreachable, and — because the original used `hasattr` rather
than truthiness — an empty `test_url` behaved identically before and after.

**Recommendation: accepted as it is.** The change is correct; the reasoning above is what
was missing from the PR.

### #540 — `fix(examples): add backwards-compatible fallback for transformers>=5.0 in ViT/DeiT`

**Verification.** `transformers>=5.0` removed `ViTIntermediate`, `ViTOutput`,
`ViTSelfAttention` and `ViTSelfOutput` from `transformers.models.vit.modeling_vit`, so
the current unguarded import raises `ImportError`. The PR wraps it in `try/except
ImportError` and, in the fallback, re-implements those four classes locally (~65 lines);
`deit.py` is repointed at `.vit` so both share one definition.

**Finding — silent substitution in a performance benchmark.** The fallback emits no
warning and records nothing in the benchmark output. A user on `transformers>=5.0` runs
`imagenet/multiedge_inference_bench` and silently measures a hand-rolled attention
implementation rather than the library's — which is precisely what the benchmark exists
to measure. The two paths are also not guaranteed to stay numerically equivalent as
upstream evolves, and nothing pins which one ran.

Minimum fix: a `LOGGER.warning` in the `except` branch, and the resolved implementation
recorded in the run's metadata. That keeps the fix and removes the silence.

**Second point.** `ViTEmbeddings` is imported from `transformers` in **both** branches. If
a future release removes that too, the fallback raises from inside its own handler.
A nested guard or an explicit supported-version range would be more durable.

**Recommendation: minor revision.** The compatibility direction is right and worth
merging; the silence is the objection.

---

## Qualification and uniqueness

All five PRs are open, non-draft, in range, not authored by me, and distinct from my
Task 2 set (#558, #651, #642, #598, #702). Each was checked against the full prior-art
coverage map built in Task 1 (`tools/build_coverage.py`, `evidence/gap_analysis.txt`):
**none of the five is cited by any of the 70 prior LFX Term 3 Discussions**, and four of
the five have no review of any kind.

| Finding | Prior art | Verdict |
|---|---|---|
| `paradigm_type` accepts unregistered values; 2 `yaoba` Examples are unrunnable | none | **new** |
| #569 leaves the inert bad name beside the fatal one it fixes | none | **new** |
| #739 documents a floor it does not encode | none | **new** |
| #632's removed branch is provably unreachable via `dataset.py:46` | none | **new evidence** for an unreviewed PR |
| #540 silently substitutes an attention implementation into a perf benchmark | none | **new** |

**Verification boundary.** All five reviews are static: code paths, symbol resolution,
enum membership and dependency metadata, at `37a9c60` and at each PR head. **No PR here
was executed end-to-end.** #540's fallback in particular is reviewed by reading — I did
not install `transformers>=5.0` and run `imagenet/multiedge_inference_bench`, which
additionally needs a registration-gated 6.3 GB dataset and an NVIDIA CUDA/ONNX-Runtime
stack. Nothing above is described as passing a test that was not run.

---

## Update — 2026-08-28: the `paradigm_type` gap, now executed

The cross-target finding above was static. It is now backed by running the validator that
**already ships on `main`** at `37a9c60` (`.github/workflows/validator/`, merged via #771,
wired into `static_code_requirement_cicd.yaml` for `examples/**`):

```text
  [PASS] examples/yaoba/singletask_learning_boost        ERROR checks: none  WARNING: 1
  [PASS] examples/yaoba/singletask_learning_yolox_tta    ERROR checks: none  WARNING: 2
  [FAIL] examples/robot-cityscapes-synthia/...           ERROR: Repository path references exist
  [FAIL] examples/MOT17/.../pedestrian_tracking (x2)     ERROR: Repository path references exist
  [FAIL] examples/Cloud_Robotics/.../perception-reasoning ERROR: Repository path references exist
```

Reproduce: `python3 tools/run_shipped_validator.py ianvs`.

Both Examples that PR #617 retires **pass every check the project runs**, and neither can
execute: their `paradigm_type` values (`singletasklearning_acboost`,
`singletasklearning_tta`) are absent from `ParadigmType`, and Core raises `ValueError: not support paradigm(...)` when it reaches them; see the second correction below.

The validator has zero references to `ClassFactory`, `register`, `alias` or
`paradigm_type`. It resolves paths, not identifiers. That is the precise shape of the gap,
and it is why #617's deletion should be described as retiring two Examples rather than as
removing unused files — nothing in CI will ever report their absence.

*(This update also corrects a claim in my Task 3 and Task 4 comments, where I wrote that no
static config validation existed. It does, it is merged, and it works for paths. See the
Correction sections there.)*


---

## Second correction — posted 2026-08-28, after installing Ianvs and running it

**I got the mechanism wrong in the update above, and I am fixing it with an executed run
rather than another static reading.**

I wrote that dispatch "has no `else`, so the call returns `None` — no exception, no log
line, no validation at config-parse time." **That is false.**
`core/testcasecontroller/algorithm/algorithm.py:140-143` validates `paradigm_type` against
the enum and raises. It is called from `_parse_config` at line 167, long before the
dispatch chain I was reading is reached.

Installed Ianvs (`pip install -r requirements.txt` plus the bundled
`sedna-0.6.0.1` wheel) and ran it:

```text
ianvs commit under test: 37a9c60

1. ianvs CLI on examples/yaoba/singletask_learning_boost
   exit code: 1
   RuntimeError: benchmarkingjob runs failed, error: prepare dataset failed,
   error: not one of train_index/train_data/train_data_info..

2. Algorithm(...) -- where paradigm_type is validated
   yaoba acboost: paradigm_type='singletasklearning_acboost'
      -> ValueError: not support paradigm(singletasklearning_acboost).
         the following paradigms can be selected: ['singletasklearning', ...]
   yaoba tta:     paradigm_type='singletasklearning_tta'
      -> ValueError: not support paradigm(singletasklearning_tta). ...
   valid control: paradigm_type='singletasklearning'
      -> constructed, no error
```

Reproduce: `python3 tools/probe_paradigm_runtime.py ianvs`.

**Corrected statement of the finding.** Two things I claimed are confirmed, one is retracted:

| Claim | Verdict |
|---|---|
| Both `yaoba` Examples are unrunnable | **confirmed** — the CLI exits 1, and `Algorithm(...)` raises on the paradigm |
| The shipped CI validator reports **PASS** for both | **confirmed** |
| Core validates `paradigm_type` silently / returns `None` | **RETRACTED — Core validates it correctly and loudly** |

The run also shows the Examples fail *even earlier* than the paradigm check, at dataset
preparation (`not one of train_index/train_data/train_data_info`), so they are broken in at
least two independent ways.

**What the finding actually is, now that it is measured.** The gap is not that Ianvs fails
to validate identifiers — Core validates them, with a good error message that even lists
the valid values. The gap is that **CI and Core validate different things, and CI's set is
the smaller one.** `ParadigmType` is right there in `core/common/constant.py`; the
validator under `.github/workflows/validator/` never consults it, so two Examples pass
every check the project runs and fail immediately when actually executed.

That is a narrower claim than the one I published, and it is a better one: it names the
information that already exists in the tree and is simply not wired into the check. It is
also exactly Step 1 of my Task 3 repair strategy — have Core expose what it would resolve,
so the existing validator can consult it — which I can now say is a small change rather
than a new subsystem.

**On my own method, again.** This is my second correction on this submission. Both came
from the same habit: reading a dispatch chain and inferring behaviour instead of running
it. The first correction I found by reading someone else's review; this one I found by
finally installing the framework. The submission's own thesis is that unvalidated
declarations drift until something executes them — which turns out to apply to my
analysis as well as to the repository's configs.
