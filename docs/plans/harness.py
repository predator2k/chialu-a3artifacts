"""Both sides of one micro-architecture: what the numeric model predicts, and what synthesis measures.

The two must describe the same design or the comparison is meaningless, so both start from one
`overrides` dict of VAR values: `families_of` turns it into {structure: (family, pins)}, which the
declaration the estimate node reads and the text yosys synthesizes are each built from.

The estimate is taken with area_scale = delay_scale = 1, i.e. raw: those two factors are what this
experiment is trying to measure, so feeding the calibrated ones back in would hide the answer.
"""
import json, random
from pathlib import Path


def context(target: str, run_dir: str):
    from adir.instance import load
    from chialu.modules.generators import spec_of
    from chialu.targets import derive
    inst = load(target, run_dir_override=run_dir)
    ctx = inst.ctx(run_dir=Path(run_dir))
    manifest = derive.seed_alu_text(spec_of(ctx), None).structures
    return inst, ctx, manifest


def plans_of(inst, manifest, level="natural"):
    from chialu.plans import sharing_schemes
    def admits(sid, family):
        st = manifest.get(sid)
        b = inst.bindings.get(f"core.{st.slot}.{st.index}.family") if st is not None else None
        if b is None:
            return False
        return b.value == family if b.time == "fixed" else b.domain.contains(family)
    return list(sharing_schemes(manifest, level, admits))


def family_choices(inst, manifest):
    """{var name: [members]} for every structure's top-level family that the run file searches."""
    out = {}
    for s in manifest:
        if not s.slot:
            continue
        name = f"core.{s.slot}.{s.index}.family"
        b = inst.bindings.get(name)
        if b is None or b.time == "fixed":
            continue
        try:
            members = list(b.domain.members())
        except Exception:                                   # noqa: BLE001
            continue
        if len(members) > 1:
            out[name] = members
    # Whether a multiply-add is fused is a sharing decision, not a micro-architecture one: a
    # fused family is only renderable under a partition that groups the adder, the multiplier
    # and the fma, so it belongs to the plan layer and the plan's own vars set it. Sampling it
    # here would make almost every draw unrenderable -- four of the five families are fused, so
    # a four-mode unit draws a legal set once in about six hundred tries.
    # A family domain mixes two different kinds of decision. `single_path` and `two_path` are
    # micro-architectures; `shared_across_formats` and `shared_per_lane` are sharing patterns,
    # which the plan already states and whose partition it already built -- declaring one here
    # contradicts the plan and the render refuses it. SHARING_FAMILY names them for the kinds
    # that have one, and every member called `shared_*` is one by construction. Whether a
    # multiply-add is fused is a sharing decision too, so the whole variable goes to the plan.
    from chialu.plans import SHARING_FAMILY
    micro = {}
    for k, members in out.items():
        if ".fp_fma." in k:
            continue
        kind = k.split(".")[1]
        drop = {SHARING_FAMILY.get(kind)} | {m for m in members if str(m).startswith("shared_")}
        keep = [m for m in members if m not in drop]
        if len(keep) > 1:
            micro[k] = keep
    return micro


def group_map(manifest, plan, fc):
    """{var name: representative var name} — the variables a plan's sharing groups tie together.

    A shared group is one physical module, so its members declare one family and one pin set;
    `partition.py` refuses a group whose members chose differently ("physical sharing is not
    implemented for these selected structures"). The plan says which structures are one module,
    but for the arithmetic kinds it does not say which family that module is -- SHARING_FAMILY
    maps them to None because there their family is a micro-architecture, not a sharing pattern.
    So the group is exactly one micro-architecture decision, and the sampler must draw it once
    and write it to every member rather than draw per structure and contradict itself.
    """
    from chialu.plans import partition_of_plan
    tie = {}
    for _name, members in partition_of_plan(manifest, plan):
        keys = []
        for sid in members:
            st = manifest.get(sid)
            if st is not None and st.slot:
                k = f"core.{st.slot}.{st.index}.family"
                if k in fc:
                    keys.append(k)
        for k in keys[1:]:
            tie[k] = keys[0]
    return tie


def tie_group(ctx, overrides, tie):
    """One draw per group: every tied variable takes its representative's value, where legal.

    A member whose domain excludes the representative's family keeps its own draw; the render
    then refuses that pair, and the skip is reported rather than hidden.
    """
    out = dict(overrides)
    for k, rep in tie.items():
        v = out.get(rep)
        b = ctx.bindings.get(k)
        if v is not None and b is not None and b.time == "search" and b.domain.contains(v):
            out[k] = v
    return out


def declaration(ctx, manifest, overrides):
    from chialu.modules.generators import families_of
    decl = {}
    for base, (fam, pins) in families_of(ctx, manifest, overrides).items():
        d = decl
        for part in base.split(".")[1:]:
            d = d.setdefault(part, {})
        d["family"] = fam
        for k, v in (pins or {}).items():
            dd = d
            ks = str(k).split(".")
            for part in ks[:-1]:
                dd = dd.setdefault(part, {})
            dd[ks[-1]] = v
    return decl


def sample_random(fc, rng):
    """Every family variable drawn independently from its own members."""
    return {k: rng.choice(v) for k, v in fc.items()}


def sample_spread(fc, rng, i, n):
    """A stratified draw: variable j takes member (i * stride_j) mod |members|.

    Independent uniform draws concentrate near the middle of a product space -- most
    samples end up a couple of swaps away from each other, which is the opposite of
    what a coefficient fit wants. Walking each variable at its own stride sweeps the
    corners as well, so the 300 designs of one plan differ in many structures at once
    rather than in one or two.
    """
    out = {}
    for j, (k, members) in enumerate(sorted(fc.items())):
        stride = 1 + (j % max(1, len(members) - 1))
        out[k] = members[(i * stride + j) % len(members)]
    # a quarter of the variables re-randomized, so the walk does not become a lattice
    for k in rng.sample(sorted(fc), max(1, len(fc) // 4)):
        out[k] = rng.choice(fc[k])
    return out


def measure(inst, ctx, manifest, plan, overrides, pdk="nangate45", effort="medium",
            glue_json="", context_json=""):
    """(estimate, synthesis) for one design, or an error string."""
    import json as _json
    from adir.registry import underlying
    from chialu import eda
    from chialu.plans import partition_of_plan, plan_vars, _render
    from chialu.modules.generators import spec_of, seed_output, split_fixed_families
    spec = _json.dumps(spec_of(ctx))
    raw = partition_of_plan(manifest, plan)
    vars_ = plan_vars(ctx, manifest, plan, raw)
    # The plan wins every key it states. A sharing group does not merely group its members: it
    # requires the family that implements that sharing (SHARING_FAMILY -- a shared multiplier is
    # `twin_precision_subword`, a shared logic row is `wide_gate_row`), and plan_vars has already
    # pinned it. Letting a sampled family overwrite that pin contradicts the partition, and the
    # render refuses the pair -- which is what skipped five of every six draws on mixed_cvt_alu.
    # So the sampler only fills the structures the plan left free, and `free` is what this design
    # actually varies.
    overrides = tie_group(ctx, overrides, group_map(manifest, plan, overrides))
    free = {k: v for k, v in overrides.items() if k not in vars_}
    varied = len(free)
    vars_.update(free)
    # The space is conditional: a fused fp_fma leaves the separate adder's and multiplier's
    # family variables with nothing to name, and families_of rejects a declaration that sets
    # them. Rather than reimplement the condition tree here, let it say which keys are
    # inactive and drop those, which is self-correcting as the tree changes upstream.
    for _ in range(8):
        try:
            decl = declaration(ctx, manifest, vars_)
            break
        except ValueError as e:
            import re as _re
            dead = _re.findall(r"'([\w.*]+)'", str(e))
            if "inactive" not in str(e) or not dead:
                return {"ok": False, "detail": str(e)[:200]}, {"ok": False}, 0
            for k in dead:
                vars_.pop(k, None)
    else:
        return {"ok": False, "detail": "could not settle the declaration"}, {"ok": False}, 0
    est = underlying(eda.estimate)({"spec.json": spec}, decl, pdk, effort,
                                   1.0, 1.0, _json.dumps(plan), glue_json, context_json)
    # A family and a plan can also disagree: a fused multiply-add is only renderable under a
    # partition that shares the adder, the multiplier and the fma, so the cross of plans and
    # families is not free. An unrenderable pair is reported rather than raised -- how large
    # that fraction is, is itself part of what the experiment measures.
    partition = split_fixed_families(raw, manifest, ctx.bindings)
    try:
        st = _render(ctx, partition, vars_)
        text = seed_output(ctx, st)
    except Exception as e:                       # noqa: BLE001
        return est, {"ok": False, "skip": f"{type(e).__name__}: {str(e)[:120]}", "varied": varied}, 0
    if isinstance(text, tuple):
        text = text[0]
    structures = [dict(id=s.id, kind=s.kind, slot=s.slot, index=s.index) for s in st.structures if s.slot]
    ppa = underlying(eda.synth_ppa)(text, "alu_core", pdk, int(ctx.bindings["clock_ps"].value),
                                    repeats=int(inst.raw.get("evaluate", {}).get("nodes", {}).get("synth_ppa", {}).get("inputs", {}).get("repeats", 5)),
                                    timeout_s=900, effort=effort)
    ppa = dict(ppa); ppa["varied"] = varied
    return est, ppa, len(structures)
