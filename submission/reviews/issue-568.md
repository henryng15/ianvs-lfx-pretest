Confirmed at `37a9c60`. `LadeSpecDecLLM` appears exactly twice in the repository:

```text
examples/.../query-routing/edge_model.py:21   from models import ... LadeSpecDecLLM
examples/.../query-routing/edge_model.py:77       self.model = LadeSpecDecLLM(**self.kwargs)
```

Both are **uses**. There is no definition anywhere, and
`.../query-routing/models/__init__.py` exports only `APIBasedLLM`, `HuggingfaceLLM`,
`VllmLLM`, `BaseLLM` and `EagleSpecDecModel`. So line 21 raises `ImportError` and the
module cannot be loaded at all — before any dataset, model download or API key is
involved. PR #569 addresses it.

**One observation about the same file that may be useful when fixing this.** Four lines
below the failing import:

```python
# line 21  -- ImportError, fatal
from models import HuggingfaceLLM, APIBasedLLM, VllmLLM, EagleSpecDecModel, LadeSpecDecLLM

# line 25  -- no effect at all
__all__ = ["BaseModel"]        # this module defines EdgeModel, not BaseModel

# line 27  -- the name Ianvs actually resolves
@ClassFactory.register(ClassType.GENERAL, alias="EdgeModel")
```

Three name declarations in seven lines. Line 21 names something that does not exist and
kills the Example; line 25 names something that does not exist and is never read (nothing
star-imports this module, and `core/` contains zero references to `__all__`); line 27 is
the one Core resolves, and it is correct.

Since #569 is already touching this file for line 21, correcting line 25 in the same
change would cost nothing and remove a second wrong name from the file.

**Also worth confirming for whoever closes this:** `test_queryrouting.yaml` never offered
`LadeSpecDec` in its `values:` list, and `EagleSpecDec` there is commented out, so
removing the backend loses no reachable configuration. That said, this issue asks for the
backend to be treated as *optional*; #569 deletes it. Given the class was never
implemented, deletion looks right, but the issue text and the fix should be reconciled
before closing.
