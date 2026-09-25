"""Physical rounder and unpacker banks requested by explicit FP partitions."""
from chialu.targets.rtl.engine import FW, _core


def emit_format_groups(top, library, kind, selected, groups, modes, families, geometry,
                       result_count, ternary_modes, tokens, normalized):
    """Mux mutually exclusive modes, with an independent instance per lane.

    The mode buses include ungrouped lanes too. Those get their own selected
    module, so a group involving lane 0 never silently shares lane 1 as well.
    Format-specific extraction/encoding surrounds the shared arithmetic cells.
    """
    from chialu.targets.rtl import families as FAM
    from chialu.targets.rtl.families.module_library import collect_modules

    srcs = ("a", "b", "c") if any(mi in ternary_modes for mi in selected) else ("a", "b")
    for mi in selected:
        count, fmt = result_count(mi, kind), _core(modes[mi][1])
        if kind == "rounder":
            top.logic(f"rsfl_m{mi}", count * FW)
            top.logic(f"rsbits_m{mi}", count * fmt.width)
        else:
            for src in srcs:
                top.logic(f"usu{src}_m{mi}", count * (geometry.VW + 1))
    for lane in range(max(result_count(mi, kind) for mi in selected)):
        live = {mi for mi in selected if lane < result_count(mi, kind)}
        cohorts = [sorted(mi for mi in live if (mi, lane % modes[mi][0]) in group)
                   for group in groups]
        used = {mi for cohort in cohorts for mi in cohort}
        cohorts += [[mi] for mi in sorted(live - used)]
        for cohort in filter(None, cohorts):
            formats = [_core(modes[mi][1]) for mi in cohort]
            shared = len(cohort) > 1
            # Generate for every owner so selection validation records every
            # member's family and pins as realized by this physical module.
            for mi in cohort:
                family, pins = families[f"core.{kind}.m{mi}"]
                if shared:
                    module = FAM.fp_shared_module(kind, family, pins, formats, geometry, cohort,
                                                  tokens=tokens, normalized_input=normalized)
                else:
                    module = FAM.fp_module(kind, family, pins, geometry, fmt=formats[0],
                                           tokens=tokens, normalized_input=normalized)
            for module_name, module_text in FAM.module_texts(module.name, module.text).items():
                collect_modules(library, ((module_name, module_text),))
            for src in (None,) if kind == "rounder" else srcs:
                conns = {"mode": "mode"} if shared else {}
                for index, (mi, fmt) in enumerate(zip(cohort, formats)):
                    prefix = f"f{index}_" if shared else ""
                    if kind == "rounder":
                        sw, xt = geometry.sr_bits, geometry.XT
                        ports = {"x": f"rsx_m{mi}[{lane*xt} +: {xt}]",
                                 "word": f"rsword_m{mi}" if result_count(mi, kind) * sw == 1 else
                                         f"rsword_m{mi}[{lane*sw} +: {sw}]",
                                 "rnd": "rnd", "ftz": "ftz",
                                 "fl": f"rsfl_m{mi}[{lane*FW} +: {FW}]",
                                 "bits": f"rsbits_m{mi}[{lane*fmt.width} +: {fmt.width}]"}
                    else:
                        width, uw = modes[mi][1].width, geometry.VW + 1
                        arg = f"{src}[{lane*width} +: {width}]"
                        if width != fmt.width:
                            from chialu.targets.rtl.alu_mode import x87_to_core
                            arg = x87_to_core(arg)
                        ports = {"b": arg, "daz": "daz", "u": f"usu{src}_m{mi}[{lane*uw} +: {uw}]"}
                    conns.update({prefix + port: value for port, value in ports.items()})
                instance = f"u_shared_{kind}_l{lane}_m" + "_".join(map(str, cohort))
                top.instance(module.name, instance + (f"_{src}" if src else ""), conns)
