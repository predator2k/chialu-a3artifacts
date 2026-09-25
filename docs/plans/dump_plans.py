"""Dump, for one target, the structure manifest and what each plan does to it.

A plan is a datapath sharing scheme over a FIXED structure set: `register_op` builds the
structures from the mode's format and the op list alone, so every plan of one target sees
the same manifest and differs only in which structures share one physical unit. This dump
shows both halves side by side: the manifest once, then per plan the groups it forms, the
family each group is pinned to, and the variables it leaves free to the micro-architecture.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from harness import context, plans_of, family_choices, group_map


def dump(target: str, out_dir: Path, run_dir: str, max_plans: int = 8):
    from chialu.plans import partition_of_plan, plan_vars, SHARING_FAMILY
    inst, ctx, man = context(target, run_dir)
    plans = plans_of(inst, man)
    fc = family_choices(inst, man)
    out_dir.mkdir(parents=True, exist_ok=True)
    name = Path(target).stem

    L = [f"# `{name}` — structures\n",
         f"target: `{target}`  ·  structures: {len(list(man))}  ·  "
         f"slotted: {sum(1 for s in man if s.slot)}  ·  plans: {len(plans)}  ·  "
         f"free micro-architecture variables: {len(fc)}\n",
         "Every plan below shares this one manifest: `register_op` derives the structure set from the",
         "mode's format and its op list alone, with no reference to any family choice, so sharing is the",
         "only thing a plan varies.\n",
         "| id | kind | slot | mode | lane | width | format | ops | library |",
         "|---|---|---|---|---|---|---|---|---|"]
    for s in man:
        ops = ",".join(s.ops)[:44]
        L.append(f"| `{s.id}` | {s.kind} | {s.slot or '—'} | {s.mode} | {s.lane} | {s.width} | "
                 f"`{s.format}` | {ops} | {'yes' if s.library else 'no'} |")

    L += ["", "## Micro-architecture variables (free in every plan)", "",
          "| variable | members |", "|---|---|"]
    for k, v in sorted(fc.items()):
        L.append(f"| `{k}` | {', '.join(map(str, v))} |")

    # An even spread rather than the first N: `sharing_schemes` enumerates the rules in a fixed
    # order, so the head of a 144-plan list is 8 plans that differ in one rule each. The spread
    # shows the range -- no sharing at one end, most kinds shared at the other.
    step = max(1, len(plans) // max_plans)
    shown = plans[::step][:max_plans]
    if plans and plans[-1] not in shown:
        shown[-1] = plans[-1]
    L += ["", f"## Plans ({len(shown)} of {len(plans)}, evenly spread through the enumeration)", ""]
    for pname, plan in shown:
        raw = partition_of_plan(man, plan)
        groups = [(n, m) for n, m in raw if len(m) >= 2]
        try:
            pv = plan_vars(ctx, man, plan, raw)
        except Exception as e:                                   # noqa: BLE001
            pv = {"<error>": str(e)[:120]}
        tie = group_map(man, plan, fc)
        L += [f"### `{pname}`", "",
              f"units: {len(raw)}  ·  shared groups: {len(groups)}  ·  "
              f"variables the plan pins: {len(pv)}  ·  tied to a group representative: {len(tie)}", ""]
        if groups:
            L += ["| unit | members | kind | family the sharing requires |", "|---|---|---|---|"]
            for n, m in groups:
                kinds = sorted({man.get(i).kind for i in m if man.get(i)})
                req = sorted({str(SHARING_FAMILY.get(k)) for k in kinds})
                req = ", ".join(r for r in req if r != "None") or "— (a micro-architecture: one draw per group)"
                L.append(f"| `{n}` | {', '.join(f'`{i}`' for i in m)} | {', '.join(kinds)} | {req} |")
        else:
            L.append("No shared group: every structure is its own unit.")
        if pv:
            L += ["", "<details><summary>variables the plan pins</summary>", "", "```"]
            L += [f"{k} = {v}" for k, v in sorted(pv.items())]
            L += ["```", "", "</details>"]
        L += ["", "<details><summary>plan JSON</summary>", "", "```json",
              json.dumps(plan, indent=2, sort_keys=True), "```", "", "</details>", ""]

    (out_dir / f"{name}.md").write_text("\n".join(L) + "\n")
    (out_dir / f"{name}.plans.json").write_text(
        json.dumps({"target": target,
                    "structures": [dict(id=s.id, kind=s.kind, slot=s.slot, index=getattr(s, "index", None),
                                        mode=s.mode, lane=s.lane, width=s.width, format=s.format,
                                        ops=list(s.ops), library=s.library) for s in man],
                    "micro_vars": {k: list(map(str, v)) for k, v in sorted(fc.items())},
                    "plans": [{"name": n, "plan": p} for n, p in plans]}, indent=2, sort_keys=True) + "\n")
    return name, len(list(man)), len(plans), len(fc)


if __name__ == "__main__":
    out = Path("$A3EVAL/docs/plans")
    for tgt, rd, n in [("targets/eval/fp_alu_cmp_plans.yaml", "fpcd", 8),
                       ("targets/mixed_cvt_alu.yaml", "mixd", 8),
                       ("targets/int_subword_alu.yaml", "intd", 8)]:
        try:
            print("%-22s structures=%-4d plans=%-4d micro_vars=%d" %
                  dump(tgt, out, f"$CHIALU_HOME/tmp/a3eval/{rd}", n))
        except Exception as e:                                   # noqa: BLE001
            print(f"{tgt}: {type(e).__name__}: {e}")
