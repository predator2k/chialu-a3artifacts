"""The front of a numeric run as seeds of the search run.

    python3 -m chialu.front_seeds <target.yaml> --numeric-run <dir> --run-dir <dir> [--top 8]

The numeric run's archive (`results_db.jsonl`) holds one record per
declaration the backend evaluated, with the estimate node's area and
delay as its goal values. The feasible records' Pareto front is taken,
at most `top` points spread along it are kept, the fastest first (the
search run lists no seed of its own, so the first plan is its score
reference and the `seed.*` its area screens read), and each becomes a
plan in the search run's `discovered.json`: `structures` entries with
the point's family and choices per structure, a `components` entry for
the subword family, and a `why` naming the estimate. `adir seeds` and `adir run` render a
plan through `plan_seed`, so the front's declarations reach the search
as seeds without a change to the run file; every plan is rendered here
once, and one the seed cannot realize is dropped with its reason.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def front(records: list) -> list:
    """The non-dominated feasible records under minimization of every goal value."""
    feas = [r for r in records if r.get("feasible") and not r.get("hard_fail")
            and all(v is not None for v in (r.get("goal_values") or []))]
    out = []
    for r in feas:
        g = r["goal_values"]
        if any(all(o["goal_values"][i] <= g[i] for i in range(len(g))) and o["goal_values"] != g for o in feas):
            continue
        out.append(r)
    return sorted(out, key=lambda r: tuple(r["goal_values"]))


def spread(points: list, k: int) -> list:
    """At most k points spread evenly along a list ordered by the first goal."""
    if len(points) <= k:
        return points
    idx = sorted({round(i * (len(points) - 1) / (k - 1)) for i in range(k)})
    return [points[i] for i in idx]


def declared(record: dict) -> dict:
    """The record's point as `core.*` variables and implementation options: the declaration node's
    bound value where the archive holds it (every active variable, defaults
    included, so a family's inactive choices never appear), else the
    search's declared variables."""
    decl = ((record.get("measurements") or {}).get("declaration") or {}).get("value") or {}
    bound = {k[len("decl."):]: v for k, v in decl.items() if isinstance(k, str) and (k.startswith("decl.core.") or k == "decl.x_form")}
    return bound or dict((record.get("declarations") or {}).get("vars") or {})


INACTIVE_LIST_RE = re.compile(r"inactive under the selected families: \[([^\]]*)\]")
INACTIVE_ONE_RE = re.compile(r"(?:^|\s)(core\.[\w.]+): inactive")


def inactive_names(error: Exception) -> set:
    """The variables a plan_seed rejection names as inactive (a numeric
    backend assigns every variable of the space, active or not, and the
    front end refuses an explicit value on an inactive one), else empty."""
    text = str(error)
    m = INACTIVE_LIST_RE.search(text)
    if m:
        return {x.strip().strip("'\"") for x in m.group(1).split(",") if x.strip()}
    return set(INACTIVE_ONE_RE.findall(text))


PIN_VALUE_RE = re.compile(r"(\w+)=('?)([^'\s]*)\2 is outside")
SLOT_PIN_RE = re.compile(r"(?:^|\s)(\w+)\.(\w+) requires")
FAMILY_RE = re.compile(r"(\w+) family '(\w+)' rejected its pins at width")
PARTITION_RE = re.compile(r"(\w+) partition must share")


def offending_pins(error: Exception, vars_: dict) -> set:
    """The variables a realization rejection names by pin and value
    (`block_sizing='variable_ramp' is outside enum[...]`,
    `chain_segment_length=10 is outside 2..8 by 1`: the numeric space
    admits a value the selected family does not construct at this
    width), as the names of every variable with that last component
    and value."""
    out = set()
    for pin, _q, value in PIN_VALUE_RE.findall(str(error)):
        out |= {n for n, v in vars_.items() if n.split(".")[-1] == pin and str(v) == value}
    for slot, name in SLOT_PIN_RE.findall(str(error)):
        # `rounder.shared_across_formats requires two distinct selected formats`: a pin of the slot, or a family
        # of the slot the numeric space admits where the mode has one format (the structure then keeps its default)
        out |= {n for n, v in vars_.items() if n.split(".")[1:2] == [slot]
                and (n.split(".")[-1] == name or (n.endswith(".family") and str(v) == name))}
    for _kind, fam in FAMILY_RE.findall(str(error)):
        # `adder family 'sparse_prefix_hybrid' rejected its pins at width 13`: an inner structure's family that
        # does not construct at its width; every declaration of that family goes (the slot keeps its default)
        out |= {n for n, v in vars_.items() if n.endswith(".family") and str(v) == fam}
    for fam in PARTITION_RE.findall(str(error)):
        # `alu_pg_fused partition must share m1.l0.logic and m1.l0.adder`: a family that realizes two kinds in one
        # unit, which a plan states as a group rather than as a family; the structures keep their defaults
        out |= {n for n, v in vars_.items() if n.endswith(".family") and str(v) == fam}
    return out


# what a plan keeps of a point, by level: everything; the structures' families at every depth without their
# pins; the structures' own families alone (core.<slot>.<index>.family). The subword component stays at every level.
LEVELS = ("full", "families", "structure_families")


def kept(name: str, level: str) -> bool:
    if name == "x_form":
        return True
    parts = name.split(".")
    if len(parts) < 2:
        return False
    if parts[1] == "subword" or level == "full":
        return True
    if not name.endswith(".family"):
        return False
    return level == "families" or len(parts) == 4


def plan_of(record: dict, manifest, k: int, exclude: set = frozenset(), level: str = "full",
            scheme: dict | None = None) -> dict:
    """A plan (chialu.plans.PLAN_DOC) declaring the record's families and
    choices, without the variables in `exclude`, reduced to `level`
    (LEVELS), on top of a sharing `scheme` (its `shared` groups and
    `components` stand; a group without a family takes its first
    member's, and its members carry no entries of their own). `manifest`
    is the seed generator's structure manifest: a declaration
    `core.<slot>.<index>.*` names every library structure of that slot
    and index (the lanes of a mode share one), and each of them gets the
    entry."""
    import copy
    from chialu.targets.rtl.structures import is_inline
    from chialu.surrogate_features import scheme_repair
    values = scheme_repair(declared(record), scheme) if scheme else declared(record)
    vars_ = {n: v for n, v in values.items() if n not in exclude and kept(n, level)}
    by_index: dict = {}
    for st in manifest:
        if st.slot and st.index is not None and st.library and not is_inline(st):
            by_index.setdefault((st.slot, str(st.index)), []).append(st.id)
    shared = copy.deepcopy((scheme or {}).get("shared") or {})
    group_of = {m: g for g, spec in shared.items() for m in (spec.get("members") or [])}
    structures: dict = {}
    components: dict = copy.deepcopy((scheme or {}).get("components") or {})
    # A shared slot takes all choices from one canonical owner. Discarding
    # its pins here used to make the rendered design differ from the point
    # priced by the numeric/surrogate stage.
    owners = {g: min(members, key=lambda sid: (manifest.get(sid).mode, manifest.get(sid).lane))
              for g, entry in shared.items() if (members := entry.get("members"))}
    for name, value in vars_.items():
        parts = name.split(".")
        if parts[0] != "core" or len(parts) < 3:
            continue
        slot = parts[1]
        if slot == "subword":
            if scheme and "subword" in components:
                continue                              # the scheme fixes the subword family
            entry = components.setdefault("subword", {"pin": {}})
            if parts[2] == "family":
                entry["family"] = value
            else:
                entry["pin"][".".join(parts[2:])] = value
            continue
        # the longest index prefix that names a structure (an index may be dotted: m1.fp16)
        hit = None
        for n in range(len(parts) - 1, 2, -1):
            index = ".".join(parts[2:n])
            if (slot, index) in by_index:
                hit = (by_index[(slot, index)], ".".join(parts[n:]))
                break
        if hit is None:
            continue
        sids, choice = hit
        for sid in sids:
            g = group_of.get(sid)
            if g is not None:
                # a member of a shared group: the group's family is the first member's where the sharing left
                # it open (an adder bank); a member's own entries would contradict the group
                if choice == "family" and not shared[g].get("family"):
                    shared[g]["family"] = value
                elif choice != "family" and sid == owners[g] and slot in (
                        "fp_adder", "fp_multiplier", "fp_comparator", "fp_divider", "rounder", "unpacker"):
                    shared[g].setdefault("pin", {}).setdefault(choice, value)
                continue
            entry = structures.setdefault(sid, {"pin": {}})
            if choice == "family":
                entry["family"] = value
            else:
                entry["pin"][choice] = value
    for sid, entry in ((scheme or {}).get("structures") or {}).items():
        dest = structures.setdefault(sid, {})
        if entry.get("family"):
            dest.setdefault("family", entry["family"])
        dest.setdefault("pin", {}).update(entry.get("pin") or {})
    goals = record.get("goal_values") or []
    why = f"front point {k} of the numeric stage: estimated area {goals[0]:.0f} um2, delay {goals[1]:.0f} ps" \
        if len(goals) >= 2 else f"front point {k} of the numeric stage"
    if scheme:
        why += f"; sharing scheme {record.get('_scheme_name', '')}".rstrip()
    plan = {"structures": structures, "why": why}
    if "x_form" in vars_:
        plan["options"] = {"x_form": vars_["x_form"]}
    if shared:
        plan["shared"] = shared
    if components:
        plan["components"] = components
    return plan


def realize(inst, ctx, manifest, rec: dict, name: str, k: int, scheme: dict | None = None) -> tuple:
    """(plan, None) of a record the seed renders, or (None, reason). A
    rejection that names inactive or unconstructible choices drops them
    and renders again; one that names none reduces the plan to the next
    level of LEVELS (the numeric space admits values the seed's
    realization refuses together); a plan that fails at the last level is
    dropped. The plan names what was dropped (`dropped`) and why it was
    reduced (`reduced_after`)."""
    exclude: set = set()
    level, reduced_after = 0, []
    plan = None
    for _attempt in range(160):
        plan = plan_of(rec, manifest, k, exclude, LEVELS[level], scheme)
        try:
            inst.template.plan_seed(ctx, name, plan)
        except Exception as e:  # noqa: BLE001
            names = (inactive_names(e) or offending_pins(e, declared(rec))) - exclude
            if names:
                exclude |= names
                continue
            if level + 1 < len(LEVELS):
                level += 1
                reduced_after.append(f"{type(e).__name__}: {str(e)[:120]}")
                continue
            return None, f"{type(e).__name__}: {str(e)[:200]}"
        break
    else:
        return None, "no rendering after 160 repairs"
    if exclude:
        plan["why"] += f"; {len(exclude)} choices the seed does not realize dropped"
        plan["dropped"] = sorted(exclude)
    if level:
        plan["why"] += f"; reduced to {LEVELS[level]}"
        plan["reduced_after"] = reduced_after
    return plan, None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target")
    ap.add_argument("--numeric-run", required=True, help="the numeric run's directory (results_db.jsonl)")
    ap.add_argument("--run-dir", required=True, help="the search run's directory (discovered.json is written there)")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--prefix", default="front")
    ap.add_argument("--per-scheme", action="store_true",
                    help="keep each sharing scheme's own estimated front (up to --top per scheme) rather than the global "
                         "front: a wider pool to screen by synthesis where the estimate misjudges shared units")
    a = ap.parse_args(argv)
    nroot = Path(a.numeric_run)
    # one numeric run, or one per sharing scheme (a subdirectory with `scheme.json` beside its archive)
    runs = [nroot] if (nroot / "results_db.jsonl").is_file() else sorted(
        d for d in nroot.iterdir() if d.is_dir() and (d / "results_db.jsonl").is_file()) if nroot.is_dir() else []
    if not runs:
        print(f"no archive under {nroot}")
        return 2
    records = []
    for d in runs:
        scheme = json.loads((d / "scheme.json").read_text()) if (d / "scheme.json").is_file() else {}
        for line in (d / "results_db.jsonl").read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                r["_scheme"] = scheme.get("plan")
                r["_scheme_name"] = scheme.get("name", d.name)
                records.append(r)
    # the front is ordered by area; the seeds are written the other way round, so the first plan is the
    # fastest (and largest) point: ADIR takes the first seed as the score reference and as the `seed.*`
    # of the run file's area screens, which a smaller reference would close on every larger candidate
    if a.per_scheme:
        chosen = []
        for name in dict.fromkeys(r["_scheme_name"] for r in records):
            chosen += list(reversed(spread(front([r for r in records if r["_scheme_name"] == name]), a.top)))
        chosen.sort(key=lambda r: r["goal_values"][1])          # fastest estimate first, as the global front
    else:
        chosen = list(reversed(spread(front(records), a.top)))
    print(f"[front_seeds] {len(records)} records over {len(runs)} run(s), {sum(1 for r in records if r.get('feasible'))} feasible, "
          f"front {len(front(records))}, kept {len(chosen)}")
    from adir.instance import load
    run = Path(a.run_dir)
    run.mkdir(parents=True, exist_ok=True)
    inst = load(a.target, run_dir_override=str(run))
    ctx = inst.ctx(run_dir=run)
    from chialu.modules.generators import spec_of
    from chialu.targets import derive
    manifest = derive.seed_alu_text(spec_of(ctx), None).structures     # the structures plan_seed itself resolves
    f = run / "discovered.json"
    doc = json.loads(f.read_text()) if f.is_file() else {"plans": {}, "rejected": {}}
    plans = dict(doc.get("plans") or {})
    plans = {k: v for k, v in plans.items() if not k.startswith(a.prefix + "_")}
    rejected = dict(doc.get("rejected") or {})
    seen_plans: dict = {}
    for k, rec in enumerate(chosen, 1):
        name = f"{a.prefix}_{k}"
        plan, err = realize(inst, ctx, manifest, rec, name, k, rec.get("_scheme"))
        if plan is None:
            rejected[name] = err
            print(f"[front_seeds] {name} dropped: {rejected[name]}")
            continue
        key = json.dumps({k: plan.get(k) for k in ("shared", "structures", "components")}, sort_keys=True)
        if key in seen_plans:
            print(f"[front_seeds] {name} is the same plan as {seen_plans[key]} after the repairs; not repeated")
            continue
        seen_plans[key] = name
        rejected.pop(name, None)           # a rejection of an earlier pass over this archive
        plans[name] = plan
        print(f"[front_seeds] {name}: {plan['why']} ({len(plan['structures'])} structures)")
    doc.update({"plans": plans, "rejected": rejected})
    f.write_text(json.dumps(doc, indent=1))
    print(f"[front_seeds] {f}: {len(plans)} plans")
    return 0


if __name__ == "__main__":
    sys.exit(main())
