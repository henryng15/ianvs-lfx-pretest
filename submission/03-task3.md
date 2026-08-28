# Task 3 — Repair Boundary Analysis

## 1. Problem Definition

### 1.1 The common problem and the Examples involved

Tasks 1–2 established one defect shape appearing at three positions relative to Ianvs's
runtime resolution path:

| Position | Declaration | Enforcement today | Examples carrying a broken instance |
|---|---|---|---|
| **On** the path | `@ClassFactory.register(alias=…)` ⟷ YAML `name:` | resolved at run time, unvalidated | all (0 broken today — see E4) |
| **On** the path | YAML `url:` → file | opened at run time, unvalidated | 12 Examples, 31 of 87 entries broken |
| **On** the path | module identity in `sys.modules` | none | every Example with a colliding basename (392 of 572 files) |
| **Off** the path | `__all__` | none | 10 Examples, 30 declarations |
| **Off** the path | unreachable helpers | none | 0 — `parse_kwargs` |

At least two Examples, as required, and in fact ten:
`cloud-edge-collaborative-inference-for-llm` (#568),
`Cloud_Robotics/cloud-edge-collaborative-inference_bench` (#641),
`robot-cityscapes-synthia`, `cityscapes-synthia`, `robot`, `bdd`, `cityscapes`,
`imagenet/multiedge_inference_bench`, `MOT17/multiedge_inference_bench`, `pcb-aoi`,
`RoboDK Palletizing`.

### 1.2 Why the boundary decision matters here

The consequences of getting it wrong are not hypothetical — both are already visible in
the open queue:

- **Boundary too low (Example-local).** Five contributors independently produced #598,
  #702, #729, #759 and #806 for two Core issues, and #642 and #651 for one Example
  surface, none referencing another. Repair effort is being spent proportional to how
  easy a defect is to *see*, and `__all__` is the easiest thing in the repository to see.
- **Boundary too high (Core).** #558 is the correct layer and still carries two
  demonstrated regressions (Task 2 R4a, R4b) affecting six lifelong-learning Examples,
  because one function's semantics changed for 572 modules at once.

### 1.3 Scope: layers considered

| Layer | In scope | Justification |
|---|---|---|
| Example-local | **yes** | where 21 of 22 changed files in the mandatory set sit |
| Shared utility | **yes** | the natural home for a resolution helper shared by Examples |
| Ianvs Core | **yes** | owns `load_module`, `get_metric_func`, `get_module_instance` |
| CI / Validation | **yes** | the only layer that can act *before* a run reaches the module |
| Dependency / Packaging | **excluded** | The defects here are internal name resolution. No requirement pin, wheel version or install order changes whether `__all__` is read or whether a `url:` exists. Version drift is a real Ianvs problem (302 of 536 Example requirement lines are unconstrained) but it is a different root problem and belongs to a different submission. |

## 2. Evidence

Each item below has its impact on the affected Examples stated. All executed at
`37a9c60`; scripts and raw output in
[`henryng15/ianvs-lfx-pretest`](https://github.com/henryng15/ianvs-lfx-pretest).

| # | Evidence | Impact |
|---|---|---|
| E1 | `core/` contains **0** references to `__all__` and **0** star-imports; 30 malformed `__all__` exist across 10 Examples, **0** star-imported | Repairing `__all__` in any Example changes nothing at run time. An Example-local boundary here produces motion without effect. |
| E2 | `parse_kwargs` has **0** call sites; Sedna ships its own at `sedna/backend/base.py:47` with 14 call sites | A Core fix here also changes nothing. Boundary choice is irrelevant until the function is either called or deleted. |
| E3 | **31 of 87** testenv metric `url:` entries do not resolve; **0 of 87** `name:` entries fail to resolve | The half of the contract Core resolves is intact; the half nothing checks is 36 % broken. **The determining evidence:** the difference between the two columns is not the layer, it is whether anything checks. |
| E4 | `load_module()` keys `sys.modules` by basename; `basemodel.py` ×41, `accuracy.py` ×13, `acc.py` ×12; 392 of 572 files collide | No Example can fix this locally. Genuinely Core. |
| E5 | #558 fixes E4 for directly loaded files only; sibling imports still collide, and pickled task indexes become unrecoverable | A Core fix at this layer has repository-wide blast radius, demonstrated on 6 lifelong-learning Examples. |

**Is there a common root problem, or are these genuinely Example-local?** E3 answers it.
If the defects were Example-local, the two columns would fail at similar rates — each
Example would be independently sloppy about both. They do not: 36 % versus 0 %. Examples
are not less careful about paths than about names; the framework checks one and not the
other. The cause is in the framework.

## 3. Scope Decision

### 3.1 Boundary determination

> **The fix belongs at the CI / Validation layer, with a narrowly scoped Core change to
> make validation possible — and explicitly *not* at the Example-local or shared-utility
> layer.**

This is a deliberately unusual answer, so here is each alternative and why it loses.

| Layer | Verdict | Why |
|---|---|---|
| **Example-local** | **rejected as primary** | Cannot reach E4 (module identity is Core). For E1/E2 it is *effective but pointless* — the changed declaration is not read. It is where the effort is going today, and it is producing #598/#702 and #729/#759/#806. |
| **Shared utility** | **rejected** | The classic answer — extract a shared `resolve_module()` helper — fails a specific test: **a helper nobody calls creates no contract.** Ianvs already has the evidence for this in its own tree: `parse_kwargs` is exactly such a helper, sitting in Core, correct in intent, called by nobody, and now attracting two PRs. Adding a second one would reproduce the failure it is meant to cure. |
| **Ianvs Core** | **partial — narrow scope only** | Correct and unavoidable for E4. But E5 shows what a Core change costs when its semantics are not specified first: #558 is a good patch that still broke persistence for six Examples, because it changed a name that pickle happened to depend on. Core should change *after* the contract is written down, not as the vehicle for writing it. |
| **CI / Validation** | **selected** | The only layer that can act **before** a run reaches the module — which is the actual defect. It converts silent drift into a failing check, is inert for behaviour, and needs no Example to opt in. |
| Dependency / Packaging | excluded | §1.3. |

### 3.2 Trade-off analysis

| | Example-local | Shared utility | Ianvs Core | **CI / Validation** |
|---|---|---|---|---|
| Development effort | low per fix, ×31 | medium | low | low–medium (one job) |
| Maintenance burden | **high** — drift resumes immediately | high — two resolution paths coexist | low | low |
| Regression risk | none (E1/E2 are inert) | medium | **high** — E5, 572 modules | **none** — no runtime path changes |
| Time to resolution | slow; unbounded backlog | slow | fast but unsafe | fast |
| Prevents recurrence | **no** | no | no | **yes** |

The decisive row is the last one. Every other boundary repairs the 31 broken paths that
exist today; only validation prevents the 32nd.

### 3.3 Cross-Example impact and regression risk of the selected boundary

A validation job changes no runtime behaviour, so the regression risk is not to Examples
but to contributors — false positives that block unrelated PRs.

| Example group | Effect of turning validation on today | Risk |
|---|---|---|
| 12 Examples with unresolvable metric `url:` | reported as failing | **none functionally**; they already fail at run time |
| `robot-cityscapes-synthia`, `cloud_VLA_finetune`, `RoboDK Palletizing` | absolute developer paths flagged | none |
| 10 Examples with malformed `__all__` | flagged **as advisory only** | would be a false positive if made blocking — nothing reads `__all__` |
| Examples with colliding basenames (most) | reported as informational | must **not** block; collision is not yet defined as an error |
| Examples needing GPU/gated datasets | untouched — validation is static | none |

This is why the boundary is CI *and not* Core-with-a-hard-check: a static resolver that
refuses to start a run would immediately break the 12 Examples above for users who are
currently working around them.

### 3.4 Minimal repair strategy

Deliberately small. Three steps, in dependency order.

**Step 1 — Core, ~30 lines: make the contract inspectable without enforcing it.**
Add `core/common/contract.py` exposing one pure function that, given a parsed
`benchmarkingjob.yaml`, returns every `(name, url, resolved_path, registered_aliases)`
tuple it would resolve, plus the module basename it would key `sys.modules` by.
*Behaviour change: none.* It reads config and parses files; it does not import.

**Step 2 — CI: a static job over `examples/**`.**
Consume Step 1. Report, per Example: unresolvable `url:`, absolute paths, `name:` values
with no matching registration, and — advisory — basename collisions and malformed
`__all__`. Blocking for the first three, advisory for the last two.

**Step 3 — Core, only now: specify module identity, then change it.**
Write down what `load_module()` guarantees, then land #558 against that specification
with R4a and R4b addressed. Step 2 becomes the regression oracle for Step 3.

Affected files: `core/common/contract.py` (new), `.github/workflows/` (new job),
`core/common/utils.py` (Step 3 only). No Example file changes.
Expected behaviour change after all three: none at run time; previously silent
misconfiguration becomes a CI failure.

### 3.5 Local-fix justification

`__all__` and per-Example metric modules stay Example-local — they are Example
vocabulary. Duplication is prevented not by extracting them into a shared module but by
Step 2, which reports the same class of defect identically across all Examples from one
place. That is the distinction this analysis rests on: **share the check, not the code.**

## 4. Uniqueness

Audited against all 70 prior Discussions (`evidence/gap_analysis.txt`).

**Counter-consensus position, evidenced.** The prevailing answer in this term's
Discussions — and the intuitive one — is that a duplicated concern should be lifted into
a shared utility or Core helper. I argue against that here on evidence internal to this
repository: `parse_kwargs` is already precisely that helper, in Core, correct, and
**called by nobody** (Task 1 E2), and it has attracted two PRs to fix code that runs
zero times. A shared helper is not a contract; a check that runs is. I have not found
this argument, or the use of `parse_kwargs` as evidence for it, in any prior Discussion.

**Novel boundary argument.** The boundary is placed by asking *when* a declaration is
checked rather than *where* it lives. The 31/87-vs-0/87 asymmetry (E3) is the measurement
that motivates it, and it is a measurement no prior Discussion reports.

**Repair strategy not previously proposed.** Step 1's "inspect without enforcing" Core
addition — a resolver that reports what *would* be resolved without importing anything —
is what makes a static CI check possible for a framework whose entire coupling is
dynamic. Existing CI proposals in this term (#851, #744, and the Discussions around them)
check lint and file presence; none resolves the config→registration contract.

**Not claimed:** that CI validation is generally desirable, or that #851/#744 exist —
both are well covered by other candidates.

---

## Correction — posted 2026-08-28

**I made a factual error above and am correcting it rather than leaving it standing.**

§3.4 Step 2 proposes adding "a static CI job over `examples/**`", and §4 contrasts this
submission with "existing CI proposals … [that] check lint and file presence". Both
understate what the analysed commit already contains.

`.github/workflows/validator/` **already ships on `main` at `37a9c60`**. It landed with
PR #771 — the merge commit I have been analysing throughout — and is wired into
`static_code_requirement_cicd.yaml` on `pull_request` for `examples/**`. It implements
`_check_yaml_syntax`, `_check_repo_path_references`, `_check_hardcoded_paths`,
`_check_local_model_paths`, `_check_cuda_only_assumptions` and
`_check_metric_empty_pair_guard` over a 48-entry example inventory. I should have found
it before writing §3.4. Credit to @Prachi194agrawal, whose review on PR #835 pointed at it.

**What changes.** Step 2 is not a job to create; it is an extension to a job that exists.
The boundary conclusion is unchanged — and is now better supported than my own argument
made it, because the project has already placed validation at exactly this layer.

**What survives, sharper than what I first wrote.** The shipped validator resolves whether
config strings point at files that **exist**. It does not resolve whether config
**identifier** strings match anything the code **registers**: there are zero references to
`ClassFactory`, `register`, `alias` or `paradigm_type` anywhere under
`.github/workflows/validator/`.

That gap is demonstrable. Running the shipped validator unmodified at `37a9c60`
(`python3 tools/run_shipped_validator.py ianvs`):

| Example | Shipped validator verdict | Actually runnable? |
|---|---|---|
| `yaoba/singletask_learning_boost` | **PASS** (0 errors) | **No** — `paradigm_type: "singletasklearning_acboost"` is not in `ParadigmType` |
| `yaoba/singletask_learning_yolox_tta` | **PASS** (0 errors) | **No** — `paradigm_type: "singletasklearning_tta"` is not in `ParadigmType` |
| `robot-cityscapes-synthia/…/semantic-segmentation` | FAIL — `Repository path references exist` | no |
| `MOT17/…/pedestrian_tracking` (×2 entries) | FAIL — `Repository path references exist` | no |
| `Cloud_Robotics/…/perception-reasoning` | FAIL — `Repository path references exist` | no |

The path half of the contract is checked, and correctly reports four of the Examples I
discuss. **The identifier half is unchecked, and two Examples pass every check the project
runs while being unable to execute at all.** Dispatch in `base.py:95-152` and
`algorithm.py:109-127` has no `else`, so an unknown `paradigm_type` returns `None`
silently.

So the revised boundary claim is narrower and stands on executed evidence: **Core should
expose what it *would* resolve — the registration keys and the paradigm dispatch table —
so the existing validator can check identifiers as well as paths.** That is Step 1 of §3.4
unchanged; only Step 2's framing was wrong.
