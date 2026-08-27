# Ianvs LFX 2026 Term 3 — Pretest Working Repository

Working artifacts for the CNCF/KubeEdge LFX Mentorship 2026 Term 3 pretest:
**"Comprehensive Example Restoration for KubeEdge Ianvs: Phase IV"**.

- Pretest spec: <https://github.com/kubeedge/ianvs/issues/230#issuecomment-5375307896>
- Deadline: **2026-08-28 23:59 UTC**
- Upstream under analysis: `kubeedge/ianvs` @ `37a9c60` (cloned into `ianvs/`, git-ignored)

## Layout

| Path | Contents |
|---|---|
| `docs/lfx-2026-term3-pretest-plan.md` | Original evidence-first execution plan |
| `docs/PROGRESS.md` | Index of progress notes, newest last |
| `docs/progress/` | One short note per completed component/task |
| `tools/` | Probe scripts and audit tooling (reproducible, no secrets) |
| `evidence/` | Raw command output, logs, and audit tables |
| `submission/` | Draft Discussion body and Task 1-4 + Bonus comments |

## Ground rules

1. Never describe an unexecuted check as passed. Every claim carries command + SHA + output.
2. Every novelty claim is checked against the prior-art audit before it is written.
3. Secrets live in `.env` only, which is git-ignored. See `.env.example`.

## Setup

```bash
cp .env.example .env   # then fill in RUNPOD_API and HF_TOKEN
git clone --depth 1 https://github.com/kubeedge/ianvs.git ianvs
```
