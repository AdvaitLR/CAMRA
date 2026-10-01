"""
Turn the final Kaggle notebook into the public release version.

    python scripts/prepare_release.py <final_kaggle_notebook.ipynb> notebooks/02_camra_pipeline.ipynb

What it does:
  * clears all cell outputs (logs, plots, local paths),
  * sets the full-pipeline defaults (RERUN_DRL_FL_ONLY = False, SAVE_PER_SEED_STATE = False,
    RUN_FOCAL_PRIOR_CONTROL = False, EXCLUDE_ARCH / EXCLUDE_MALWARE_FAMILY = None),
  * updates the outdated STEP 1 note about val_select,
  * syntax-checks every code cell and lists the Kaggle-specific paths that users must edit.
"""
import ast, json, re, sys

src, dst = sys.argv[1], sys.argv[2]
nb = json.load(open(src))

SETS = [
    (r"^(RERUN_DRL_FL_ONLY\s*=\s*)\w+", r"\1False"),
    (r"^(SAVE_PER_SEED_STATE\s*=\s*)\w+", r"\1False"),
    (r"^(RUN_FOCAL_PRIOR_CONTROL\s*=\s*)\w+", r"\1False"),
    (r"^(EXCLUDE_ARCH\s*:\s*Optional\[str\]\s*=\s*)[^#\n]+", r"\1None  "),
    (r"^(EXCLUDE_MALWARE_FAMILY\s*:\s*Optional\[str\]\s*=\s*)[^#\n]+", r"\1None  "),
]
OLD_NOTE = re.compile(r"`val_select` \(drives\s+early-stopping/best-checkpoint choice\)")
OLD_COMMENT = re.compile(r"val_select \(early stopping\)")
NEW_NOTE = "`val_select` (hyperparameter selection and monitoring only; every model is evaluated at its final epoch)"

applied, errors, paths = set(), [], set()
for i, c in enumerate(nb["cells"]):
    text = "".join(c["source"])
    if c["cell_type"] == "code":
        c["outputs"], c["execution_count"] = [], None
        for pat, rep in SETS:
            new = re.sub(pat, rep, text, flags=re.M)
            if new != text:
                applied.add(pat.split("\\")[0].strip("^("))
                text = new
        text = OLD_COMMENT.sub("val_select (hyperparameter selection / monitoring)", text)
        code = "\n".join(l for l in text.split("\n") if not l.lstrip().startswith(("!", "%")))
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"cell {i}, line {e.lineno}: {e.msg}")
        paths.update(re.findall(r"/kaggle/[^\s\"')]+", text))
    else:
        text = OLD_NOTE.sub(NEW_NOTE, text)
    c["source"] = text.splitlines(keepends=True)

json.dump(nb, open(dst, "w"), indent=1)
print(f"written: {dst}")
print("defaults set:", ", ".join(sorted(applied)) or "none found")
if errors:
    print("\nSYNTAX ERRORS - fix these before publishing:")
    for e in errors:
        print("  ", e)
else:
    print("syntax check: all code cells parse")
if paths:
    print("\nKaggle-specific paths (documented in the README; users point these at their own copies):")
    for p in sorted(paths):
        print("  ", p)
