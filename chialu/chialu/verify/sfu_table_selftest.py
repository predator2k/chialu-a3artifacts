"""Check independent SFU tables and reject a table computed at format precision."""
import argparse
from pathlib import Path
import tempfile
import subprocess
import shutil

from chialu.targets.rtl.families import sfu as SF
from chialu.targets.rtl.families import sfu_table as TABLE
from chialu.targets.rtl.families.selftest import run_case
from chialu.verify.family_ref import Port
from chialu.verify.family_tb import emit_text
from chialu.verify.formats import parse_format
from chialu.verify.ops import SFU_UNARY
from chialu.verify.tb_gen import write_hex


def check(fmt, fn, family, work, precision=None, simulate=False):
    name = f"table_{fmt.name}_{fn}_{family}"
    pins = {} if precision is None else {"_table_precision": precision}
    name, text, net = SF.pattern_sv(fn, fmt, family, pins, name)
    expected = [SF.reference_bits(fn, fmt, b) for b in range(1 << fmt.width)]
    wrong = [(b, got, expected[b]) for b in range(1 << fmt.width)
             if (got := net.run({"x": b})["y"]) != expected[b]]
    verdict = None
    if simulate:
        directory = work / name
        directory.mkdir(parents=True, exist_ok=True)
        write_hex(directory / "vectors.hex", range(1 << fmt.width), fmt.width)
        write_hex(directory / "expected.hex", expected, fmt.width)
        ports = [Port("x", "input", fmt.width), Port("y", "output", fmt.width)]
        bench = emit_text(name, {}, ports, len(expected))
        verdict = run_case("", name, bench, work, text)
    return wrong, verdict


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--formats", default="fp8e4m3,posit8_0")
    ap.add_argument("--functions", default=",".join(SFU_UNARY))
    ap.add_argument("--working-precision", help="format, or a precision in bits; the default uses at least twice the format precision")
    args = ap.parse_args(argv)
    for tool in ("verilator",):
        if not shutil.which(tool):
            ap.error(f"{tool} is not on PATH")
    work = Path(tempfile.mkdtemp(prefix="chialu_sfu_tables_"))
    failures = cases = skipped = 0
    for fname in args.formats.split(","):
        fmt = parse_format(fname)
        if fmt.width > SF.PATTERN_MAX_BITS:
            ap.error(f"{fname} exceeds the library's table limit of {SF.PATTERN_MAX_BITS} bits")
        precision = TABLE.format_precision(fmt) if args.working_precision == "format" else int(args.working_precision) if args.working_precision else None
        for family in SF.PATTERN_FAMILIES:
            for fn in args.functions.split(","):
                wrong, verdict = check(fmt, fn, family, work, precision, simulate=True)
                ok = not wrong and (verdict is None or verdict.endswith(": PASS"))
                skip = bool(verdict and ": SKIP" in verdict) and not wrong
                cases += 1
                failures += not ok and not skip
                skipped += skip
                status = "SKIP" if skip else "PASS" if ok else "FAIL"
                print(f"{status} {fname} {family} {fn}: {len(wrong)} wrong entries" +
                      (f"; first={wrong[:3]}" if wrong else "") + (f"; {verdict}" if verdict else ""), flush=True)
    if args.working_precision is None:
        from chialu.verify.ops import sfu_ref
        posit = parse_format("posit8_0")
        assert posit.decode(0x85) == -14
        assert sfu_ref("gelu", posit, 0x85) == 0xff
        assert SF.reference_bits("gelu", posit, 0x85) == 0xff
        print("PASS GELU(-14) retains its nonzero negative tail", flush=True)
        fmt = parse_format("fp8e4m3")
        wrong, verdict = check(fmt, "sigmoid", "direct_lut", work / "mutant", TABLE.format_precision(fmt), simulate=True)
        detected = bool(wrong) and verdict is not None and "FAIL" in verdict
        failures += not detected
        print(f"{'PASS' if detected else 'FAIL'} format-precision mutation rejected: {len(wrong)} wrong entries", flush=True)
    print(f"[sfu tables] {cases - failures - skipped}/{cases} tables pass, {skipped} skipped, {'FAIL' if failures else 'PASS'} ({work})")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
