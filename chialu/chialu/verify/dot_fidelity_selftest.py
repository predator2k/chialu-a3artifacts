"""Dot seed simulation and structural regressions for effective variant pins.

Run with ``python -m chialu.verify.dot_fidelity_selftest``. The checks use
the public seed path and the Python unit golden. They deliberately reject
geometries that cannot exercise a selected construction.
"""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
import tempfile

from chialu.targets.rtl.families.dot import dot_sv, geom_of
from chialu.targets.rtl.families.fidelity import Audit
from chialu.verify.dot_ref import normalize_dot_spec
from chialu.verify.formats import parse_format
from chialu.verify.variant_selftest import check_seed


def spec(fab, fc, fd, n, **options):
    return normalize_dot_spec(dict(unit="vec_dot_acc", dut_name="dot_core", check_en=False,
                                   modes=[dict(elements=n, format_ab=fab, format_c=fc, format_d=fd)], **options))


def cases():
    for width in range(16, 49, 8):
        yield f"integer_width_{width}", spec("int4", "int4", "int16", 4), "integer_mac", {"accumulator_width_bits": width}
    for levels in (1, 2):
        for dimensions in ("one", "two"):
            for accumulation in ("sum_apart", "sum_together"):
                pins = dict(array_style="composable_submultiplier", scalability_levels=levels,
                            scalable_dimensions=dimensions, accumulation_mode=accumulation, accumulator_width_bits=24)
                yield f"composable_{levels}_{dimensions}_{accumulation}", spec("int8", "int4", "int16", 2), "integer_mac", pins
    for width in (64, 96, 128):
        for org in ("monolithic", "segmented_lazy_carry", "banked_sub_adders", "two_speed"):
            pins = dict(accumulator_width_bits=width, organization=org, carry_resolution="carry_save_deferred")
            yield f"kulisch_{width}_{org}", spec("fp8e4m3", "fp8e4m3", "fp8e4m3", 2), "kulisch_long_accumulator", pins
    for family, key in (("classic_fma", "subsume_fp_add"), ("reduced_latency_fma", "add_skip_for_pure_addition")):
        for value in (False, True):
            yield f"{family}_{value}", spec("fp8e4m3", "fp8e4m3", "fp8e4m3", 1), family, {key: value}
    yield "bridge_monolithic", spec("fp8e4m3", "fp8e4m3", "fp8e4m3", 1), "bridge_fma", {"composition_style": "monolithic_fused"}
    yield "simd_integer", spec("int8", "int8", "int16", 8), "multi_precision_simd_fma", {"lane_split": "8x8"}


def must_reject(fn, fragment):
    try:
        fn()
    except ValueError as exc:
        if fragment not in str(exc):
            raise AssertionError(f"expected {fragment!r}, got {str(exc)!r}") from exc
    else:
        raise AssertionError(f"expected rejection containing {fragment!r}")


def check_vectors(target, selection, vectors, directory):
    """Run explicit pattern vectors through the same simulation gate."""
    from chialu.targets.derive import seed_for
    from chialu.verify import dot_ref as D, tb_gen
    from chialu.eda import conformance
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    lay = D.dot_layout(target)
    ports = lay["core_in"] + lay["core_out"]
    inputs, outputs = [], []
    for vector in vectors:
        ctrl = {name: target[name][vector.get(name+"_sel", 0)] for name in D.DOT_RUNTIME}
        words = [(vector.get("sr_rnd", 0) >> (index*lay["sr_bits"])) & ((1 << lay["sr_bits"])-1)
                 for index in range(lay["v_max"])]
        expected = D.dot_outputs(target, lay, vector.get("mode", 0), vector["a"], vector["b"], vector.get("c"), ctrl, words)
        iw = ow = 0
        for port in lay["core_in"]:
            iw = (iw << port.width) | vector.get(port.name, 0)
        for port in lay["core_out"]:
            ow = (ow << port.width) | expected[port.name]
        inputs.append(iw)
        outputs.append(ow)
    tb_gen.write_hex(directory / "vectors.hex", inputs, sum(p.width for p in lay["core_in"]))
    tb_gen.write_hex(directory / "expected.hex", outputs, sum(p.width for p in lay["core_out"]))
    tb = tb_gen.emit_tb(target["dut_name"], ports, len(vectors), expected_file="expected.hex")
    files = {"vectors.hex": (directory / "vectors.hex").read_text(),
             "expected.hex": (directory / "expected.hex").read_text(), "tb.sv": tb,
             "spec.json": json.dumps(target)}
    rtl = seed_for(target, family=selection)
    (directory / "seed.sv").write_text(rtl)
    (directory / "tb.sv").write_text(tb)
    result = conformance(rtl, files)
    result.update(source_sha256=hashlib.sha256(str(rtl).encode()).hexdigest(),
                  vectors_sha256=hashlib.sha256(files["vectors.hex"].encode()).hexdigest(),
                  expected_sha256=hashlib.sha256(files["expected.hex"].encode()).hexdigest(),
                  vector_count=len(vectors))
    (directory / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def zero_cases(directory):
    from itertools import product
    for fmt_name in ("fp8e4m3", "fp16", "fp32"):
        fmt = parse_format(fmt_name)
        sign = 1 << (fmt.width-1)
        vectors = [dict(a=a*sign, b=b*sign, c=c*sign, rounding_sel=r)
                   for a, b, c, r in product((0, 1), repeat=4)]
        for r in (0, 1):
            vectors += [dict(a=fmt.encode(1), b=fmt.encode(1), c=fmt.encode(-1), rounding_sel=r),
                        dict(a=fmt.encode(-1), b=fmt.encode(1), c=fmt.encode(1), rounding_sel=r)]
        target = spec(fmt_name, fmt_name, fmt_name, 1, rounding=["RNE", "RDN"])
        for selected in (None, ("classic_fma", {}), ("mixed_precision_cascade_fma", {})):
            name = selected[0] if selected else "behavioral"
            result = check_vectors(target, selected, vectors, Path(directory) / f"zero_{fmt_name}_{name}")
            assert result["pass"], (fmt_name, selected, result)


def main():
    from chialu.targets.derive import seed_for
    out = Path(tempfile.mkdtemp(prefix="chialu-dot-fidelity-"))
    summary = []
    for name, target, family, pins in cases():
        with Audit() as audit:
            result = check_seed(target, (family, pins), out / name, 96, 37)
        item = dict(name=name, family=family, pins=pins, **result)
        summary.append(item)
        (out / "results.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(item), flush=True)
        assert result["pass"] is True, (name, result, out)
        if "accumulator_width_bits" in pins:
            effects = audit.report()["effects"]
            assert any(e["pin"] == "accumulator_width_bits" and e["effective"] == pins["accumulator_width_bits"] for e in effects), name
            # Audit metadata alone is not evidence: inspect the actual word
            # feeding the sum in the generated, instantiated module.
            import re
            rtl = (out / name / "seed.sv").read_text()
            width = pins["accumulator_width_bits"]
            assert re.search(rf"logic (?:signed )?\[{width-1}:0\] v0;", rtl), (name, "reduction word width")
    small = spec("int8", "int8", "int16", 4)
    must_reject(lambda: seed_for(small, family=("integer_mac", {"accumulator_width_bits": 16})), "at least")
    narrow = geom_of(parse_format("fp32"), parse_format("fp32"), parse_format("fp32"), 4)
    must_reject(lambda: dot_sv(narrow, "streaming_accurate_accumulator", {"window_bits": 33}), "minimum")
    must_reject(lambda: seed_for(small, family=("multi_precision_simd_fma", {"lane_split": "8x8"})), "requires 8")
    must_reject(lambda: seed_for(small, family=("integer_mac", {"scalability_levels": 2})), "inactive")
    must_reject(lambda: seed_for(small, family=("integer_mac", {"element_op": "absolute_difference"})), "absolute_difference")
    zero_cases(out)
    print(f"PASS {len(summary)} dot seeds and 5 explicit fidelity rejections; {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
