"""Simulate CORDIC coordinate/residual choices against an independent recurrence."""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import random
import tempfile
import traceback


def audit_adder(hierarchy, family):
    """Check the actual original hierarchy before scheduling its simulation."""
    if family == 'ripple_carry':
        adders = [row for row in hierarchy if row['module'] == 'fam_adder_ripple_carry']
        chunks = [row for row in hierarchy if row['module'] == 'fam_adder_ripple_chunk']
        assert adders and chunks
        for row in adders:
            assert row['parameters']['CHUNK'] == 1 and row['parameters']['FORM'] == 0, row
            width = row['parameters']['W']
            for port in ('a', 'b', 's'):
                assert row['ports'][port]['width'] == width, row
        assert len(chunks) == sum(row['parameters']['W'] for row in adders)
        for row in chunks:
            assert row['parameters']['W'] == 1 and row['parameters']['FORM'] == 0, row
            assert all(row['ports'][port]['width'] == 1 for port in ('a', 'b', 'cin', 's', 'cout')), row
    else:
        adders = [row for row in hierarchy if row['module'].startswith('fam_prefix_brent_kung_')]
        chunks = []
        assert adders, 'the selected Brent-Kung adders are absent'
    return {'pass': True, 'scope': 'the original elaboration of the selected exact child CPA',
            'family': family, 'adder_instances': len(adders), 'full_chunk_instances': len(chunks),
            'adder_widths': dict(Counter(row['ports']['a']['width'] for row in adders))}


# the iteration counts a default run binds: the ends of 8..64 and each side of a power of two, where the
# angle table and the shift network change width; --iterations names others
REPRESENTATIVE_ITERATIONS = (8, 9, 15, 16, 17, 31, 32, 33, 48, 63, 64)


def cases(iterations=REPRESENTATIVE_ITERATIONS):
    for count in iterations:
        for coordinate in ("circular", "hyperbolic", "linear"):
            for vectoring in (False, True):
                yield "cordic", count, coordinate, vectoring, "cpa", None
    for count in (8, 16, 64):
        for residual in ("carry_save", "signed_digit", "conventional_cpa"):
            for scale in ("double_rotation", "correcting_iterations", "digit_set_restriction"):
                for coordinate in ("circular", "hyperbolic", "linear"):
                    for vectoring in (False, True):
                        if coordinate == "linear" and not vectoring and residual != "conventional_cpa":
                            continue
                        yield "redundant_high_radix_cordic", count, coordinate, vectoring, residual, scale


def _check(job):
    import mpmath
    from chialu.targets.rtl.families import sfu as SF
    from chialu.targets.rtl.families.selftest import run_case
    from chialu.verify.cordic_algorithm import CordicRotationContract
    from chialu.verify.family_ref import Port
    from chialu.verify.family_tb import emit_text, pack_ports
    from chialu.verify.tb_gen import write_hex
    index, case, root, random_count, *component_choices = job
    adder = component_choices[0] if component_choices else "ripple_carry"
    simulation_path = component_choices[1] if len(component_choices) > 1 else 'original'
    adder_pins = {"chunk_width_bits": 1} if adder == "ripple_carry" else {"topology": "brent_kung", "valency": 2}
    family, count, coordinate, vectoring, residual, scale = case
    pins = {"iterations": count, "coordinate_set": coordinate, "mode": "vectoring" if vectoring else "rotation"} if family == "cordic" \
        else {"residual_arithmetic": residual, "scale_handling": scale}
    fraction, width = count + 8, count + 12
    mp = mpmath.mp.clone(); mp.prec = fraction + 64
    if coordinate == "circular":
        angles = [int(mp.atan(mp.power(2, -i)) * (1 << fraction) + mp.mpf("0.5")) for i in range(count + 2)]
        schedule = list(range(1, count + 1)) if scale == "double_rotation" else list(range(count))
    elif coordinate == "hyperbolic":
        angles = [0] + [int(mp.atanh(mp.power(2, -i)) * (1 << fraction) + mp.mpf("0.5")) for i in range(1, count + 2)]
        schedule = []
        shift, repeat = 1, 4
        while len(schedule) < count:
            schedule.append(shift)
            if shift == repeat:
                schedule.append(shift)
                repeat = 3 * repeat + 1
            shift += 1
        schedule = schedule[:count]
    else:
        angles = [(1 << fraction) >> i for i in range(count + 2)]
        schedule = list(range(1, count + 1))
    if scale == "correcting_iterations" and coordinate != "linear":
        schedule = sorted(schedule + list(range(3, count, 4)))
    net = SF.Net(f"cordic_rotation_{index}", "selected micro-rotation chain", {"adder": (adder, adder_pins)})
    inputs = [net.port_in(name, width, True) for name in ("x", "y", "z")]
    engine = SF.CordicEngine(family, pins)
    outputs = engine._rot(net, *inputs, coordinate, count, fraction, angles, schedule, [], vectoring)
    for name, value in zip(("out_x", "out_y", "out_z"), outputs):
        net.port_out(name, value)
    contract = CordicRotationContract(net.algorithm_contracts[-1])
    ports_in = [Port(name, "input", width) for name in ("x", "y", "z")]
    ports_out = [Port(name, "output", value.w) for name, value in zip(("out_x", "out_y", "out_z"), outputs)]
    mask = (1 << width) - 1
    corners = [0, 1, mask, 1 << fraction, (-1 << fraction) & mask, (1 << (width - 1)) - 1, 1 << (width - 1)]
    values = [{"x": a, "y": b, "z": c} for a in corners for b, c in zip(corners, reversed(corners))]
    rng = random.Random(921 + index)
    values.extend({name: rng.getrandbits(width) for name in ("x", "y", "z")} for _ in range(random_count))
    expected = []
    for value in values:
        answer = contract.evaluate(value)
        expected.append(pack_ports({"out_" + name: result for name, result in answer.items()}, ports_out))
    directory = Path(root) / str(index)
    run_dir = directory / net.name
    run_dir.mkdir(parents=True, exist_ok=True)
    (directory / "contract.json").write_text(json.dumps(contract.definition, indent=2) + "\n")
    write_hex(run_dir / "vectors.hex", [pack_ports(value, ports_in) for value in values], 3 * width)
    write_hex(run_dir / "expected.hex", expected, sum(port.width for port in ports_out))
    bench = emit_text(net.name, {}, ports_in + ports_out, len(values))
    extra_evidence = {}
    if simulation_path == 'checked_process':
        from chialu.targets.rtl.families import library_closure
        from chialu.verify.combinational_sim import simulate
        from chialu.verify.elaboration import elaborate
        source = library_closure(bench + '\n' + net.render()) + '\n' + net.render()
        hierarchy_dir = run_dir / 'original-hierarchy'
        hierarchy = elaborate(source + '\n' + bench, 'tb', hierarchy_dir, timeout=1800)
        extra_evidence['original_hierarchy'] = audit_adder(hierarchy, adder)
        with (hierarchy_dir / 'obj_sim' / 'sim').open('rb') as original_model:
            extra_evidence['original_model_sha256'] = hashlib.file_digest(original_model, 'sha256').hexdigest()
        result = simulate(source, net.name, bench, run_dir)
        extra_evidence['correspondence'] = result['certificate']
        verdict = net.name + ': PASS'
    elif simulation_path == 'original':
        verdict = run_case("", net.name, bench, directory, net.render())
    else:
        raise ValueError(f'unknown simulation path {simulation_path}')
    hashes = {name + "_sha256": hashlib.sha256((run_dir / filename).read_bytes()).hexdigest()
              for name, filename in (("rtl", "lib.sv"), ("bench", "tb.sv"),
                                     ("vectors", "vectors.hex"), ("expected", "expected.hex"))}
    return {"index": index, "family": family, "iterations": count, "coordinate": coordinate, "vectoring": vectoring,
            "residual": residual, "scale": scale, "vectors": len(values), "pass": verdict.endswith(": PASS"),
            "component_adder": {"family": adder, "pins": adder_pins}, "simulation_path": simulation_path,
            "detail": verdict, **contract.report(), **hashes, **extra_evidence}


def check(job):
    """Keep an individual generation/tool failure in the batch denominator."""
    try:
        return _check(job)
    except Exception as error:
        index, case, root, random_count, *choices = job
        directory = Path(root) / str(index)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / 'failure.log').write_text(traceback.format_exc())
        result = {'index': index, 'case': list(case), 'pass': False,
                  'random_vectors_requested': random_count,
                  'simulation_path': choices[1] if len(choices) > 1 else 'original',
                  'detail': type(error).__name__ + ': ' + str(error), 'failure_log': str(directory/'failure.log')}
        (directory / 'failure.json').write_text(json.dumps(result, indent=2)+'\n')
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out")
    parser.add_argument("--iterations", default=",".join(map(str, REPRESENTATIVE_ITERATIONS)),
                        help="comma-separated counts; every count of 8..64 is --iterations " + ",".join(map(str, range(8, 65))))
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--stop", type=int)
    parser.add_argument("--indices", help="explicit comma-separated original case ordinals, before start/stop slicing")
    parser.add_argument("--vectors", type=int, default=96)
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--adder", choices=("ripple_carry", "parallel_prefix"), default="ripple_carry",
                        help="explicit child CPA fixture; prefix uses Brent-Kung and reports a separate target")
    parser.add_argument('--simulation-path', choices=('original', 'checked_process'), default='original')
    args = parser.parse_args(argv)
    root = Path(args.out or tempfile.mkdtemp(prefix="chialu-cordic-rotation-"))
    root.mkdir(parents=True, exist_ok=True)
    selected = list(enumerate(cases(list(map(int, args.iterations.split(","))))))
    if args.indices is not None:
        indices = set(map(int, args.indices.split(',')))
        if not indices <= set(range(len(selected))):
            parser.error('an explicit index is outside the selected iteration catalog')
        selected = [(index, case) for index, case in selected if index in indices]
    selected = selected[args.start:args.stop]
    results = []
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for result in pool.map(check, [(index, case, str(root), args.vectors, args.adder, args.simulation_path) for index, case in selected]):
            results.append(result)
            print(json.dumps(result), flush=True)
            (root / "report.json").write_text(json.dumps(results, indent=2) + "\n")
    return 0 if results and all(result["pass"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
