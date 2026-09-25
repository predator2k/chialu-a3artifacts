"""The plain baseline programs of the ALU comparison targets, the seed of the
generic-evolution controls (make_targets.FREE_SEEDS).

    python3 targets/make_plain_seeds.py

Each is the target's baseline rendered by the seed generator, as the chiALU
run renders it, with its ADIR declaration emptied and the generator's library
annotations removed: the library's modules stay in the text as ordinary code
(their names still carry the family they came from), and no VAR or STRUCTURE
line is left for a model to edit or for a template to re-render. The empty block is what ADIR asks of a
file seed whose instance has searched variables."""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

TARGETS = {"int_subword_alu": HERE / "int_subword_alu.yaml",
           "fp_alu_cmp": HERE / "eval" / "fp_alu_cmp.yaml",
           "fp_alu_cmp_hf": HERE / "eval" / "fp_alu_cmp_hf.yaml",
           "vec_dot_acc_cmp_fp16": HERE / "eval" / "vec_dot_acc_cmp_fp16.yaml",
           "vec_dot_acc_cmp_fp8": HERE / "eval" / "vec_dot_acc_cmp_fp8.yaml",
           "vec_dot_acc_cmp": HERE / "eval" / "vec_dot_acc_cmp.yaml"}
_BLOCK = re.compile(r"^[ \t]*//[ \t]*ADIR-DECL v1\n.*?^[ \t]*//[ \t]*ADIR-END[ \t]*\n", re.S | re.M)
_EVOLVE = re.compile(r"^[ \t]*//[ \t]*(EVOLVE-BLOCK-(START|END)|ADIR-MEMBER)\b.*\n", re.M)
# the generator's annotations of the library: the structure and unit manifests, the library and hierarchy
# lists and the "structure core.<slot>: family <f> realized by the library module" line above each instance
_ANNOTATION = re.compile(r"^[ \t]*//[ \t]*(//[ \t]*)?(STRUCTURE|UNIT|LIBRARY|HIERARCHY)\b.*\n"
                         r"|^[ \t]*//[ \t]*structure core\.[^\n]*\n"
                         r"|^[ \t]*//[ \t]*the seed's body:[^\n]*\n"
                         r"|^//[ \t]*---- the family library modules[^\n]*\n", re.M)


def plain_baseline(run_file: Path) -> str:
    from adir.instance import load
    from adir.seeds import _seed_texts, program_from_seed_text
    from chialu.eda import rtl_of
    inst = load(str(run_file))
    res = inst.template.seed_generator(inst.ctx(), "baseline")
    texts, vars_, lines = _seed_texts(inst.seed_artifacts()[0], res, "baseline")
    text = rtl_of(program_from_seed_text(inst, texts, vars_, lines))
    text = _ANNOTATION.sub("", _EVOLVE.sub("", _BLOCK.sub("", text)))
    if "ADIR-DECL" in text or "VAR " in text.split("module", 1)[0]:
        raise SystemExit(f"{run_file}: a declaration survived the strip")
    return "// ADIR-DECL v1\n// ADIR-END\n" + text


def main() -> int:
    out = HERE / "seeds"
    out.mkdir(exist_ok=True)
    for name, run_file in TARGETS.items():
        text = plain_baseline(run_file)
        (out / f"{name}.baseline.sv").write_text(text)
        print(f"wrote targets/seeds/{name}.baseline.sv ({len(text) / 1024:.0f} KB, "
              f"{text.count(chr(10) + 'module ')} modules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
