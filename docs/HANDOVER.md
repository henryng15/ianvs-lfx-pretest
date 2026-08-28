# Handover — what is done, and what only you can do

**Written:** 2026-08-27 ~06:30 UTC · **Updated:** 2026-08-28 ~03:00 UTC · **Deadline:** 2026-08-28 23:59 UTC
(= 2026-08-29 06:59 in Vietnam, UTC+7 · **~41 hours left** as of writing)

Everything below marked ✅ is already live on GitHub. The 5 items marked **TODO** are the
ones I physically cannot do. Total time for you: roughly **60–90 minutes**, most of it
the video.

---

## ✅ Already done — nothing to redo

| | Item | Link |
|---|---|---|
| 1 | Discussion created (only one, as the rules require) | https://github.com/kubeedge/ianvs/discussions/948 |
| 2 | Task 1–4 + Bonus posted as 5 separate comments | see §"All links" below |
| 3 | 10 PR reviews posted (5 mandatory + 5 bonus) | ditto |
| 4 | 4 issue comments posted | ditto |
| 5 | All 20 links verified HTTP 200 | `python3 tools/verify_links.py` |
| 6 | Corrections + 2 follow-up reviews posted (see `docs/progress/05-...`) | #598, #617, and Task 3/4/Bonus edited in place |
| 7 | `.docx` for the email built | `submission/LFX-2026-Term3-Ianvs-Pretest-henryng15.docx` (89 KB) |
| 8 | Working repo committed and pushed | https://github.com/henryng15/ianvs-lfx-pretest |

**RunPod was not used.** Every finding runs on CPU with no dataset, model or network, so
there was nothing to rent. Your balance is untouched at **$6.93**.

---

## TODO 1 — Make the reproduction repo public  ⏱ 30 seconds  🔴 do this first

My posted comments link to `github.com/henryng15/ianvs-lfx-pretest` as the source of the
probe scripts. **It is currently private, so for a reviewer that link is broken**, and the
rules say broken links score zero.

```bash
gh repo edit henryng15/ianvs-lfx-pretest --visibility public --accept-visibility-change-consequences
```

Then confirm it opens in a logged-out browser (or a private window):
https://github.com/henryng15/ianvs-lfx-pretest

I already checked it contains **no secrets** — `.env` is git-ignored and only the empty
`.env.example` placeholders are tracked. You can re-verify:

```bash
cd ~/VSCode/projects/KubeEdge
git ls-files | grep -i env        # should show only .env.example
git grep -nE "hf_[A-Za-z0-9]{20,}|rpa_[A-Za-z0-9]{20,}"   # should print nothing
```

> If you would rather keep it private, tell me and I will edit the comments to drop the
> links — the Discussion already has a self-contained appendix, so nothing depends on it.

---

## TODO 2 — Screenshots  ⏱ 10 minutes

Task 1's rubric asks for "detailed logs and execution screenshots". I produced the logs;
I have no display, so I could not screenshot them.

Run these four, and screenshot each terminal window (whole window, so the command line is
visible):

```bash
cd ~/VSCode/projects/KubeEdge

# 1 — the commit everything is measured at (expect 37a9c60)
cd ianvs && git rev-parse --short HEAD && cd ..

# 2 — __all__ is inert  (expect: 30 malformed, 0 star-imported, 0 core refs)
python3 tools/probe_all_is_inert.py ianvs | tail -12

# 3 — parse_kwargs is unreachable  (expect: invocations NONE)
python3 tools/probe_parse_kwargs_dead.py ianvs

# 4 — PR #558 differential, the headline finding
python3 tools/probe_pr558_transitive.py ianvs
python3 tools/probe_pr558_pickle.py ianvs
```

Then attach them by **dragging the image files into the GitHub comment box**:

- Screenshots 2 and 3 → edit the **Task 1** comment
  https://github.com/kubeedge/ianvs/discussions/948#discussioncomment-18171140
  Paste them under the matching "E1"/"E2" code block.
- Screenshot 4 → edit the **Task 2** comment
  https://github.com/kubeedge/ianvs/discussions/948#discussioncomment-18171142
  Paste under "R4a" and "R4b".

*(Editing a comment does not change its permalink, so the links in the email stay valid.)*

---

## TODO 3 — One short video  ⏱ 20–30 minutes  ← the biggest scoring gap

Task 2's "Reproduce" is worth **6 points** and says: *if execution succeeds, leave a video
showing the process*. I cannot record.

**Record 2–3 minutes, screen only, no voice needed.** Suggested take:

1. `cd ~/VSCode/projects/KubeEdge/ianvs && git rev-parse --short HEAD` → shows `37a9c60`
2. `git branch -a` → shows the real `pr-558` branch fetched from the PR
3. `cd .. && python3 tools/probe_pr558_transitive.py ianvs`
   → pause on the output: `main` gives `predict(1) = 1` for both; `pr-558` gives
   `example_B` its own code but **still `utils` from example_A**, so still `1` not `100`
4. `python3 tools/probe_pr558_pickle.py ianvs`
   → pause on: `main` = `LOAD-OK`, `pr-558` = `ModuleNotFoundError`

Recording on WSL: OBS Studio, or Windows **Win+Alt+R** (Xbox Game Bar) on the terminal
window, or `ffmpeg` if you have an X display. Keep it under 10 MB so you can drag it
straight into the GitHub comment.

Attach to the **Task 2** comment, in the "5. Reproduce" section. If it is over 10 MB,
upload unlisted to YouTube and paste the link instead.

---

## TODO 4 — Send the email  ⏱ 10 minutes

**To:** `zimu.zheng@huawei.com`, `content@kaiwei.dev`
**Attach:** `submission/LFX-2026-Term3-Ianvs-Pretest-henryng15.docx`

> ⚠️ Rebuild the `.docx` **after** you finish TODO 2 and 3, so the attachment matches what
> is on GitHub — the rules say the email content takes precedence if the two differ:
> ```bash
> cd ~/VSCode/projects/KubeEdge && python3 tools/build_docx.py
> ```
> (Screenshots and video will not be inside the `.docx`; that is fine — the links point at
> the comments that hold them.)

Draft you can paste:

```
Subject: LFX Mentorship 2026 Term 3 Pre-test Submission — KubeEdge Ianvs Example Restoration (henryng15)

Dear Zimu Zheng and the KubeEdge Ianvs team,

Please find my pre-test submission for LFX Mentorship 2026 Term 3, "Comprehensive
Example Restoration for KubeEdge Ianvs: Phase IV", attached as a .docx containing the
full content of Task 1-4 and the Bonus task.

Pre-test Discussion
  https://github.com/kubeedge/ianvs/discussions/948

Task comments
  Task 1  https://github.com/kubeedge/ianvs/discussions/948#discussioncomment-18171140
  Task 2  https://github.com/kubeedge/ianvs/discussions/948#discussioncomment-18171142
  Task 3  https://github.com/kubeedge/ianvs/discussions/948#discussioncomment-18171145
  Task 4  https://github.com/kubeedge/ianvs/discussions/948#discussioncomment-18171147
  Bonus   https://github.com/kubeedge/ianvs/discussions/948#discussioncomment-18171151

Mandatory PR reviews (Task 2)
  #558  https://github.com/kubeedge/ianvs/pull/558#pullrequestreview-5037520746
  #651  https://github.com/kubeedge/ianvs/pull/651#pullrequestreview-5037524481
  #642  https://github.com/kubeedge/ianvs/pull/642#pullrequestreview-5037525342
  #598  https://github.com/kubeedge/ianvs/pull/598#pullrequestreview-5037526231
  #702  https://github.com/kubeedge/ianvs/pull/702#pullrequestreview-5037527196

  #598 follow-up  https://github.com/kubeedge/ianvs/pull/598#pullrequestreview-5047338395

Bonus PR reviews
  #617  https://github.com/kubeedge/ianvs/pull/617#pullrequestreview-5037528102
  #617 follow-up  https://github.com/kubeedge/ianvs/pull/617#pullrequestreview-5047339798
  #569  https://github.com/kubeedge/ianvs/pull/569#pullrequestreview-5037529132
  #739  https://github.com/kubeedge/ianvs/pull/739#pullrequestreview-5037529977
  #632  https://github.com/kubeedge/ianvs/pull/632#pullrequestreview-5037530827
  #540  https://github.com/kubeedge/ianvs/pull/540#pullrequestreview-5037531623

Issue comments
  #557  https://github.com/kubeedge/ianvs/issues/557#issuecomment-5434805900
  #597  https://github.com/kubeedge/ianvs/issues/597#issuecomment-5434807109
  #641  https://github.com/kubeedge/ianvs/issues/641#issuecomment-5434808390
  #568  https://github.com/kubeedge/ianvs/issues/568#issuecomment-5434809726

All evidence is reproducible on CPU with no dataset, model weights or network access:
  https://github.com/henryng15/ianvs-lfx-pretest

Thank you for your time.

Best regards,
Henry Nguyen (GitHub: henryng15)
```

---

## TODO 5 — Final link check right before you send  ⏱ 2 minutes

```bash
cd ~/VSCode/projects/KubeEdge && python3 tools/verify_links.py
```

Expect `22 links checked, 0 broken`. Then open two or three in a **logged-out** browser
window, including the `henryng15/ianvs-lfx-pretest` link from TODO 1.

---

## What was submitted, in one paragraph

The Root Problem is that **Ianvs has no enforced contract between the interface an Example
declares and the interface Ianvs actually resolves**. An Example declares itself through a
config `url:`, a config `name:`, and Python metadata (`__all__`, signatures); Core resolves
only the `name:`→ClassFactory alias, validates none of them, and does so only when a run
reaches the module. Three findings carry it, all executed and none claimed by any of the
70 rival Discussions: **`__all__` is read by nothing**, so PRs #651 and #642 change no
runtime behaviour; **`parse_kwargs` has zero callers**, so PRs #598 and #702 fix
unreachable code; and **PR #558** — the one PR that touches the live path, already
reviewed by three strong candidates — still lets sibling imports collide (returning `1`
where the Example's own helper returns `100`) and silently removes the recoverability of
pickled knowledge bases. A fifth surface, `paradigm_type`, turned up during the Bonus
review: two shipped `yaoba` Examples declare values absent from the `ParadigmType` enum
and dispatch has no `else`, so they are unrunnable and nothing reports it.

## Honest assessment

Strong on Analysis, Uniqueness and Review — the four PRs #651/#642/#598/#702 had **zero
reviews**, so every finding on them is first, and the #558 findings survived three prior
reviewers. Weakest on **Reproduce** until TODO 3 is done, and on Evidence screenshots until
TODO 2. No end-to-end benchmark run is claimed anywhere, and every such gap is labelled
with its blocker rather than glossed over.

## If you want to change anything

All source is in `submission/*.md`. Edit, then re-post with:

```bash
python3 tools/post_discussion.py   # skips anything already posted
python3 tools/post_targets.py      # same
python3 tools/build_docx.py        # rebuild the attachment
```

Both posting scripts are idempotent — they read `evidence/posted*.json` and will not
create a second Discussion or double-post a review. To **edit** an already-posted comment,
do it in the GitHub web UI; the permalink does not change.


---

## Update — 2026-08-28

Three things happened after the first handover was written.

**1. The author of PR #598 replied to my review and updated the PR.** They added unit
tests and moved the head from `69470dd` to `6b39813`. Another candidate (@31groot) then
found that positional-only parameters are still wrongly accepted. I re-reviewed at the new
head, independently confirmed their finding, added two cases neither of them had
(`getfullargspec` raises `TypeError` on callables it cannot introspect; builtins silently
return `{}`), and **revised my verdict from minor to major revision**.

**2. I found and corrected a factual error in my own submission.** Task 4 said no static
config validation existed and Task 3 proposed adding it. Wrong: `.github/workflows/validator/`
already ships on `main` at the exact commit I analysed, merged via #771, wired into CI.
Corrections are now appended in place to the Task 3, Task 4 and Bonus comments — permalinks
unchanged, nothing silently rewritten.

The correction ended up **strengthening** the submission. Running the shipped validator
shows it checks paths but not identifiers, so both `yaoba` Examples **pass every check the
project runs and still cannot execute**. The "missing fix" is now demonstrated against the
project's own validation rather than asserted.

**3. Uniqueness re-verified.** 86 Discussions now (was 70). My three core claims —
`__all__` is inert, `parse_kwargs` is unreachable, #558 breaks pickle recoverability —
are still asserted by **nobody else**.

**Nothing changes in your TODO list.** Same five steps. Two notes:

- The link count in TODO 5 is now **22**, not 20.
- Rebuild the `.docx` after your screenshots/video as before — it already includes the two
  follow-up reviews and the corrections.
