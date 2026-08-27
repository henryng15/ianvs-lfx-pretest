#!/usr/bin/env python3
"""Regression demonstrated on PR #558: dynamically loaded Example classes stop
being unpicklable outside the exact absolute path they were loaded from.

Why this matters for Ianvs
--------------------------
Sedna's lifelong learning persists its knowledge base with pickle:
    sedna/core/lifelong_learning/lifelong_learning.py   FileOps.dump(task_index...)
    sedna/core/lifelong_learning/knowledge_management/*  FileOps.dump(task_info, name)
    sedna/common/file_ops.py                             joblib.dump(obj, name)
The persisted structures hold objects whose classes are defined in Example
modules that Ianvs loads through core.common.utils.load_module -- for example
`task_definition_by_domain.py` and `task_allocation_by_domain.py` in
examples/robot-cityscapes-synthia/.../erfnet/.

pickle does not serialise a class: it stores `obj.__class__.__module__` and
`__qualname__`, and re-imports that module name on load.

  main  @37a9c60 : module name is the bare basename, e.g. "taskdef"
  PR #558 @b99161f: module name is "taskdef_<md5 of the absolute file path>"

The md5 is derived from the absolute path, so the recorded module name differs
on any other checkout directory, container, or machine -- and the edge/cloud
knowledge-base transfer that lifelong learning performs is exactly such a move.

Usage: python3 tools/probe_pr558_pickle.py [path/to/ianvs]
"""
import os, pathlib, pickle, subprocess, sys, tempfile, textwrap

IANVS = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "ianvs").resolve()

TASKDEF = textwrap.dedent('''\
    """Stand-in for an Example task-definition module loaded via load_module()."""
    class TaskDefinitionByDomain:
        def __init__(self, domain):
            self.domain = domain
        def __repr__(self):
            return f"TaskDefinitionByDomain({self.domain!r})"
''')

CHILD = textwrap.dedent('''\
    """Unpickle in a fresh interpreter.

    argv[1] = pickle file, argv[2] = the Example directory holding the source.
    The directory is put on sys.path, which is the recovery a consumer can
    perform and which Ianvs itself performs in load_module().
    """
    import pickle, sys
    sys.path.insert(0, sys.argv[2])
    with open(sys.argv[1], "rb") as fh:
        try:
            obj = pickle.load(fh)
            print(f"LOAD-OK {obj!r}")
        except Exception as e:
            print(f"LOAD-FAIL {type(e).__name__}: {e}")
''')


def run_case(ref, workdir):
    """Load a module through `ref`'s load_module, pickle an instance of a class
    it defines, then unpickle it in a *fresh* interpreter."""
    tree = workdir / f"ianvs-{ref}"
    subprocess.run(["git", "-C", str(IANVS), "worktree", "add", "-q", "--detach",
                    str(tree), ref], check=True)

    example = workdir / f"example-{ref}" / "testalgorithms"
    example.mkdir(parents=True)
    (example / "taskdef.py").write_text(TASKDEF)

    pkl = workdir / f"task_index-{ref}.pkl"
    child = workdir / "unpickle.py"
    child.write_text(CHILD)

    driver = workdir / f"drive-{ref}.py"
    driver.write_text(textwrap.dedent(f'''\
        import pickle, sys
        sys.path.insert(0, {str(tree)!r})
        from core.common.utils import load_module
        load_module({str(example / "taskdef.py")!r})
        mod = next(m for n, m in sys.modules.items()
                   if n.startswith("taskdef") and hasattr(m, "TaskDefinitionByDomain"))
        cls = mod.TaskDefinitionByDomain
        obj = cls("Cityscapes")
        print("MODULE_NAME", mod.__name__)
        print("CLASS_MODULE", cls.__module__)
        with open({str(pkl)!r}, "wb") as fh:
            pickle.dump(obj, fh)
        print("PICKLED_OK")
    '''))

    out = subprocess.run([sys.executable, str(driver)], capture_output=True, text=True)
    info = dict(l.split(" ", 1) for l in out.stdout.strip().splitlines() if " " in l)
    if out.returncode:
        info["ERROR"] = out.stderr.strip().splitlines()[-1] if out.stderr else "?"

    # fresh interpreter, cwd elsewhere, nothing on sys.path -- exactly what a
    # later Ianvs run, another container, or the cloud side would look like
    # (a) no recovery attempt: nothing but the pickle file
    bare = subprocess.run([sys.executable, str(child), str(pkl), str(workdir / "nowhere")],
                          capture_output=True, text=True, cwd=str(workdir))
    info["UNPICKLE_bare"] = (bare.stdout or bare.stderr).strip()
    # (b) recovery attempt: put the Example source directory on sys.path,
    #     exactly what load_module() itself does
    rec = subprocess.run([sys.executable, str(child), str(pkl), str(example)],
                         capture_output=True, text=True, cwd=str(workdir))
    info["UNPICKLE_recover"] = (rec.stdout or rec.stderr).strip()
    subprocess.run(["git", "-C", str(IANVS), "worktree", "remove", "--force", str(tree)],
                   capture_output=True)
    return info


def main():
    heads = {r: subprocess.run(["git", "-C", str(IANVS), "rev-parse", "--short", r],
                               capture_output=True, text=True).stdout.strip()
             for r in ("main", "pr-558")}
    print(f"main    @ {heads['main']}")
    print(f"pr-558  @ {heads['pr-558']}\n")

    with tempfile.TemporaryDirectory() as tmp:
        wd = pathlib.Path(tmp)
        for ref in ("main", "pr-558"):
            info = run_case(ref, wd)
            print(f"--- {ref} " + "-" * (62 - len(ref)))
            for k in ("MODULE_NAME", "CLASS_MODULE", "PICKLED_OK", "ERROR"):
                if k in info:
                    print(f"  {k:<13} {info[k]}")
            print(f"  {'UNPICKLE (no sys.path help)':<28} {info['UNPICKLE_bare']}")
            print(f"  {'UNPICKLE (source dir on sys.path)':<28} {info['UNPICKLE_recover']}")
            print()


if __name__ == "__main__":
    main()
