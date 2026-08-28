# Task 4 — Restoration Path Design

## 1. Problem Definition

### 1.1 Examples to restore, current state, blockers

Scope is the Examples whose failure is caused by the resolution contract of Tasks 1–3.

| Example | Current state | Blocker |
|---|---|---|
| `cloud-edge-collaborative-inference-for-llm` | **cannot import** | #568 — `edge_model.py:21` imports `LadeSpecDecLLM`, defined nowhere. Open PR #569. |
| `Cloud_Robotics/cloud-edge-collaborative-inference_bench` | runs; declaration wrong | #641 — inert `__all__`. Open PR #642. |
| `robot-cityscapes-synthia` (lifelong, ERFNet) | **cannot be run at all by anyone** | `testenv.yaml:5` → `/home/QXY/dataset/mdil-ss/...`; no published URL for `mdil-ss.zip`. Plus 1 unresolvable metric `url:`. |
| `robot`, `cityscapes-synthia` ×2, `bdd`, `cityscapes` | metric config unresolvable | 12 of the 31 broken `url:` entries |
| `MOT17/multiedge_inference_bench` | metric config unresolvable | 8 broken `url:` entries in two `testenv.yaml` |
| `RoboDK Palletizing`, `cloud_VLA_finetune` | absolute developer paths | 3 entries |
| **all Examples** | latent | #557 module identity. Open PR #558. |

**Excluded, with justification.** `imagenet/multiedge_inference_bench` is excluded from
the restoration path even though it carries 4 malformed `__all__`: its blocking defects
are ONNX-Runtime provider selection and a registration-gated 6.3 GB dataset, which belong
to a different root problem and are covered by other candidates this term.
`llm_simple_qa`, `government_rag` and `phys_scene_gen` are excluded as configuration-path
and dependency problems, not resolution-contract problems.

### 1.2 Why a structured order matters here

Two orderings are actively dangerous, and both look reasonable:

- **Fix the loader first (#558), then validate.** #558 changes module identity for 572
  Example modules. Landing it before a regression oracle exists means R4a's wrong-value
  behaviour and R4b's recoverability loss have nothing watching for them — which is
  exactly what happened: three reviewers, neither found.
- **Fix the 31 broken paths first.** Repairs today's instances and prevents none. The
  same drift produced them over multiple directory renames and will produce more.

The order below is chosen so that **every stage that changes behaviour is preceded by a
stage that can detect the change.**

### 1.3 Dependency graph

```text
                    S0  Baseline census + reproductions        [DONE, this submission]
                        31/87 url · 30 __all__ · 0 name-fail
                        loader collision reproduced
                                    |
                                    | provides the measurable "before" state
                                    | that every later gate compares against
                                    v
                    S1  Core: contract inspector  (new, ~30 lines, no behaviour change)
                        core/common/contract.py -- resolves config statically
                                    |
                                    | S2 needs something to call; S4 needs an oracle
                    +---------------+---------------+
                    |                               |
                    v                               v
      S2  CI: static validation job        S3a #569  fix #568 undefined import
          blocking: url/abs-path/name          (PARALLEL - Example-local, one file,
          advisory: __all__, collisions         no shared state, no Core API)
                    |                               |
                    |                       S3b #642 / #651  __all__ cleanup
                    |                           (PARALLEL - inert by construction,
                    |                            proven in Task 2 R2)
                    |                               |
                    |                       S3c #598  parse_kwargs  (#702 closed)
                    |                           (PARALLEL - unreachable code, R3)
                    |                               |
                    +---------------+---------------+
                                    |
                                    | S2 is now green and is the regression oracle
                                    v
                    S4  Core: specify module identity, THEN land #558
                        with R4a (transitive) and R4b (pickle) addressed
                                    |
                                    v
                    S5  Repair the 31 unresolvable url: entries
                        (safe last: S2 proves each one, S4 fixed identity)
```

Sequential edges: `S0→S1→S2→S4→S5`. Parallel nodes: `S3a`, `S3b`, `S3c` — disjoint file
sets, no shared state, no API contract change (§3.4).

## 2. Evidence

### 2.1 Per-blocker evidence and impact

| Blocker | Evidence (all executed at `37a9c60`) | Impact |
|---|---|---|
| #568 undefined import | `grep -rn LadeSpecDecLLM examples/` → 2 hits, both **uses**, zero definitions (`edge_model.py:21`, `:77`) | Example cannot be imported; `load_module()` raises before any dataset is touched |
| 31 unresolvable `url:` | `evidence/census_metric_urls.txt` | Metric resolution fails at run time in 12 Examples |
| 30 inert `__all__` | `evidence/probe_all_is_inert.txt` | **None.** Recorded so the path does not spend effort here |
| `parse_kwargs` | `evidence/probe_parse_kwargs_dead.txt` | **None.** Same reason |
| #557 module identity | `evidence/probe_load_module.txt` | Silent wrong results when two test cases share a basename |
| #558 R4a / R4b | `evidence/probe_pr558_transitive.txt`, `evidence/probe_pr558_pickle.txt` | Wrong value (active); lost recoverability (latent) |

### 2.2 Already addressed vs still missing

| Need | Existing work | Status | Gap |
|---|---|---|---|
| Undefined import in `edge_model.py` | **PR #569** | open | none — merge it |
| `__all__` in Cloud_Robotics | **PR #642** | open | none — merge as cleanup |
| `__all__` in 18 modules | **PR #651** | open | none — merge as cleanup |
| `parse_kwargs` | **PR #598**, #702 | open, duplicated | pick one, close the other |
| Module identity | **PR #558** | open | R4a and R4b unaddressed |
| `sys.path` leak (#728) | #729, #759, #806, **and #558 incidentally** | open ×4 | over-served; needs a decision, not more PRs |
| **Static contract validation** | **none** | — | **This is the missing fix.** No open PR in `#133`–`#851` resolves a config `url:`/`name:` against the code. #851 runs pylint and checks requirements-file presence; #744 validates YAML shape against a baseline. Neither resolves the registration contract. Verified against the full open-PR list in `evidence/gap_analysis.txt`. |
| **Repair of the 31 `url:` entries** | **none** | — | Missing. No open PR touches those `testenv.yaml` files. |

### 2.3 Counter-evidence and fallback for the critical fix

**Critical fix: S4 (#558).** What if it regresses?

*Failure mode.* The hashed `__name__` breaks something not covered by S2 — for instance
an Example that inspects `__name__`, or a `torch.load` of a checkpoint holding an
Example-defined class (same mechanism as R4b, different serialiser).

*How it surfaces.* S2 is static and would **not** catch it. This is a real limit of the
chosen boundary and I state it rather than paper over it: S2's oracle covers
config→registration resolution, not serialisation. The detection for S4 has to be the
differential probes in this submission, promoted into the test suite.

*Fallback.* `git revert` the single-file S4 commit. Nothing depends on it: S1/S2 do not
import `load_module`, S3a–c touch different files, S5 changes only YAML. The repository
returns to `main` semantics — collisions present but recoverability intact — which is a
strictly known state, not a worse one.

*Second fallback if reverting is not acceptable* (because collisions are then back):
keep `sys.modules` keyed uniquely but restore `mod.__name__` to the bare basename. This
retains the collision fix and removes R4b entirely. It does not fix R4a.

## 3. Path Design

### 3.1 Fix order and justification

| Stage | Action | Why here |
|---|---|---|
| S1 | Core contract inspector, no behaviour change | Must precede S2 — S2 has nothing to call otherwise. Safe to land first precisely because it changes nothing |
| S2 | CI validation job | Must precede S4 — it is S4's regression oracle. Also converts S5 from guesswork to a checklist |
| S3a | Merge #569 | Independent; unblocks an Example that currently cannot import |
| S3b | Merge #642, #651 as `kind/cleanup` | Independent; **proven inert** (R2), so cannot regress anything |
| S3c | Merge #598, close #702 | Independent; **proven unreachable** (R3) |
| S4 | Specify identity, then land #558 | Last of the behaviour-changing work, because it is the only one that can break every Example at once |
| S5 | Repair 31 `url:` entries | After S2 so each repair is verified, after S4 so identity is settled |

### 3.2 Critical path

`S0 → S1 → S2 → S4 → S5`. That is the minimum time-to-restoration; S3a–c can happen at
any point and shorten nothing. S3b and S3c are explicitly **deferrable**: Task 2 proved
neither changes runtime behaviour, so neither can restore an Example, and neither should
be allowed to consume review capacity ahead of S4.

That is the sharpest practical consequence of this whole analysis: **the four PRs that
look most reviewable are the four that matter least.**

### 3.3 Parallelisation

| Node | Files | Shared state | API contract |
|---|---|---|---|
| S3a #569 | `examples/cloud-edge-collaborative-inference-for-llm/.../edge_model.py` | none | none |
| S3b #642 | `examples/Cloud_Robotics/.../cloud_model.py` | none | none |
| S3b #651 | 18 `examples/**` metric modules | none | none |
| S3c #598 | `core/common/utils.py` (`parse_kwargs` only) | none | function is uncalled |

Disjoint paths except S3c and S4, which touch the same **file** but different
**functions** (`parse_kwargs` vs `load_module`). That is a textual merge risk, not a
semantic one; ordering S3c before S4 removes it.

### 3.4 Repair strategy outline

| Stage | Files | Expected behaviour change |
|---|---|---|
| S1 | `core/common/contract.py` (new) | **none** — pure function, reads config and parses source, imports nothing |
| S2 | `.github/workflows/example-contract.yaml` (new) | **none at run time**; 12 Examples begin failing CI on defects they already have |
| S3a | 1 Example file | Example becomes importable |
| S3b | 19 Example files | **none** (R2) |
| S3c | `core/common/utils.py` | **none** (R3) |
| S4 | `core/common/utils.py` | Module identity becomes path-unique; R4a and R4b must be closed first |
| S5 | ~12 `testenv.yaml` | Metric resolution succeeds where it currently raises |

### 3.5 Rollback per stage

| Stage | Gate failure action | Leaves Example worse? |
|---|---|---|
| S1 | revert; nothing imports it | no — dead code removed |
| S2 | set the job non-blocking (`continue-on-error`) rather than reverting; keep the signal | no — CI-only |
| S3a | revert one file → back to a known `ImportError` | no |
| S3b | revert → back to inert wrong metadata | no, provably (R2) |
| S3c | revert → back to uncalled buggy helper | no, provably (R3) |
| S4 | **`git revert` the single commit.** Collisions return; recoverability returns | no — returns to today's known state |
| S5 | revert individual YAML edits | no — each is independent |

No stage's rollback depends on another stage being rolled back. That is a property of the
order, not luck: the only stage with repository-wide blast radius (S4) is deliberately
last among behaviour-changing stages and touches one function in one file.

### 3.6 Cross-Example coordination

S4 is the only stage needing it. Concretely: land S2 first so all Examples are measured
under identical rules; announce S4 with a release note covering R4b's invariant; stagger
S4 behind at least one green S2 run on `main`.

## 4. Verification

### 4.1 Gates

| Gate | Command | Expected observable result | Failure condition |
|---|---|---|---|
| **G0** | `python3 tools/scan_metric_contract.py ianvs` | `56 OK · 28 missing file · 3 absolute · 0 name-fail` | any other counts ⇒ tree is not at `37a9c60` |
| **G0b** | `python3 tools/probe_all_is_inert.py ianvs` | `30 malformed · 0 star-imported · 0 core refs` | any star-import found ⇒ R2 is wrong; retract it |
| **G1** | `python3 tools/probe_load_module.py ianvs` | test case 2 reuses test case 1's module, no error | not reproduced ⇒ #557 is interpreter-specific; narrow the claim |
| **G2** | S1 inspector over all 48 `testenv*.yaml` | same counts as G0, produced by production code | divergence ⇒ inspector does not model the real resolver |
| **G3** | S2 job on `main` | fails, naming exactly the 31 entries from G0 | fewer ⇒ coverage gap; more ⇒ false positives, fix before blocking |
| **G4** | `python3 tools/probe_pr558_transitive.py ianvs` on the S4 branch | `example_B.predict(1) == 100` | still `1` ⇒ R4a unaddressed; do not merge |
| **G5** | `python3 tools/probe_pr558_pickle.py ianvs` on the S4 branch | `UNPICKLE (source dir on sys.path) = LOAD-OK` on both refs | FAIL on the branch ⇒ R4b unaddressed; require the release note |
| **G6** | re-run G0–G5 after **each** merged stage | all previously green gates stay green | any flip ⇒ revert that stage per §3.5, then diagnose |
| **G7** | S2 job after S5 | zero blocking findings | remaining findings ⇒ S5 incomplete |

### 4.2 Independent verification tied to a major finding

**G4 is tied to Task 2 R4a.** It is a differential test: identical fixture, two real git
refs (`main` `37a9c60`, `pr-558` `b99161f`) in isolated worktrees, executing the
unmodified `core.common.utils.load_module` from each. It currently returns `1` on the PR
branch where the Example's own helper returns `100`, and it will return `100` when R4a is
fixed. Anyone can run it: `python3 tools/probe_pr558_transitive.py ianvs`. It needs no
GPU, dataset, model, API key or network.

### 4.3 Incremental regression testing

G6 is the rule: after each stage passes its own gate, **all** earlier gates re-run. The
gates are cheap — the full G0–G5 sweep is static analysis plus four short subprocess
tests — so this is affordable per commit, not per release. Results are recorded in
`docs/progress/` alongside the stage that produced them.

### 4.4 Final success criteria

Restoration is **not** "the ImportError disappeared". It is all of:

1. G3 green — S2 reports zero blocking findings across all 48 `testenv*.yaml`.
2. G4 and G5 green on the S4 branch — the loader fix no longer trades one silent wrong
   answer for another.
3. `cloud-edge-collaborative-inference-for-llm` imports cleanly (S3a) — verifiable
   without any dataset.
4. The identity contract is **written down**, in `load_module()`'s docstring, including
   what may be placed in a persisted `task_index`.
5. Each Example's documented command path matches what S2 resolves — docs and config
   agree.
6. **Explicitly still out of reach, and named as such:** end-to-end benchmark results for
   `robot-cityscapes-synthia` (no published `mdil-ss.zip` URL) and
   `imagenet/multiedge_inference_bench` (gated 6.3 GB dataset + NVIDIA stack). Those
   require a maintainer to publish a dataset URL and a GPU runner. Restoration of the
   *contract* does not depend on them; restoration of those *Examples* does.

## 5. Uniqueness

Audited against all 70 prior Discussions (`evidence/gap_analysis.txt`).

**Novel dependency ordering.** The path deliberately places the highest-impact Core fix
(#558) **last** among behaviour-changing stages and the zero-impact PRs as deferrable
parallel work — the inverse of the natural priority. The justification is measured, not
stylistic: R2 and R3 prove #642/#651/#598/#702 cannot restore anything, and R4a proves
#558 can break something. No prior Discussion orders these PRs, and none argues for
deprioritising a PR on the grounds that its change is provably inert.

**Novel verification strategy.** Gates G4 and G5 are **differential tests across two real
git refs**, not assertions about one tree — the same fixture executed against `main` and
against the PR head, with the *difference* as the oracle. G5 additionally asserts a
property (recoverability) that is invisible in any single-ref test, which is precisely
why three capable reviewers of #558 did not see it.

**Different scope decision.** The missing fix identified in §2.2 is a *check*, not a
patch, and it is the only item in the path with no existing PR.

**Not claimed:** that #558 fixes the collision (established by @Omkeswani27, @Yash4616,
@Aryansingh-ai); that #729/#759/#806 duplicate each other (@Omkeswani27); that CI
validation is broadly desirable (#851, #744 and their Discussions).

---

## Correction — posted 2026-08-28

**§2.2 contains a factual error, which I am correcting rather than leaving to stand.**

That table says of "Static contract validation": *"existing work: **none** … No open PR in
`#133`–`#851` resolves a config `url:`/`name:` against the code."* The second half is
right; the first half is wrong, and the row was wrong to be there at all.

Corrected row:

| Need | Existing work | Status | Gap |
|---|---|---|---|
| Static **path** validation | `.github/workflows/validator/` **merged on `main`** via #771; also proposed again by open PRs **#835** and **#744** | shipped + duplicated | none — this is covered, and covered three times |
| Static **identifier** validation (`name:` → ClassFactory alias, `paradigm_type` → `ParadigmType`) | **none** | — | **this is the missing fix** |

The shipped validator is wired into `static_code_requirement_cicd.yaml` for `examples/**`
and implements `_check_repo_path_references` among five other checks. Run unmodified at
`37a9c60` it correctly fails `robot-cityscapes-synthia`, both `MOT17` inventory entries and
`Cloud_Robotics/…/perception-reasoning` on `Repository path references exist` — the same
breakage my §2.1 census counted. Credit to @Prachi194agrawal for surfacing it in the PR
#835 thread; I should have found it myself before writing §2.2.

**What this does to the path.** S2 becomes *extend the existing validator*, not *add a
job*. The dependency order is unchanged: S1 (a Core inspector that reports what would be
resolved) must still precede it, because the existing validator has no way to know what
the code registers.

**What this does to the "missing fix" claim.** It narrows it, and puts it on executed
evidence. Running the shipped validator:

```text
  [PASS] examples/yaoba/singletask_learning_boost        ERROR checks: none
  [PASS] examples/yaoba/singletask_learning_yolox_tta    ERROR checks: none
  [FAIL] examples/robot-cityscapes-synthia/...           ERROR: Repository path references exist
  [FAIL] examples/MOT17/.../pedestrian_tracking          ERROR: Repository path references exist
  [FAIL] examples/Cloud_Robotics/.../perception-reasoning ERROR: Repository path references exist
```

Both `yaoba` Examples pass every check the project currently runs, and neither can
execute — their `paradigm_type` matches no `ParadigmType` member, and dispatch has no
`else` clause. There are zero references to `ClassFactory`, `register`, `alias` or
`paradigm_type` under `.github/workflows/validator/`. (See the second correction below
for what Core itself does check.)

**A note on my own method.** I built a prior-art map over 86 Discussions and every open
target, and still missed a validator sitting in the tree I had checked out. The failure is
instructive for this submission's own thesis: I searched for *proposals* in the PR queue
and did not check what had already *merged*. Recording it here because a verification
boundary is worth nothing if it only covers the checks that happened to be run.


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
