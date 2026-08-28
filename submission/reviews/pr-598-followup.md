Re-reviewed at the new head `6b39813` (my first review was against `69470dd`).

Thanks for the quick turnaround, and the unit tests are a real improvement — they are the
thing this PR had been missing.

**On the scope point, I think we are agreeing rather than disagreeing.** You are right
that a shared helper in `core/common/` should be correct for future callers; I am not
arguing it should stay broken. My narrower point was only that #597 states the bug
*currently* drops Example hyperparameters, and it cannot, because the function has no
callers and Sedna ships its own. That matters for two practical reasons: this PR needs no
Example regression testing, and #597 should not be counted as a broken Example. Neither is
an argument against merging.

**@31groot's positional-only finding reproduces.** I verified it independently on both
refs, so it is pre-existing rather than introduced here:

```text
def posonly(x, /, y): ...
parse_kwargs(posonly, x=1, y=2) -> {'x': 1, 'y': 2}     # main AND 6b39813
posonly(**that)                 -> TypeError: posonly() got some positional-only
                                   arguments passed as keyword arguments: 'x'
```

`getfullargspec()` merges positional-only parameters into `.args`, so
`set(need_kw.args) | set(need_kw.kwonlyargs)` admits names that cannot legally be passed
by keyword. Their recommendation stands and I am not restating it further.

**Two further cases the new tests do not cover.** Both are also pre-existing, but the PR
is the natural place to close them since it is rewriting exactly this filter.

**1. `getfullargspec()` raises on callables it cannot introspect, and nothing catches it.**

```text
parse_kwargs(dict, a=1)  -> TypeError: unsupported callable      # main and 6b39813
```

The function already guards `if not callable(func): return kwargs`, which shows the intent
to tolerate odd inputs — but `dict` *is* callable, passes that guard, and then raises from
`getfullargspec`. Any C-implemented or otherwise unintrospectable callable does the same.

**2. When introspection succeeds but is empty, every kwarg is silently discarded.**

```text
parse_kwargs(len,   a=1) -> {}
parse_kwargs(print, a=1) -> {}
```

For a parameter-filtering helper in a benchmarking framework, silently returning `{}` is
the worse of the two outcomes: a caller loses every hyperparameter and gets no signal. A
`try/except TypeError` that falls back to returning `kwargs` unchanged — matching the
existing non-callable branch — would make both cases behave consistently and is about
three lines.

**One very small note.** `getfullargspec` on a class returns `__init__`'s spec, so `self`
lands in `.args` and is therefore accepted into the filtered set. Harmless in practice
(no one passes `self=` from YAML), and mentioned only because `ClassFactory.get_cls()`
returns classes, so classes are the likely shape of a future caller.

**Revised recommendation: major revision** (was *minor revision* in my first review).

That change is because of @31groot's finding plus the two above — my earlier "no coding
effort" was accurate for head `69470dd` and is not accurate now that the accepted-set
construction is the thing under discussion. The direction of the PR is right and I would
still like to see it land over #702.
