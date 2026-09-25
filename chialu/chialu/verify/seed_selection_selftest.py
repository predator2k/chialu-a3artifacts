"""Check that an explicit family reaches its own seed structure without fallback."""
from chialu.targets.rtl.alu_seed import alu_seed
from chialu.targets.rtl.families.selection import SelectionError, SelectionTrace, SelectedPins, reachable_modules, track_factory
from chialu.verify.alu_ref import normalize_spec


def spec(formats, operations):
    return normalize_spec({"unit": "alu", "modes": [{"format": fmt, "count": 1} for fmt in formats],
                           "ops": operations, "check_en": False})


def main():
    integer = spec(["int8"], ["add", "sub"])
    for family, pins in (("ripple_carry", {"chunk_width_bits": 7}),
                         ("carry_skip", {"block_width": 3, "block_adder.family": "carry_lookahead"})):
        seed = alu_seed(integer, families={"core.adder.m0": (family, pins)})
        assert any(n.startswith("fam_") for n in reachable_modules(seed.text, "alu_core"))
    fp = spec(["fp16"], ["fadd", "fsub"])
    alu_seed(fp, families={"core.fp_adder.m0": ("single_path", {})})
    ones = spec(["int8_ones"], ["add", "sub"])
    alu_seed(ones, families={"core.adder.m0": ("end_around_carry", {"modulus": "mod_2n_minus_1"})})
    tail = alu_seed(spec(["int24"], ["add", "sub"]), families={"core.adder.m0": ("carry_skip", {
        "block_width": 16, "block_adder.family": "ripple_carry", "block_adder.chunk_width_bits": 16})})
    partial = [effect for effect in tail.fidelity["effects"] if effect["partial"]]
    assert len(partial) == 1 and partial[0]["requested"] == 16 and partial[0]["effective"] == 8
    assert ".CHUNK(16)" in tail.text
    alu_seed(spec(["int8_sm", "int8"], ["add"]),
             families={"core.adder.m0": ("ripple_carry", {}), "core.adder.m1": ("ripple_carry", {})})
    rejected = [(integer, {"core.adder.m0": ("unknown", {})}),
                (integer, {"core.adder.m1": ("ripple_carry", {})}),
                (ones, {"core.adder.m0": ("end_around_carry", {"modulus": "generic_p_correction", "modulus_value": 127})}),
                (integer, {"core.adder.m0": ("carry_skip", {"block_width": 16})}),
                (integer, {"core.adder.m0": ("ripple_carry", {"chunk_width_bits": 16})})]
    rejected += [(integer, {"core.adder.m0": ("ripple_carry", {"unknown_pin": 1})}),
                 (spec(["int64"], ["add"]), {"core.adder.m0": ("carry_skip", {
                     "block_width": 2, "block_adder.family": "ripple_carry", "block_adder.chunk_width_bits": 16})}),
                 (integer, {"core.adder.m0": ("carry_select", {"duplication": "full_duplicate",
                                                             "add_one.family": "prefix_and_incrementer"})})]
    for request, selections in rejected:
        try:
            alu_seed(request, families=selections)
        except SelectionError:
            pass
        else:
            raise AssertionError(f"unrealized explicit selection accepted: {selections}")
    fake = "module top(input a,output y); assign y=a; // unused u(.a(a),.y(y));\nendmodule\n" \
           "module unused(input a,output y); assign y=a; endmodule\n"
    assert reachable_modules(fake, "top") == {"top"}
    from chialu.targets.rtl import families as FAM
    supplied = SelectedPins("core.adder.m0", {"chunk_width_bits": 8})
    with SelectionTrace() as trace:
        FAM.adder_module("ripple_carry", supplied, 8)
    wrong_parameters = "module top(input [7:0] a,b,output [7:0] s); " \
        "fam_adder_ripple_carry #(.W(8),.CHUNK(4),.FORM(0)) u(.a(a),.b(b),.cin(1'b0),.s(s),.cout()); endmodule\n" \
        + FAM.module_text("fam_adder_ripple_carry")
    try:
        trace.check({supplied.owner: ("ripple_carry", supplied)}, wrong_parameters, "top")
    except SelectionError:
        pass
    else:
        raise AssertionError("a static module instantiated with different parameters counted as the requested variant")
    trace.check({supplied.owner: ("ripple_carry", supplied)}, wrong_parameters.replace(".CHUNK(4)", ".CHUNK(8)"), "top")
    original = FAM.posit_module
    def missing_decoder(kind, family, pins, *args, **kwargs):
        return None if kind == "decode" else original(kind, family, pins, *args, **kwargs)
    FAM.posit_module = track_factory(missing_decoder)
    try:
        try:
            alu_seed(spec(["posit8_0"], ["fadd"]), families={"core.posit_unit.m0": ("posit_adder_multiplier", {})})
        except SelectionError:
            pass
        else:
            raise AssertionError("an encoder concealed a missing decoder")
    finally:
        FAM.posit_module = original
    print("PASS explicit selections, pin preservation, mode ownership, unused modules and fallback rejection")


if __name__ == "__main__":
    main()
