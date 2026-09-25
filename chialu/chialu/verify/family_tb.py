"""Write Python vectors and emit one comparison bench for any family port list."""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path

from chialu.verify.family_ref import Adapter
from chialu.verify.tb_gen import write_hex

ERROR_BITS = 32


def pack_ports(values, ports):
    """Concatenate port patterns in declaration order, with the first port highest."""
    result = 0
    for port in ports:
        result = (result << port.width) | values[port.name]
    return result


class Bench(str):
    """Carry a generated bench and its deferred vector writer."""
    def __new__(cls, text, adapter, n, seed):
        obj = super().__new__(cls, text)
        obj.adapter, obj.n, obj.seed = adapter, n, seed
        return obj

    def write(self, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        vectors = self.adapter.stimulus(self.n, self.seed)
        inputs = [p for p in self.adapter.ports if p.direction == "input"]
        outputs = [p for p in self.adapter.ports if p.direction == "output"]
        write_hex(directory / "vectors.hex", (pack_ports(v, inputs) for v in vectors), sum(p.width for p in inputs))
        write_hex(directory / "expected.hex", (pack_ports(self.adapter.expect(v), outputs) for v in vectors),
                  sum(p.width for p in outputs))
        if self.adapter.algorithm is not None:
            write_hex(directory / "algorithm.hex", (pack_ports(self.adapter.algorithm_expect(v), outputs) for v in vectors),
                      sum(p.width for p in outputs))


def emit(module, params, adapter: Adapter, n=256, seed=1):
    """Emit a bench that compares file values or the adapter's numerical bounds."""
    n = max(1500, n) if adapter.tolerance else n
    corners = len(adapter.stimulus(0, seed))
    count = corners + n
    return Bench(emit_text(module, params, adapter.ports, count, adapter.tolerance, corners,
                           algorithm=adapter.algorithm is not None), adapter, n, seed)


def emit_text(module, params, ports, count, tolerance=None, corners=0, *, algorithm=False):
    """Emit comparisons for files whose row count is already known."""
    inputs = [p for p in ports if p.direction == "input"]
    outputs = [p for p in ports if p.direction == "output"]
    iw, ow = sum(p.width for p in inputs), sum(p.width for p in outputs)
    lines = ["module tb;", f"  localparam N = {count};",
             f"  reg [{iw-1}:0] vectors [0:N-1];", f"  reg [{ow-1}:0] expected [0:N-1];",
             "  integer i, errors = 0, measured = 0;", "  integer fd;"]
    if algorithm:
        lines.append(f"  reg [{ow-1}:0] algorithm_expected [0:N-1];")
    for port in ports:
        lines.append(f"  {'reg' if port.direction == 'input' else 'wire'} [{port.width-1}:0] {port.name};")
    for port in outputs:
        lines.append(f"  reg [{port.width-1}:0] expected_{port.name};")
    parameters = "#(" + ", ".join(f".{k}({v})" for k, v in params.items()) + ") " if params else ""
    conns = ", ".join(f".{p.name}({p.name})" for p in ports)
    lines.append(f"  {module} {parameters}dut ({conns});")
    cat = lambda names: "{" + ", ".join(names) + "}"
    actual = cat(p.name for p in outputs)
    reference = cat("expected_" + p.name for p in outputs)
    compare = [f"      if ({actual} !== {reference}) begin",
               "        errors = errors + 1;",
               f'        if (errors < 5) $display("MISMATCH vector=%0d got=%h expected=%h", i, {actual}, {reference});',
               "      end"]
    if tolerance:
        sizes = {p.name: p.width for p in outputs}
        bits = sum(sizes[p] for p in tolerance.ports)
        work_bits = max(bits + ERROR_BITS + 3,
                        max(tolerance.scale.bit_length(), tolerance.minimum.bit_length(), tolerance.slack.bit_length()) + ERROR_BITS + 3)
        scale = 1 << ERROR_BITS
        max_fraction = Fraction(str(tolerance.max_err))
        compare_bits = work_bits + max(max_fraction.numerator.bit_length(), max_fraction.denominator.bit_length()) + 1
        mean_fraction = Fraction(str(tolerance.mean_err))
        mean_bits = work_bits + count.bit_length() + ERROR_BITS + max(mean_fraction.numerator.bit_length(), mean_fraction.denominator.bit_length()) + 1
        lines += [f"  reg signed [{bits}:0] got_value, expected_value;",
                  f"  reg [{work_bits-1}:0] difference, denominator, error_units;",
                  f"  reg [{work_bits+count.bit_length()-1}:0] sum_error = 0;",
                  f"  reg [{compare_bits-1}:0] bound_error, bound_limit;",
                  f"  reg [{mean_bits-1}:0] mean_error, mean_limit;"]
        actual_value = cat(tolerance.ports)
        expected_value = cat("expected_" + p for p in tolerance.ports)
        if tolerance.signed:
            actual_value, expected_value = f"$signed({actual_value})", f"$signed({expected_value})"
        else:
            actual_value, expected_value = "{1'b0, " + actual_value + "}", "{1'b0, " + expected_value + "}"
        denominator_value = "(expected_value < 0 ? -expected_value : expected_value)" if tolerance.relative else f"{work_bits}'d{tolerance.scale}"
        minimum_test = f"denominator >= {work_bits}'d{tolerance.minimum}" if tolerance.relative else "1"
        compare = [f"      got_value = {actual_value}; expected_value = {expected_value};",
                   "      if ((^got_value) === 1'bx) errors = errors + 1;",
                   "      else begin",
                   "        difference = got_value >= expected_value ? got_value - expected_value : expected_value - got_value;",
                   f"        denominator = {denominator_value};",
                   f"        if (denominator != 0 && {minimum_test}) begin",
                   f"          if (difference <= {work_bits}'d{tolerance.slack}) difference = 0;",
                   f"          error_units = ((difference << {ERROR_BITS}) + denominator - 1) / denominator;",
                   f"          bound_error = difference * {compare_bits}'d{max_fraction.denominator};",
                   f"          bound_limit = denominator * {compare_bits}'d{max_fraction.numerator};",
                   "          if (bound_error > bound_limit) begin",
                   "            errors = errors + 1;",
                   '            if (errors < 5) $display("BOUND vector=%0d got=%h expected=%h error_units=%h", i, got_value, expected_value, error_units);',
                   "          end",
                   f"          if (i >= {corners}) begin sum_error = sum_error + error_units; measured = measured + 1; end",
                   "        end",
                   "      end"]
        exact_ports = [p.name for p in outputs if p.name not in tolerance.ports and p.name not in tolerance.unchecked_ports]
        if exact_ports:
            compare += [f"      if ({cat(exact_ports)} !== {cat('expected_' + p for p in exact_ports)}) begin",
                        "        errors = errors + 1;",
                        '        if (errors < 5) $display("MISMATCH in exact output vector=%0d", i);', "      end"]
    algorithm_load = ['    $readmemh("algorithm.hex", algorithm_expected);'] if algorithm else []
    algorithm_compare = [f"      if ({actual} !== algorithm_expected[i]) begin",
                         "        errors = errors + 1;",
                         f'        if (errors < 5) $display("ALGORITHM vector=%0d got=%h expected=%h", i, {actual}, algorithm_expected[i]);',
                         "      end"] if algorithm else []
    lines += ["  initial begin", '    $readmemh("vectors.hex", vectors);',
              '    $readmemh("expected.hex", expected);', *algorithm_load, '    fd = $fopen("actual.hex", "w");',
              "    for (i = 0; i < N; i = i + 1) begin",
              f"      {cat(p.name for p in inputs)} = vectors[i];",
              f"      {reference} = expected[i];", "      #1;",
              f'      $fdisplay(fd, "%h", {actual});', *algorithm_compare, *compare, "    end", "    $fclose(fd);"]
    if tolerance:
        lines += [f"    mean_error = sum_error * {mean_bits}'d{mean_fraction.denominator};",
                  f"    mean_limit = {mean_bits}'d{mean_fraction.numerator * scale} * measured;",
                  "    if (measured == 0 || mean_error > mean_limit) begin",
                  "      errors = errors + 1;",
                  '      $display("MEAN sum_error=%h measured=%0d", sum_error, measured);', "    end"]
    lines += ['    if (errors == 0) $display("PASS"); else $display("FAIL %0d", errors);',
              "    $finish;", "  end", "endmodule"]
    return "\n".join(lines) + "\n"
