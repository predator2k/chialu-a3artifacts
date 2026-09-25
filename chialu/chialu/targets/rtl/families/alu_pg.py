"""Share operand propagate/generate terms between logic and an adder."""
import hashlib


def terms_module(width, owner):
    """PG terms whose sum is supplied by the unit's partitioned adder."""
    from chialu.targets.rtl import families as FAM
    from .selection import register_origin
    from .fidelity import shared
    name = f"fam_alu_pg_terms_w{width}"
    text = f"""module {name}(input logic [{width-1}:0] a, b,
    output logic [{width-1}:0] p, g);
  assign p = a ^ b;
  assign g = a & b;
endmodule
"""
    register_origin(owner, "alu_pg_fused", {}, name, text)
    shared(owner, "alu_pg_fused", [name], [owner, owner.replace(".logic.", ".adder.")],
           "The partitioned adder consumes p + (g << 1) within each lane; logic reads the same terms.")
    return FAM.Module(name, {}, text)


def fused_module(adder, width, owner, use_gate=False, consumers=None):
    from chialu.targets.rtl import families as FAM
    from .selection import register_origin
    from .fidelity import shared
    key = repr((adder.name, adder.params, adder.text, width, use_gate)).encode()
    name = "fam_alu_pg_fused_" + hashlib.sha256(key).hexdigest()[:16]
    terms = name + "_terms"
    params = ", ".join(f".{key}({value})" for key, value in adder.params.items())
    control_ports = "".join(f", input logic [{bits-1}:0] {port}" for port, bits in adder.ctrl)
    control_connections = "".join(f", .{port}({port})" for port, _ in adder.ctrl)
    shifted = f"{{pg_g[{width-2}:0], 1'b0}}" if width > 1 else "1'b0"
    if use_gate:
        shifted = f"(use_g ? {shifted} : {width}'d0)"
        control_ports += ", input logic use_g"
    high_generate = f"(use_g & pg_g[{width-1}])" if use_gate else f"pg_g[{width-1}]"
    text = f"""module {terms}(input logic [{width-1}:0] a, b,
    output logic [{width-1}:0] p, g);
  assign p = a ^ b;
  assign g = a & b;
endmodule
module {name}(input logic [{width-1}:0] a, b, input logic cin,
    output logic [{width-1}:0] s, output logic cout,
    output logic [{width-1}:0] pg_p, pg_g{control_ports});
  logic carry;
  {terms} u_terms(.a(a), .b(b), .p(pg_p), .g(pg_g));
  {adder.name} {"#(" + params + ")" if params else ""} u_sum(
    .a(pg_p), .b({shifted}), .cin(cin), .s(s), .cout(carry){control_connections});
  assign cout = carry | {high_generate};
endmodule
"""
    text += "\n" + "\n".join(FAM.module_texts(adder.name, adder.text).values())
    register_origin(owner, "alu_pg_fused", {}, name, text)
    shared(owner, "alu_pg_fused", [name + ".u_terms"],
           consumers or [owner, owner.replace(".logic.", ".adder.")],
           "The sum consumes p + (g << 1); bitwise results consume the same p and g wires.")
    return FAM.Module(name, {}, text, adder.ctrl)


def fuse_partition(manifest, partition, selections):
    """Place each selected logic row in the same lane module as its adder."""
    selected = {key for key, (family, _) in selections.items() if family == "alu_pg_fused"}
    wide = {key for key, (family, _) in selections.items() if family == "wide_gate_row"}
    if not selected and (partition is not None or not wide):
        return partition
    from chialu.targets.rtl.alu_seed import default_partition
    groups = [(name, list(members)) for name, members in (partition if partition is not None else default_partition(manifest))]
    for logic in manifest:
        if logic.kind != "logic" or f"core.logic.{logic.index}" not in selected:
            continue
        adder = next((st for st in manifest if st.kind == "adder" and st.mode == logic.mode and st.lane == logic.lane), None)
        if adder is None:
            adder = next((st for st in manifest if st.kind == "adder" and st.lane == logic.lane
                          and st.width == logic.width and st.format.startswith(("int", "uint", "fxs"))
                          and not st.format.endswith(("_sign_magnitude", "_ones_complement", "_sm", "_ones"))), None)
        if adder is None:
            raise ValueError(f"core.logic.{logic.index}: alu_pg_fused requires an adder operation in the same mode "
                             "or a binary integer companion of the same raw width and lane count")
        owners = [i for i, (_, members) in enumerate(groups) if logic.id in members or adder.id in members]
        # Fusion is a connectivity requirement, including for explicit partitions.
        # Preserve both groups: comparator/adder and other PG pairs can compose
        # transitively. validate_partition checks the resulting union, so this
        # cannot silently absorb an unsupported kind or another lane's comparator.
        if len(owners) == 2:
            first, second = owners
            groups[first][1].extend(groups[second][1])
            groups.pop(second)
    if partition is None:
        import json
        merged = {}
        for logic in manifest:
            owner = f"core.logic.{logic.index}"
            if logic.kind == "logic" and owner in wide and logic.format.startswith(("int", "uint", "fxs", "bcd")):
                key = json.dumps(selections[owner][1], sort_keys=True)
                merged.setdefault(key, []).append(logic.id)
        for members in merged.values():
            owners = [index for index, (_, group) in enumerate(groups) if any(member in group for member in members)]
            for index in reversed(owners[1:]):
                groups[owners[0]][1].extend(groups[index][1])
                groups.pop(index)
    return [(name, tuple(members)) for name, members in groups]
