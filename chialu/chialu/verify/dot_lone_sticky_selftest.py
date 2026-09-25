"""Compare both float packers on lone sticky values at rounding boundaries."""
from fractions import Fraction
from itertools import product
from pathlib import Path
import tempfile

from chialu.targets.rtl.engine import Engine, Conventions, FW
from chialu.targets.rtl.families.fp import Geom, round_sv
from chialu.targets.rtl.families.selftest import run_case
from chialu.verify.family_ref import Port, ROUNDING, _fields
from chialu.verify.family_tb import emit_text, pack_ports
from chialu.verify.formats import parse_format
from chialu.verify.rounding import Rounder, flag_word
from chialu.verify.tb_gen import write_hex


def main():
    from chialu.targets.rtl.engine import FLAG_ORDER
    root = Path(tempfile.mkdtemp(prefix="chialu-lone-sticky-"))
    total = 0
    for fname, wide in (("fp8e4m3", False), ("fp16", False), ("bf16", False), ("fp32", False), ("fp32", True)):
        fmt = parse_format(fname)
        e = Engine("t", fmt, 8, True, targets=[fmt], conv=Conventions(zero_sign="preserve"))
        if wide:
            e.widen(512)
        geometry = Geom.of_engine(e)
        name, library = round_sv(fmt, geometry, "dedicated_per_op", {}, e.tokens)
        inputs = [Port("x", "input", e.XT), Port("rnd", "input", 3), Port("word", "input", 8), Port("ftz", "input", 1)]
        outputs = [Port("engine_bits", "output", fmt.width+FW), Port("library_bits", "output", fmt.width+FW)]
        vectors, expected = [], []
        anchors = [1-fmt.bias-fmt.man_bits-1, 1-fmt.bias-fmt.man_bits, 1-fmt.bias-1,
                   1-fmt.bias, 0, fmt._top()-fmt.bias]
        for sign, value_exponent, rnd, word, ftz in product((0, 1), anchors, range(6), (0, 127, 255), (0, 1)):
            exponent = value_exponent + e.XW
            x = (_fields(0, sign, exponent, 0, e.XW, e.EW) << 1) | 1
            # The X sticky sits below the normalized significand. Choose
            # an exact positive tail below every retained rounding bit.
            magnitude = Fraction(2)**value_exponent * (1 + Fraction(2)**(-2*e.XW+1))
            value = -magnitude if sign else magnitude
            mode = ROUNDING[rnd] if rnd != 5 else "RDN" if sign else "RUP"
            bits, flags = Rounder(mode, 8, ftz=bool(ftz)).float(fmt, value, word, sign)
            want = (flag_word(flags, FLAG_ORDER) << fmt.width) | bits
            vectors.append(pack_ports(dict(x=x, rnd=rnd, word=word, ftz=ftz), inputs))
            expected.append(pack_ports(dict(engine_bits=want, library_bits=want), outputs))
            if wide:
                # A literal low bit exercises P_norm's full-width shift;
                # the lone-sticky branch itself begins with sig=0.
                x = _fields(0, sign, value_exponent, 1, e.XW, e.EW) << 1
                value = Fraction(2)**value_exponent * (-1 if sign else 1)
                bits, flags = Rounder(mode, 8, ftz=bool(ftz)).float(fmt, value, word, sign)
                want = (flag_word(flags, FLAG_ORDER) << fmt.width) | bits
                vectors.append(pack_ports(dict(x=x, rnd=rnd, word=word, ftz=ftz), inputs))
                expected.append(pack_ports(dict(engine_bits=want, library_bits=want), outputs))
        directory = root / (fname + ("_wide" if wide else ""))
        run_directory = directory / "lone_sticky_dut"
        run_directory.mkdir(parents=True)
        write_hex(run_directory / "vectors.hex", vectors, sum(p.width for p in inputs))
        write_hex(run_directory / "expected.hex", expected, sum(p.width for p in outputs))
        ports = inputs + outputs
        decl = ", ".join(f"{p.direction} wire [{p.width-1}:0] {p.name}" for p in ports)
        source = e.vdecl() + e.rup_fn() + e.arith() + e.pack_float(fmt, "s")
        dut = f"module lone_sticky_dut({decl});\n{source}\nassign engine_bits=t_pack_s(x,rnd,word,ftz);\n"
        dut += f"{name} u_round (.x(x), .rnd(rnd), .word(word), .ftz(ftz), .bits(library_bits[{fmt.width-1}:0]), .fl(library_bits[{fmt.width+FW-1}:{fmt.width}]));\nendmodule\n"
        bench = emit_text("lone_sticky_dut", {}, ports, len(vectors))
        result = run_case("", "lone_sticky_dut", bench, directory, dut + library)
        print(fname, result, flush=True)
        assert result.endswith("PASS"), (fname, result, directory)
        total += len(vectors)
    print(f"PASS {total} lone-sticky vectors against independent Python and both packers; {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
