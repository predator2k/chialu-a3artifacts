"""feasible_families and chialu.checkers against the static checker model.

The checks pin the model's known numbers: a residue code aliases at
1/M, two low-cost moduli at 1/(3*7), the parities at 1/2, an exact
compare at 0; a replica covers an uncovered op under `duplicate`,
`error` rejects it, `none` leaves it unchecked and is legal only
without a requirement; a rule's `choices` restrict the space, a pin
outside its domain is an error, and `emit` round-trips through the
same function.
"""
from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout

from chialu.targets.rtl.alu_checker import FAMILIES, feasibility, feasible_families
from chialu import checkers as CK

ARITH = ("add", "sub", "adc", "sbb", "neg", "abs", "mul_wide")


def by_family(points):
    out = {}
    for p in points:
        out.setdefault(p["family"], []).append(p)
    return out


def main(argv=None) -> int:
    from chialu.verify.formats import parse_format
    I16 = parse_format("int16").name
    pairs = [("int16", op) for op in ARITH]
    # every family renders at least one point without a requirement, and every point names a mechanism per pair
    cands, rej = feasibility(pairs)
    assert not rej, rej[:2]
    fams = by_family(cands)
    assert set(fams) == set(FAMILIES), sorted(set(FAMILIES) - set(fams))
    for p in cands:
        assert set(p["mechanism"]) == {f"{I16}/{op}" for op in ARITH}
        assert p["code_pairs"] + p["replica_pairs"] + p["unchecked_pairs"] == len(ARITH)
    # the model's numbers
    res = {p["pins"]["modulus"]: p for p in fams["residue"] if p["comparator"]["family"] == "direct_compare"
           and p["pins"]["generator_style"] == "csa_tree"}
    assert set(res) == {3, 7, 15, 31, 63, 255}
    for M, p in res.items():
        assert abs(p["output_alias"] - 1.0 / M) < 1e-12 and p["single_bit"] == 1.0 and p["code_pairs"] == len(ARITH)
    two = next(p for p in fams["multi_residue"] if p["pins"] == {"moduli_count": 2, "moduli_set": "low_cost_2a_minus_1"}
               and p["comparator"]["family"] == "direct_compare")
    assert two["moduli"] == [3, 7] and abs(two["output_alias"] - 1.0 / 21) < 1e-12
    assert all(p["output_alias"] == 0.5 for p in fams["parity_prediction_adder"] if p["comparator"]["family"] == "direct_compare")
    assert all(p["output_alias"] == 0.0 and p["exact"] for p in fams["duplication"] if p["comparator"]["family"] != "m_out_of_n_checker"
               or p["comparator"].get("code_class") == "one_out_of_n")
    assert all(p["replica_pairs"] == len(ARITH) and p["code_pairs"] == 0 for p in fams["duplication"])
    # a weight compare enters the model through the comparator: modulus 31 under k_out_of_2k escapes weight-preserving changes
    weight = next(p for p in fams["residue"] if p["pins"]["modulus"] == 31 and p["comparator"] == {"family": "m_out_of_n_checker", "code_class": "k_out_of_2k"})
    assert weight["output_alias"] > 1.0 / 31 and weight["single_bit"] == 0.5
    # the bound prunes: 5e-2 keeps modulus 31 and above and drops 15, the parities and Berger
    cands, rej = feasibility(pairs, {"random_alias": 5e-2, "single_bit": 1.0})
    kept = by_family(cands)
    assert {p["pins"]["modulus"] for p in kept["residue"]} == {31, 63, 255}
    assert "parity_prediction_adder" not in kept and "berger" not in kept and "inverse_residue" not in kept
    assert {p["reject_class"] for p in rej if p["family"] == "parity_prediction_adder"} == {"alias"}
    assert {p["reject_class"] for p in rej if p["family"] == "reduced_precision"} <= {"alias", "single_bit"}
    assert "duplication" in kept and "an_code" in kept                      # the exact compares pass outright
    # op coverage under the three fallbacks
    mixed = pairs + [("int16", "and"), ("int16", "shl")]
    dup, _ = feasibility(mixed, None, "duplicate", [{"family": "residue", "modulus": 31}])
    assert all(p["replica_pairs"] == 2 and p["code_pairs"] == len(ARITH) for p in dup)
    err_c, err_r = feasibility(mixed, None, "error", [{"family": "residue", "modulus": 31}, {"family": "duplication"}])
    assert not err_c and {p["reject_class"] for p in err_r} == {"coverage"}
    none_c, _ = feasibility(mixed, None, "none", [{"family": "residue", "modulus": 31}])
    assert none_c and all(p["unchecked_pairs"] == 2 for p in none_c)
    none_gated_c, none_gated_r = feasibility(mixed, {"random_alias": 0.1}, "none", [{"family": "residue", "modulus": 31}])
    assert not none_gated_c and {p["reject_class"] for p in none_gated_r} == {"coverage"}
    # a float rule: the reduced-precision replica alone codes fadd/fmul; a residue family gets a replica
    fl, _ = feasibility([("fp16", "fadd"), ("fp16", "fmul")], None, "duplicate",
                        [{"family": "reduced_precision", "replica_width_bits": 8, "bound_type": "absolute",
                          "replica_adder.family": ["parallel_prefix", "carry_select"], "replica_adder.topology": "kogge_stone"},
                         {"family": "residue"}])
    rp = [p for p in fl if p["family"] == "reduced_precision"]
    assert len(rp) == 1 and rp[0]["code_pairs"] == 2 and rp[0]["comparator"] is None
    assert rp[0]["slots"] == {"replica_adder.family": ["parallel_prefix", "carry_select"], "replica_adder.topology": "kogge_stone"}
    assert all(p["replica_pairs"] == 2 for p in fl if p["family"] == "residue")
    # lanes compound the escape
    one, _ = feasibility([("int8", "add")], None, "duplicate", [{"family": "residue", "modulus": 7, "comparator.family": "direct_compare"}])
    four, _ = feasibility([("int8", "add")], None, "duplicate", [{"family": "residue", "modulus": 7, "comparator.family": "direct_compare"}], lanes={"int8": 4})
    assert abs(one[0]["output_alias"] - 1 / 7) < 1e-12 and abs(four[0]["output_alias"] - (1 / 7) ** 4) < 1e-12
    # a dual-capable unit duplicates neg and abs
    dual, _ = feasibility(pairs, None, "duplicate", [{"family": "residue", "modulus": 31, "comparator.family": "direct_compare"}], dual_possible=True)
    assert dual[0]["replica_pairs"] == 2 and dual[0]["mechanism"][f"{I16}/neg"] == "replica"
    # the declaration is a restriction, and a pin outside its family is an error
    for bad in ([{"family": "residue", "modulus": 5}], [{"family": "residue", "A": 3}], [{"family": "residue"}, {"family": "residue"}],
                [{"family": "rns_redundant", "comparator.family": "two_rail_tree"}], [{"family": "nope"}]):
        try:
            feasible_families(pairs, None, "duplicate", bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted {bad}")
    try:
        feasibility(pairs, {"escape": 0.1})
    except ValueError:
        pass
    else:
        raise AssertionError("an unknown requirement key was accepted")
    # the command line: select, explain, floor, emit; emit's block feeds the same function
    out = io.StringIO()
    with redirect_stdout(out):
        rc = CK.main(["select", "--formats", "int16", "--ops", ",".join(ARITH), "--random-alias", "5e-2", "--single-bit", "1.0",
                      "--fallback", "error", "--families", "residue,multi_residue,duplication"])
    text = out.getvalue()
    table = "\n".join(line for line in text.splitlines() if not line.startswith("[chialu.checkers]"))
    assert rc == 0 and "points meet the bound" in text and "residue" in table and "duplication" not in table, text
    out = io.StringIO()
    with redirect_stdout(out):
        rc = CK.main(["explain", "--family", "residue", "--pin", "modulus=7", "--formats", "int16", "--ops", "add,and", "--random-alias", "5e-2"])
    assert rc == 1 and "rejected on alias" in out.getvalue() and f"{I16}/and: replica" in out.getvalue(), out.getvalue()
    out = io.StringIO()
    with redirect_stdout(out):
        rc = CK.main(["floor", "--formats", "int16,2xfp8e4m3"])
    assert rc == 0 and "lowest output_alias" in out.getvalue() and "reduced_precision" in out.getvalue()
    out = io.StringIO()
    with redirect_stdout(out):
        rc = CK.main(["emit", "--formats", "int16", "--ops", ",".join(ARITH), "--random-alias", "5e-2", "--single-bit", "1.0", "--fallback", "error"])
    import yaml
    block = yaml.safe_load(out.getvalue())
    assert rc == 0 and block["choices"] and all("family" in e for e in block["choices"])
    again, again_rej = feasibility(pairs, {"random_alias": 5e-2, "single_bit": 1.0}, "error", block["choices"])
    assert again and all(p["output_alias"] <= 5e-2 for p in again)
    # illegal pairs are dropped rather than counted
    out = io.StringIO()
    with redirect_stdout(out):
        CK.main(["select", "--formats", "int16", "--ops", "add,fadd", "--families", "residue"])
    assert f"illegal pairs dropped: {I16}/fadd" in out.getvalue()
    print("PASS feasible_families: model numbers, three fallbacks, restrictions, lanes, dual, and the four subcommands")
    return 0


if __name__ == "__main__":
    sys.exit(main())
