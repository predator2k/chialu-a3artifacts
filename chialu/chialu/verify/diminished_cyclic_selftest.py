"""Check the live inverted cyclic carry row against modular arithmetic."""
import argparse
import hashlib
from itertools import product
import json
from pathlib import Path
import random
import tempfile


def check(width, pins, directory, mutation=False):
    from chialu.targets.rtl import families as FAM
    from chialu.targets.rtl.families import prefix
    from chialu.targets.rtl.families.adder_ext import end_around_carry_sv
    from chialu.targets.rtl.families.selftest import run_case
    from chialu.verify.family_ref import golden
    selected = dict(modulus="mod_2n_plus_1_diminished_one", recirculation="cyclic_prefix_level", **pins)
    spec = FAM.prefix_spec("end_around_carry", selected, width)
    graph = prefix.build(width, spec)
    source = end_around_carry_sv(width, selected, "cyclic_dut")
    assert "cyclic_sum" in source and "a + b + cin (two guard bits)" not in source
    if mutation:
        import re
        source, count = re.subn(r"assign feedback = ~[^;]+;", "assign feedback = 1'b0;", source)
        assert count == 1
    mask = (1 << width) - 1
    if width <= 5:
        vectors = list(product(range(1 << width), range(1 << width), (0, 1)))
    else:
        values = sorted({0, 1, 2, mask, mask - 1, mask >> 1, 1 << (width - 1)})
        vectors = list(product(values, values, (0, 1)))
        vectors += [(a, mask - a, cin) for a in values for cin in (0, 1)]
        rng = random.Random(57)
        vectors += [(rng.getrandbits(width), rng.getrandbits(width), rng.getrandbits(1)) for _ in range(256)]
    reference = golden("adder", "end_around_carry", selected, width)
    lines = [f"module tb; reg [{width-1}:0] a,b; reg cin; wire [{width-1}:0] s; wire cout; integer errors;",
             "cyclic_dut dut(.a(a),.b(b),.cin(cin),.s(s),.cout(cout)); initial begin errors=0;"]
    for a, b, cin in vectors:
        expected = reference.expect(dict(a=a, b=b, cin=cin))
        failed = [f"s !== {width}'d{expected['s']}", f"cout !== 1'b{expected['cout']}"]
        # Every selected prefix group must compute its actual operand span.
        # The expected carry uses integer addition, independently of the GP
        # graph's combining equations and topology construction.
        for lo, hi in graph.nodes:
            span = hi - lo + 1
            left, right = (a >> lo) & ((1 << span) - 1), (b >> lo) & ((1 << span) - 1)
            failed += [f"dut.cyclic_g_{lo}_{hi} !== 1'b{(left + right) >> span}",
                       f"dut.cyclic_p_{lo}_{hi} !== 1'b{int((left ^ right) == (1 << span) - 1)}"]
        lines.append(f"a={width}'d{a}; b={width}'d{b}; cin=1'b{cin}; #1; if ({' || '.join(failed)}) "
                     'begin errors=errors+1; if(errors<4) $display("MISMATCH a=%h b=%h cin=%b s=%h",a,b,cin,s); end')
    lines += ['if(errors==0) $display("PASS"); else $display("FAIL %0d",errors); $finish; end endmodule']
    tag = "case_" + hashlib.sha256(json.dumps([width, pins, mutation], sort_keys=True).encode()).hexdigest()[:12]
    dependencies = FAM.module_texts("cyclic_dut", source)
    status = run_case("", tag, "\n".join(lines), directory, "\n".join(dependencies.values()))
    passed = status.endswith(": PASS")
    if mutation:
        assert not passed and "FAIL" in status, status
    else:
        assert passed, status
    return {"width": width, "pins": selected, "graph": spec, "nodes": graph.size(), "vectors": len(vectors),
            "source_sha256": hashlib.sha256(source.encode()).hexdigest(), "pass": passed,
            "mutation_rejected": mutation and not passed, "detail": status}


def main(argv=None):
    from chialu.spaces.adder_spaces import PREFIX_TOPOLOGIES
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out")
    args = parser.parse_args(argv)
    root = Path(args.out or tempfile.mkdtemp(prefix="chialu-diminished-cyclic-"))
    root.mkdir(parents=True, exist_ok=True)
    results = []
    cases = [(width, {"topology": topology}) for width, topology in
             product((3, 5, 32), [t for t in PREFIX_TOPOLOGIES if t != "harris"])]
    cases += [(32, {"topology": "harris", "log2_sparsity": sparsity, "fanout_cap": fanout})
              for sparsity, fanout in product(range(4), range(2, 9))]
    cases += [(width, {"topology": "brent_kung"}) for width in (1, 2, 4)]
    cases += [(5, {"topology": "brent_kung", "incrementer.structure": "prefix_and_tree",
                   "incrementer.topology": topology}) for topology in ("sklansky", "brent_kung", "kogge_stone")]
    cases += [(5, {"topology": "brent_kung", "incrementer.structure": structure})
              for structure in ("ripple_and_chain", "select_blocks")]
    for width, pins in cases:
        result = check(width, pins, root)
        results.append(result)
        print(json.dumps(result), flush=True)
        (root / "report.json").write_text(json.dumps(results, indent=2) + "\n")
    damaged = check(5, {"topology": "brent_kung"}, root, mutation=True)
    (root / "mutation.json").write_text(json.dumps(damaged, indent=2) + "\n")
    print(f"PASS {len(results)} directed geometry/pin cases and feedback mutation; {root}")


if __name__ == "__main__":
    main()
