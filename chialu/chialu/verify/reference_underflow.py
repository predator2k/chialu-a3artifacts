"""The observable underflow quirk of the 16-bit MERGED reference datapath.

The narrow destination uses MAN_BITS to index a SUPER_MAN_BITS sticky
vector. For the supported multiply operands that selected bit is zero.
Thus RNE detects tininess before rounding on lane zero of bf16/fp8;
the full-width fp16 and dedicated second fp8 lane retain IEEE after.
This is bug compatibility, not an alternative definition of IEEE after.
"""


def validate(spec):
    if spec.get("underflow_contract", "ieee") == "ieee":
        return
    from adir import BindError
    expected = [(1, "fp16"), (1, "bf16"), (2, "fp8e5m2")]
    if (spec.get("underflow_contract") != "fpnew_merged_16"
            or [(m["count"], m["format"]) for m in spec["modes"]] != expected
            or set(spec["ops"]) - {"fadd", "fsub", "fmul", "fmin", "fmax", "fcmp"}
            or set(spec["rounding"]) - {"RNE", "RTZ", "RDN", "RUP"}
            or spec.get("tininess", "after") != "after"
            or any(spec.get("daz_in", [False])) or any(spec.get("ftz_out", [False]))
            or any(spec.get("unary_dual", [False]))):
        raise BindError("fpnew_merged_16 requires the fp16/bf16/2xfp8e5m2 comparison modes, "
                        "basic ALU ops, IEEE rounding modes, tininess after and no DAZ/FTZ/dual")


def lane_tininess(conv, format_name, lane, op, rounding):
    if (conv.get("underflow_contract") == "fpnew_merged_16" and op == "fmul"
            and rounding == "RNE" and lane == 0 and format_name in ("bf16", "fp8e5m2")):
        return "before"
    return conv.get("tininess", "after")
