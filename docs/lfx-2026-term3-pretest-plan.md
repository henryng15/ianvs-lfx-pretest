# LFX Mentorship 2026 Term 3 — KubeEdge Ianvs Pretest
## Evidence-first execution plan

**Project:** CNCF — KubeEdge: Comprehensive Example Restoration for KubeEdge Ianvs: Phase IV  
**Pretest:** https://github.com/kubeedge/ianvs/issues/230#issuecomment-5375307896  
**Deadline:** 2026-08-28 23:59 UTC (= 2026-08-29 06:59 UTC+7 / 07:59 UTC+8)  
**Local source-inspection snapshot:** Ianvs `37a9c60` (record a fresh SHA immediately before collecting evidence)

> This is a working plan, not submission text. Every sentence labelled **candidate** must be independently verified and compared with existing Discussions/reviews before it is published. Do not claim novelty from this file alone.

---

## 1. Non-negotiable submission rules

1. Create one Show and tell Discussion titled `LFX 2026 Term 3 Example Restoration: problem analysis of xxx`.
2. Publish Task 1, Task 2, Task 3, Task 4, and Bonus as five separate comments in that Discussion.
3. Put target-specific technical content on the original target Issues/PRs; keep cross-target comparison, uniqueness, consolidation, and self-assessment in the Discussion.
4. Use only open Issues `#348`–`#846` and open PRs `#133`–`#851` for scored work. Re-check status immediately before posting.
5. Submit the full GitHub content in one PDF/DOCX, with every Discussion/comment/review permalink. The email copy takes precedence if it differs from GitHub.
6. Never call a non-executed check “passed”. State the command, commit SHA, output, and resource boundary.

The rubric requires at least two Examples for Tasks 1, 3, and 4; at least three technically connected PRs for Task 2; and at least one PR beyond a purely Example-local implementation.

---

## 2. Evidence checkpoint: what is established, and what is not

### 2.1 Established from Ianvs `37a9c60`

| Fact | Evidence | Safe interpretation |
|---|---|---|
| There are six concrete paradigm directories: `singletask_learning`, `lifelong_learning`, `incremental_learning`, `federated_learning`, `multiedge_inference`, and `joint_inference`. | `find core/testcasecontroller/algorithm/paradigm -mindepth 1 -maxdepth 1 -type d` | Do **not** write “seven paradigms” unless a specific test matrix, not directory count, proves seven cases. |
| On this snapshot, only `singletask_learning.py` consumes `use_gpu`; the other five concrete paradigm directories contain no match. | `rg -n "use_gpu" core` plus the per-directory command below | This is a historical `main` observation, not a novel finding. Issue #765 already reports it. |
| Only two example testenv files explicitly declare `use_gpu`. | `rg -n '^\s*use_gpu\s*:' examples` | Do not infer that every other example should be forced to CPU. |
| `TestCaseController.run_testcases()` runs test cases sequentially in one process. | `core/testcasecontroller/testcasecontroller.py:46-61` | A process-global environment change deserves a sequential-test-case regression check. |
| `imagenet/multiedge_inference_bench` has its own `devices.yaml`, ONNX Runtime provider selection, and NVML calls. | its manual/automatic `basemodel.py` files and README | It has device/provider problems, but those are not automatically caused by the Core `use_gpu` defect. |
| ERFNet receives the module kwargs via `TrainArgs(**kwargs)` / `ValArgs(**kwargs)` and contains its own CUDA decisions. | `examples/robot-cityscapes-synthia/.../erfnet/basemodel.py` | Core visibility and ERFNet's own device logic are complementary layers, not duplicate code. |

Run and attach this exact inventory with a current SHA:

```bash
git rev-parse --short HEAD
rg -n "use_gpu" core
for p in singletask_learning lifelong_learning incremental_learning \
         federated_learning multiedge_inference joint_inference; do
  printf '%s: ' "$p"
  rg -l "use_gpu" "core/testcasecontroller/algorithm/paradigm/$p" | wc -l
done
find examples -iname 'testenv*.yaml' -type f | wc -l
rg -n '^\s*use_gpu\s*:' examples
```

### 2.2 Existing work that constrains the submission

Do not present the following as original discoveries:

| Existing work | Already established there |
|---|---|
| [Issue #765](https://github.com/kubeedge/ianvs/issues/765) | `use_gpu: false` is a no-op; the setting is applied after module construction; other paradigms ignore it; `False` default and omitted-key behavior need a third state. It also supplies a no-GPU probe reproduction. |
| [PR #767](https://github.com/kubeedge/ianvs/pull/767) | Moves visibility handling to `ParadigmBase` before module instantiation, uses `None`/`true`/`false`, and uses `-1` for explicit CPU-only visibility. |
| Existing review thread on #767 | Test-at-instantiation, cross-paradigm behavior, a broader device contract, and the fact that examples may still choose devices themselves have already been discussed. |

This means the prior plan's F1/F4 “novel problem” claim and its proposed relocation of #767 are invalid. A valid submission can still review and build on #767, but must add a different, evidenced technical value.

---

## 3. Decision gate: establish uniqueness before committing to the angle

Create `docs/prior_art.md` before drafting a final Discussion. For every relevant Discussion, Issue comment, and PR review, capture:

| URL/permalink | Target | Existing technical claim | Evidence used | Candidate addition | Duplicate? |
|---|---|---|---|---|---|
| `<permalink>` | `<#>` | `<precise claim>` | `<code/log>` | `<specific new value>` | yes/no/uncertain |

### Candidate addition to investigate — not yet a claim

`#767` changes the process-global `CUDA_VISIBLE_DEVICES` value. Test cases are executed sequentially in one interpreter, while the `None` branch intentionally leaves the current value unchanged. Investigate whether this produces order-dependent visibility:

1. Save an ambient value, e.g. `CUDA_VISIBLE_DEVICES=0,1`.
2. Construct a minimal `use_gpu: false` test case; observe `-1` **inside the module constructor**.
3. Construct a second minimal test case with the key omitted; observe whether it inherits `-1` rather than the original ambient value.
4. Repeat in the actual `TestCaseController.run_testcases()` order, not only as isolated constructor calls.

This is a review hypothesis, not a defect claim. It becomes publishable only if it reproduces on the PR head, is absent from existing reviews, and its intended semantics are confirmed. If it is not new or not reproducible, discard it rather than weakening the submission.

### Pivot rule

If the prior-art table leaves no meaningful new technical value for the device angle, pivot before posting. A fallback angle must be selected only after the same audit; “unclaimed” is never assumed from a topic name or issue number.

---

## 4. Scoped problem model

Use this wording only after the decision gate passes:

> Ianvs has a **layered CPU-capability compatibility problem**, not a proven single-cause device bug. Core visibility configuration (#765), ERFNet CUDA assumptions (#471/#554), and multiedge provider/NVML behavior (#599/#600/#601/#585) affect the same CPU-only user journey at different layers. #767 repairs the Core ordering and tri-state visibility layer; it does not by itself select valid ONNX Runtime providers or remove example-local CUDA logic.

This framing is precise about relationship:

| Target | Layer | Relationship to the Core visibility fix |
|---|---|---|
| #765 / #767 | Core lifecycle and visibility | Directly addressed by #767 while it remains open. |
| #471 / #554 | ERFNet's PyTorch CUDA decisions | Complementary: #554 must make ERFNet respect actual CUDA availability. |
| #599 / #600 / #601 / #585 | Multiedge NVML, provider fallback, device-map behavior | Related CPU compatibility, but a separate provider/device-topology layer. |
| #533 | MPS placement | Boundary example: device placement, not `CUDA_VISIBLE_DEVICES` selection. Do not use it as proof of the Core cause. |

Do not write that fixing #767 makes #554 or #585 dead code, or that `devices.yaml` is a generic Core-device contract. Those conclusions are not supported by the code.

---

## 5. Target set and review selection

Re-check every target immediately before posting. The following were open and in range when this plan was updated.

### Mandatory Issue set

| Issue | Example/layer | Use |
|---|---|---|
| [#765](https://github.com/kubeedge/ianvs/issues/765) | Core + `llm-edge-benchmark-suite` | Core lifecycle/visibility evidence and no-GPU reproduction. |
| [#471](https://github.com/kubeedge/ianvs/issues/471) | `robot-cityscapes-synthia` ERFNet | Independent example-local CUDA assumption. |
| [#599](https://github.com/kubeedge/ianvs/issues/599), [#600](https://github.com/kubeedge/ianvs/issues/600), [#601](https://github.com/kubeedge/ianvs/issues/601) | `imagenet/multiedge_inference_bench` | NVML/provider/device-map evidence; keep their comments target-specific. |

### Mandatory PR set — four focused reviews

| PR | Scope | Why it belongs |
|---|---|---|
| **[#767](https://github.com/kubeedge/ianvs/pull/767)** | Core (3 files) | Critical PR: changes the shared initialization lifecycle for all paradigms. |
| [#554](https://github.com/kubeedge/ianvs/pull/554) | ERFNet (2 files) | CPU-only behavior in a second Example; test interaction with Core visibility rather than call it duplicate. |
| [#585](https://github.com/kubeedge/ianvs/pull/585) | ImageNet/multiedge (17 files) | Repairs provider/NVML behavior plus unrelated transformer/data/config changes; assess scope and regression risk separately. |
| [#790](https://github.com/kubeedge/ianvs/pull/790) | `llm_simple_qa` (6 files) | Related CUDA-only loading case; verify the actual diff before claiming a relationship. |

Do **not** use [#679](https://github.com/kubeedge/ianvs/pull/679) in the mandatory set for this angle. Its Core changes concern lifelong inference/evaluation fallback and division behavior, not the `use_gpu` contract. It can be considered separately for Bonus after a uniqueness audit.

---

## 6. Task 1 — Root Problem Analysis (30 points)

### Problem definition

Name #765 and at least two different Examples: `llm-edge-benchmark-suite` (the shipped `use_gpu` configurations), `robot-cityscapes-synthia` (ERFNet), and/or `imagenet/multiedge_inference_bench`. State the relationship as **layered and related**, not single-sourced.

### Evidence

Minimum submission package:

- Current source inventory from §2.1 with SHA.
- The Issue #765 probe independently run on `main` and, where feasible, the #767 head. Attach unedited console logs and one screenshot or short video. It requires no physical GPU because it observes the environment variable.
- A call-order excerpt proving `TestCase` passes TestEnv attributes, and `ParadigmBase` instantiates modules after visibility handling on #767's diff.
- One ERFNet and one multiedge `file:line` evidence item, each with the concrete impact on that Example.

Label static findings **verified by source inspection at `<SHA>`**. Label the exact executed commands, expected result, and observed result separately.

### Analysis

Answer the rubric's three questions directly:

1. **Layer:** #765 is Core-related. #471 and ImageNet targets are related example/provider defects, not proof that one Core line causes all of them.
2. **Relationship:** #765/#767 and #471/#554 share the CPU-only journey but use different mechanisms; #599/#600/#601 also require example-specific provider/device-map handling.
3. **Separate fixes:** example-local fixes can drift, while an over-broad Core fix risks changing every paradigm. Explain specifically which responsibility belongs to each layer.

### Uniqueness

Never say “F1” or “F4” is new. Use the completed `prior_art.md` table. State either:

- the exact new, reproducible technical finding, its impact, and the permalink audit that shows it was not already raised; or
- that the device angle provides only partial credit and switch to the audited fallback before posting.

---

## 7. Task 2 — Multi-PR Code Review (40 points)

### Recommendation matrix

The final verdict must follow the reviewed diff and current discussion, not this draft.

| PR | Provisional review focus | Verdict only after evidence |
|---|---|---|
| #767 | Correct lifecycle/tri-state direction; verify constructor-time behavior, all six concrete paradigm paths, and any sequential-test-case state behavior. Existing test requests are prior art; add only a genuinely new finding. | `<accepted / minor / major / reject>` |
| #554 | Verify every remaining CUDA path respects `args.cuda`; inspect resume/map-location and CPU behavior. It complements Core visibility. | `<verdict>` |
| #585 | Separate its NVML/provider fallback from transformer, dataset, YAML, and documentation changes. Identify whether the bundled changes create a review or regression blind spot. | `<verdict>` |
| #790 | Inspect its actual model loading/config changes; do not assume it duplicates #767. | `<verdict>` |

For every PR, publish under these headings: root-vs-symptom, duplicated/conflicting behavior, edge cases and regression risk, cross-example impact, correct layer, simultaneous merge behavior, evidence, verification boundary, and explicit verdict.

### Required alternative explanation

Use a defensible alternative, not a straw man:

> Alternative: the example failures are independent provider/model implementation bugs and `use_gpu` is only a narrow Core visibility option.  
> Assessment: this is partly supported by ImageNet's explicit device-map and ONNX Runtime provider logic. It is rejected only for the narrower #765 claim because the setting is a shared TestEnv field and #767 demonstrates a common initialization-order repair. It is **not** rejected as an explanation for all ImageNet or ERFNet failures.

### Reproduction boundary

Run the no-GPU #765 probe before and after #767. For full benchmark runs blocked by ImageNet, Cityscapes/Synthia, weights, or NVIDIA hardware, attach the actual failure log and resource requirement; do not invent a pass result.

---

## 8. Task 3 — Repair Boundary Analysis (15 points)

| Layer | Decision | Evidence-based justification |
|---|---|---|
| Example-local | Retain where provider/model behavior is specific | ERFNet CUDA calls and multiedge ONNX Runtime/device-map logic cannot safely be erased by visibility alone. |
| Shared utility | Candidate follow-up, not assumed remedy | Consider only if a concrete API and adopters are identified; a helper nobody calls does not create a contract. |
| Ianvs Core | Adopt for visibility lifecycle only | #767's `ParadigmBase` placement precedes module construction and preserves omitted-key behavior using `None`. |
| Dependency/packaging | Separate concern | Optional NVML/ORT packaging affects installability but does not itself select a correct runtime provider. |
| CI/validation | Guard, not primary repair | Add a lightweight CPU-only constructor/probe regression check after behavior is specified. |

Compare effort, maintenance, regression risk, and time-to-resolution. Assess the concrete affected groups separately: two explicit `llm-edge-benchmark-suite` configs; ERFNet; ImageNet/multiedge; and omitted-key examples. Do not estimate their count from a stale example total.

The unique boundary argument, if the audit supports it, should be narrow: Core owns *when visibility is applied*; each Example owns its model/provider-specific device behavior. That is more defensible than claiming a single global device resolver can replace `devices.yaml`.

---

## 9. Task 4 — Restoration Path Design (15 points)

### Dependency graph

```text
S0  Reproduce #765 with a no-GPU probe and record baseline
 |
 | establishes the observable behavior and regression oracle
 v
S1  #767 Core visibility lifecycle (open PR)
 |\
 | \-- must be checked at module-constructor time; preserve omitted-key behavior
 |
 +-------------------------------+
 |                               |
 v                               v
S2a #554 ERFNet CPU paths     S2b #585 multiedge provider/NVML paths
 |                               |
 | independent files, but both require S1 behavior to be understood
 +---------------+---------------+
                 v
S3  Example-specific smoke tests, documentation, and CPU regression guard

#790: review and place only after its diff proves a dependency; otherwise it is parallel work.
```

`#554` and `#585` are not dead after #767: the former controls ERFNet logic, and the latter controls ONNX Runtime/provider and NVML behavior. They may be reviewed in parallel because their modified file sets are separate; only claim execution independence after recording the relevant commands and output.

### Existing-work audit and missing-fix table

| Blocker | Current evidence | Existing work | Remaining question |
|---|---|---|---|
| Core order / explicit false | #765 reproduction and #767 diff | #767 open | Does the PR pass constructor-time tests across all concrete paradigm paths and sequential test cases? |
| ERFNet hardcoded CUDA | #471 plus local source inspection | #554 open | Which CUDA paths remain and how does a CPU-only environment behave? |
| ImageNet NVML/provider behavior | #599/#600/#601 plus local source inspection | #585 open | Does fallback work with the declared `devices.yaml` topology and no CUDA provider? |
| Model/config loading in `llm_simple_qa` | #790 diff and execution log | #790 open | Is it actually dependency-ordered with S1, or parallel? |

### Verification gates

| Gate | Action | Expected observable result | Failure action |
|---|---|---|---|
| G0 | Run #765's minimal probe on `main` with ambient `CUDA_VISIBLE_DEVICES=0,1`. | Record current constructor/train values. | Stop and repair the probe; do not rely on a source-only claim for the runtime behavior. |
| G1 | Run the same probe on #767 head for explicit `true`, explicit `false`, and omitted key. Observe in module construction. | `0`, `-1`, and preserved ambient value respectively, if that is the agreed contract. | Reject or request revision with the raw log. |
| G1b | Drive the probe through each of the six concrete paradigm paths that can load it. | Same Core visibility lifecycle before module construction. | Identify the divergent paradigm and narrow the claim. |
| G1c | Run two TestCases sequentially: explicit false then omitted key, preserving/restoring ambient state according to agreed semantics. | No unintended order-dependent visibility. | File a target-specific finding only if reproduced and not prior art. |
| G2a | ERFNet CPU-only smoke/import check. | No unconditional CUDA failure before the dataset boundary. | Attach actual stack trace; keep dataset/hardware limitation explicit. |
| G2b | ImageNet import/provider check with CUDA unavailable. | Controlled fallback or precise supported-environment error. | Attach provider/import failure; do not claim benchmark success. |
| G3 | Re-run G0–G2 after each merged stage. | Earlier successful gates remain stable. | Revert the narrow stage, then diagnose. |

Rollback: `git revert` #767 as one PR; revert #554/#585 independently because their files are example-local. No default-flip stage is proposed: #767 deliberately preserves the omitted-key behavior with `None`.

Final success is not one vanished exception: it requires the G1 contract evidence, relevant example smoke results, documented resource boundaries for unreachable benchmarks, and docs that match the verified command paths.

---

## 10. Bonus plan (+15 cap)

Use Bonus only after all mandatory reviews are evidence-complete. Review 4–6 targets deeply rather than pursuing quantity.

| PR | Actual scope | Candidate review direction — verify first |
|---|---|---|
| [#851](https://github.com/kubeedge/ianvs/pull/851) | Advisory pylint and requirements-file presence checks | Examine whether advisory `continue-on-error` and `paths: examples/**` give the claimed protection; also assess unrelated source-file scope. |
| [#744](https://github.com/kubeedge/ianvs/pull/744) | Config path/YAML validation with a baseline | Examine baseline drift and whether path resolution matches Ianvs runtime. |
| [#850](https://github.com/kubeedge/ianvs/pull/850) | Core subprocess security | Perform a target-specific security/code-path analysis. |
| [#849](https://github.com/kubeedge/ianvs/pull/849) | Core field validation | Reproduce the fail-open/fail-closed behavior with a minimal input. |
| [#694](https://github.com/kubeedge/ianvs/pull/694) | Python CI matrix | Verify package compatibility and interaction with the actual test jobs. |

Do not call #851 and #744 duplicate implementations. They cover different checks. A valid cross-target finding may compare their coverage and blocking semantics only after verifying both diffs and existing reviews.

---

## 11. Writing and publishing checklist

### Before writing

- [ ] Record source SHA, PR head SHAs, target status, and time checked.
- [ ] Create and complete `docs/prior_art.md`; include all relevant Discussion/review permalinks.
- [ ] Execute G0 and G1; preserve commands, raw logs, screenshot/video.
- [ ] Inspect all four mandatory PR diffs and every existing review thread.
- [ ] Prove or discard the sequential-test-case hypothesis (G1c).
- [ ] Verify all example-specific claims directly from the current checkout.

### Before posting

- [ ] Each Task has one separate Discussion comment.
- [ ] Every major finding has `claim → evidence → impact → boundary`.
- [ ] Every Issue/PR comment is target-specific; no copied cross-target language.
- [ ] Every PR review has an explicit allowed verdict.
- [ ] Every novelty sentence points to the completed prior-art comparison.
- [ ] Every executed result names SHA and command; every unexecuted result names the blocker.

### Submission

- [ ] Re-check targets are still open and within range.
- [ ] Collect the Discussion, five comment, Issue, PR-review, and Bonus links.
- [ ] Open every permalink while signed out/in a fresh tab.
- [ ] Export the exact posted content to one PDF/DOCX and email it with the links.

---

## 12. References

- Pretest specification: https://github.com/kubeedge/ianvs/issues/230#issuecomment-5375307896
- Project issue: https://github.com/kubeedge/ianvs/issues/230
- Core visibility issue: https://github.com/kubeedge/ianvs/issues/765
- Core visibility PR: https://github.com/kubeedge/ianvs/pull/767
- ERFNet issue / PR: https://github.com/kubeedge/ianvs/issues/471 and https://github.com/kubeedge/ianvs/pull/554
- ImageNet issues / PR: https://github.com/kubeedge/ianvs/issues/599, https://github.com/kubeedge/ianvs/issues/600, https://github.com/kubeedge/ianvs/issues/601, and https://github.com/kubeedge/ianvs/pull/585
