#!/usr/bin/env python3
"""PR #558 gives a unique identity to the file Ianvs loads directly, but not to
the modules that file imports itself.

@Aryansingh-ai raised this on the PR as a compatibility concern and stated it was
not demonstrated by their tests. This demonstrates it.

Fixture mirrors the real shape of the repository: two Examples, each with its own
`basemodel.py` (41 such files exist) that imports its own sibling `utils.py`
(10 such files exist).

Usage: python3 tools/probe_pr558_transitive.py [path/to/ianvs]
"""
import pathlib, subprocess, sys, tempfile, textwrap

IANVS = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "ianvs").resolve()

UTILS = 'ORIGIN = "{ex}"\ndef scale(x):\n    return x * {factor}\n'
BASEMODEL = textwrap.dedent('''\
    """Stand-in for an Example basemodel.py that imports its own sibling utils.py."""
    import utils
    ORIGIN = "{ex}"
    def predict(x):
        return utils.scale(x)
    SIBLING_ORIGIN = utils.ORIGIN
''')


def build(root, ex, factor):
    d = root / ex / "testalgorithms"
    d.mkdir(parents=True)
    (d / "utils.py").write_text(UTILS.format(ex=ex, factor=factor))
    (d / "basemodel.py").write_text(BASEMODEL.format(ex=ex))
    return d / "basemodel.py"


def run(ref, wd):
    tree = wd / f"ianvs-{ref}"
    subprocess.run(["git", "-C", str(IANVS), "worktree", "add", "-q", "--detach",
                    str(tree), ref], check=True)
    a = build(wd / f"w-{ref}", "example_A", 1)
    b = build(wd / f"w-{ref}", "example_B", 100)
    driver = wd / f"drive-{ref}.py"
    driver.write_text(textwrap.dedent(f'''\
        import sys
        sys.path.insert(0, {str(tree)!r})
        from core.common.utils import load_module
        out = []
        for label, path in (("A", {str(a)!r}), ("B", {str(b)!r})):
            load_module(path)
            # what the framework would resolve for THIS test case: the most recent
            # basemodel entry, which is what ClassFactory.get_cls() would find too
            keys = [n for n in sys.modules if n.startswith("basemodel")]
            m = sys.modules[keys[-1]]
            out.append((label, m.__name__, m.ORIGIN, m.SIBLING_ORIGIN,
                        m.predict(1), len(keys)))
        for row in out:
            print("|".join(str(x) for x in row))
        print("UTILS_KEYS|" + ",".join(sorted(n for n in sys.modules if n.startswith("utils"))))
    '''))
    r = subprocess.run([sys.executable, str(driver)], capture_output=True, text=True)
    subprocess.run(["git", "-C", str(IANVS), "worktree", "remove", "--force", str(tree)],
                   capture_output=True)
    return r.stdout.strip() or r.stderr.strip()


with tempfile.TemporaryDirectory() as tmp:
    wd = pathlib.Path(tmp)
    for ref in ("main", "pr-558"):
        head = subprocess.run(["git", "-C", str(IANVS), "rev-parse", "--short", ref],
                              capture_output=True, text=True).stdout.strip()
        print(f"--- {ref} @ {head} " + "-" * (46 - len(ref)))
        print(f"  {'load':<6}{'resolved sys.modules key':<46}{'its code':<12}{'its utils':<12}{'predict(1)':<12}{'#keys'}")
        for line in run(ref, wd).splitlines():
            p = line.split("|")
            if p[0] == "UTILS_KEYS":
                print(f"\n  sys.modules keys for utils: {p[1]}")
            else:
                print(f"  {p[0]:<6}{p[1]:<46}{p[2]:<12}{p[3]:<12}{p[4]:<12}{p[5]}")
        print()
print("Expected if the fix were complete: example_B.predict(1) == 100.")
