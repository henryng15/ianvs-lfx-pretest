# 01 — Prior-art audit and angle selection

**Date:** 2026-08-27 · **Ianvs SHA under analysis:** `37a9c60` · **Status:** complete

## What this step did

Answered the one question that decides the whole submission: *which root problems
are still unclaimed?* The pretest scores `same Problem + same Solution -> 0`, and
70 rival Discussions were already published before we started.

Tooling written (all reproducible, no secrets, no GPU):

| Tool | Purpose |
|---|---|
| `tools/fetch_discussions.py` | Pull all 77 Discussions with every comment body |
| `tools/build_coverage.py` | Invert them into "which Issue/PR is claimed by whom" |
| `tools/fetch_targets.py` | All open in-range targets (issues #348-846, PRs #133-851) |
| `tools/find_gaps.py` | Cross the two -> unclaimed targets |
| `tools/scan_contracts.py` | AST census of `__all__` and `transformers` imports |
| `tools/scan_metric_contract.py` | Verify testenv metric `url:`/`name:` against the code |
| `tools/probe_load_module.py` | Executed reproduction of the loader collision |

## Findings

### The original plan's angle is dead

`docs/lfx-2026-term3-pretest-plan.md` targets the `use_gpu` / device-selection
problem. Three rivals already own it, the earliest by five days:

| Discussion | Author | Date | Overlap |
|---|---|---|---|
| #856 | nirdesho6o | 2026-08-22 | "use_gpu no-op in Core and hardcoded CUDA assumptions" — near-identical |
| #875 | Hiteshsai007 | 2026-08-23 | "Ianvs device-selection contract"; same #765+#767 critical PR, AST census, executed evidence |
| #928 | shubhika123 | 2026-08-25 | device management + dependency boundaries |

The plan's own pivot rule (§3) is therefore triggered. **Angle abandoned.**

### Coverage map

- 70 LFX Term 3 Discussions cite **361 distinct** Issue/PR numbers.
- Of 195 open in-range issues, **86 are cited by nobody**.
- Of 265 open non-draft in-range PRs, **71 are cited by nobody**.
- Saturated: #348 (21 rivals), #851 (18), #771 (16), #133 (14).

### Verified census results

`evidence/census_contracts.txt`, `evidence/census_metric_urls.txt`:

| Measurement | Value |
|---|---|
| Example `.py` files parsed (0 syntax errors) | 572 |
| Malformed `__all__` declarations | **30** across 15+ Examples |
| Well-formed `__all__` declarations | 104 |
| testenv metric entries whose `url:` file does not exist | **28** |
| testenv metric entries with an absolute developer path | **3** |
| testenv metric entries whose `name:` is unregistered | **0** |
| Example module basenames colliding across files | 69 (392 of 572 files) |
| Worst collisions | `basemodel.py` x41, `accuracy.py` x13, `acc.py` x12 |
| Example requirements lines with no version constraint | 302 of 536 |

### Executed reproduction

`evidence/probe_load_module.txt` — imports the **unmodified** production
`core.common.utils.load_module` (needs only `yaml`, no stubs) and shows that a
second Example module sharing a basename is never loaded; the first one's code is
silently reused and no error is raised.

This reproduces existing issue **#557**, so it is *evidence*, not a discovery.

## Angle selected

> **Ianvs Core resolves every Example artifact through unvalidated strings** — a
> config file path, a bare module basename, and a ClassFactory registry alias.
> None is checked before a benchmark run reaches it. Every Example inherits the
> same failure surfaces, and the repository is now accumulating uncoordinated open
> PRs that patch symptoms inside one 14-line function — **including PRs that
> change no runtime behavior at all.**

Rival-overlap check on the specific claims we intend to make:

| Claim | Rivals asserting it |
|---|---|
| Core never reads `__all__`, so `__all__` fixes are inert | **0** |
| `parse_kwargs` has zero callers in this repo | ~0 (only #899 mentions the name) |
| #558 unmasks the latent ClassFactory alias collision | to be proven experimentally |
| Loader basename collision (#557) | 4 rivals — used as shared evidence only, not claimed as new |

## Next step

`02` — Verify the merge-interaction hypothesis experimentally: apply #558's diff
and show the ClassFactory alias collision fires on Examples that currently pass by
accident. Then read the diffs of #558, #729, #759, #806, #642, #651, #598, #702
and every existing review thread on them.
