"""Define the PLAM algorithm separately from its error against multiplication."""
from fractions import Fraction

from chialu.verify import ops
from chialu.verify.engine_ref import x_ref
from chialu.verify.formats import NAN, NAR, Special, _floor_log2
from chialu.verify.family_ref import _fields


def plam_value(a, b):
    """Return Mitchell's product and whether its omitted fraction term is nonzero."""
    if a is NAR or b is NAR:
        return NAN, False
    if isinstance(a, Special) or isinstance(b, Special):
        return ops._fp2('fmul', a, b), False
    if a == 0 or b == 0:
        return Fraction(0), False
    ka, kb = _floor_log2(abs(a)), _floor_log2(abs(b))
    fa = abs(a) / Fraction(2) ** ka - 1
    fb = abs(b) / Fraction(2) ** kb - 1
    fraction_sum = fa + fb
    if fraction_sum < 1:
        magnitude = (1 + fraction_sum) * Fraction(2) ** (ka + kb)
    else:
        magnitude = fraction_sum * Fraction(2) ** (ka + kb + 1)
    return (-magnitude if (a < 0) != (b < 0) else magnitude), bool(fa and fb)


def plam_x(fmt, a_bits, b_bits, x_width, exponent_width):
    """Encode the algorithm value and its residual sticky bit in the X contract."""
    a, b = fmt.decode(a_bits), fmt.decode(b_bits)
    value, residual = plam_value(a, b)
    if not isinstance(value, Special) and value == 0:
        negative = int((a < 0) != (b < 0))
        return _fields(0, negative, 0, 0, x_width, exponent_width) << 1
    return x_ref(value, x_width, exponent_width) | int(residual)


def main():
    import argparse
    from pathlib import Path
    import tempfile
    from chialu.targets.rtl.engine import Engine
    from chialu.targets.rtl.families import fp, posit, library_closure
    from chialu.targets.rtl.families.selftest import run_python_case
    from chialu.verify.family_ref import Adapter, Port
    from chialu.verify.family_tb import emit
    from chialu.verify.formats import parse_format
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--format', default='posit8_0')
    parser.add_argument('--vectors', type=int, default=4096)
    parser.add_argument('--out')
    args = parser.parse_args()
    fmt = parse_format(args.format)
    engine = Engine('v', fmt, 8, False)
    geom = fp.Geom.of_engine(engine)
    module, body = posit.plam_sv(geom)
    source = f'''module plam_pattern(input [{fmt.width-1}:0] a,b, output [{geom.XT-1}:0] y);
{engine.vdecl()}
{engine.unpack_posit(fmt, 's')}
  wire [{geom.XT-1}:0] xa = v_x(v_unpack_s(a, 1'b0));
  wire [{geom.XT-1}:0] xb = v_x(v_unpack_s(b, 1'b0));
  {module} product(.xa(xa), .xb(xb), .y(y));
endmodule
{body}
'''
    adapter = Adapter((Port('a', 'input', fmt.width), Port('b', 'input', fmt.width), Port('y', 'output', geom.XT)),
                      lambda row: {'y': plam_x(fmt, row['a'], row['b'], geom.XW, geom.EW)})
    directory = Path(args.out or tempfile.mkdtemp(prefix='chialu-plam-algorithm-'))
    result = run_python_case('', 'plam_algorithm', emit('plam_pattern', {}, adapter, args.vectors, 7), directory, source + library_closure(source))
    print(result)
    if not result.endswith(': PASS'):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
