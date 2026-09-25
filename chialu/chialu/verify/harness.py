"""One call from functional parameters to a verification bundle.

build_verification(spec, out_dir) writes vectors.hex (+ expected.hex
for bit-exact gates), tb.sv, freeze.json and returns a Verification
whose check(dump_path) applies the numerical error model and budget.

spec is FUNCTIONAL only (microarchitecture-independent) — one dict per
unit class:

  {"unit": "alu", "modes": [{"count": 1, "format": "int16"}], "ops": ["add", "mul", ...],
   "int_encoding": "twos_complement", "fp_format": "none",
   "lanes": [1], "accuracy": "exact", "rounding": "RNE",
   "quotient_semantics": "trunc"}

  {"unit": "vec_sfu", "format": "fp16", "lanes": 4,
   "functions": ["exp2", "recip"], "rounding": "RNE",
   "daz_in": false, "ftz_out": false}

  {"unit": "vec_dot_acc", "elements": 4, "combos": ["int8->int32"],
   "accumulate": true, "rounding": "RNE"}

Optional in every spec: "latency_cycles", "variable_latency_max"
(iterative units — the TB switches protocol), "n_random", "seed",
"dut_name", and "budget" overriding the constraint-derived budget as
{"metric": bound} (e.g. {"mred": 0.01} for an approximate unit).
"""

from __future__ import annotations

import json
from pathlib import Path

from chialu.verify.ports import Port
from chialu.verify import ops as R
from chialu.verify import stimulus, tb_gen
from chialu.verify.errors import Budget, ErrorReport, PairScore
from chialu.verify.faults import DetectBudget, FaultPlan, FaultReport
from chialu.verify.formats import BCDFormat, Special, make_format

# The output ports that carry a numerical result: y of chialu.ALU and
# chialu.VecSFU, d of chialu.ALU's dual set and of chialu.VecDotAcc, and
# the error terms dot_arch_ref.extra_outputs provisions. The budget bounds
# the error of these. Every other provisioned output is a control or a
# status word, which the judge compares bit-exactly under every budget.
RESULT_OUTPUTS = ("y", "d", "d_error", "d_add_error", "d_mul_error")


def _zero_sign_differs(fmt, exp_bits, got_bits) -> bool:
    """Two patterns that decode to zero with different signs.

    errors.compare gives both zeros one index and one value, so such a
    pair carries no ulp, no absolute error and no relative error. The
    judge counts it separately rather than letting it score as exact.
    """
    if exp_bits == got_bits:
        return False
    try:
        ev, gv = fmt.decode(exp_bits), fmt.decode(got_bits)
    except (ValueError, AssertionError):
        return False
    if isinstance(ev, (Special, list)) or isinstance(gv, (Special, list)):
        return False
    return ev == 0 and gv == 0


class Verification:
    def __init__(self, spec, ports, vecs, meta, expected, out_fmt,
                 budget, out_dir, mode_budgets=None):
        self.spec = spec
        self.ports = ports
        self.vecs = vecs
        self.meta = meta
        self.expected = expected      # list of concatenated output ints
        self.out_fmt = out_fmt        # format of the primary data output
        self.budget = budget
        self.mode_budgets = mode_budgets     # {accuracy mode: Budget}, None without runtime control
        self.out_dir = Path(out_dir)
        self.out_w = sum(p.width for p in ports if p.direction == "out")
        if spec.get("unit") in ("alu", "vec_sfu"):
            from chialu.verify.formats import parse_format
            self._modes = [(int(m["count"]), parse_format(str(m["format"])))
                           for m in spec["modes"]]

    # -- host-side judgment over a dump file --
    def accuracy_mode_of(self, i: int) -> int:
        """The accuracy mode vector i drove (0 without runtime control)."""
        if i >= len(self.meta):
            return 0
        return int((self.meta[i].get("ctrl") or {}).get("accuracy_mode", 0) or 0)

    def _new_report(self):
        rep = ErrorReport()
        try:
            rep.out_max_mag = abs(self.out_fmt.max_finite()) \
                if hasattr(self.out_fmt, "max_finite") else \
                max(abs(self.out_fmt.decode(0)), self.out_fmt.max_int)
        except Exception:
            pass
        return rep

    def check(self, dump_path):
        rep = self._new_report()
        per_mode = {m: self._new_report() for m in (self.mode_budgets or {})}
        lines = Path(dump_path).read_text().split()
        n = min(len(lines), len(self.expected))
        def valid_word(line):
            return _is_hex(line) and 0 <= int(line, 16) < 1 << self.out_w
        protocol_fail = sum(not valid_word(line) for line in lines)
        self.range_execution_complete = len(lines) == len(self.expected) and not protocol_fail
        exact_outs = [p.name for p in self.ports if p.direction == "out"
                      and p.name not in RESULT_OUTPUTS]
        self.exact_output_wrong = {name: 0 for name in exact_outs}
        self.zero_sign_wrong = 0
        for i in range(n):
            if not valid_word(lines[i]):
                continue
            got = int(lines[i], 16)
            exp = self.expected[i]
            if exact_outs and got != exp:
                gf, ef = self._fields(got), self._fields(exp)
                for name in exact_outs:
                    if gf[name] != ef[name]:
                        self.exact_output_wrong[name] += 1
            targets = [rep]
            if per_mode:
                targets.append(per_mode[self.accuracy_mode_of(i)])
            for k, r in enumerate(targets):
                # the per-mode report scores the same results again, so the
                # separate counts are taken over the run report alone
                once = k == 0
                if self.spec.get("unit") == "vec_sfu":
                    self._score_sfu(r, i, self._data_field(exp),
                                    self._data_field(got), once)
                    continue
                if exp == got:
                    r.add(self.out_fmt, 0, 0, tag=f"v{i}")
                    continue
                gd, ed = self._data_field(got), self._data_field(exp)
                if self.spec.get("unit") == "alu":
                    self._score_alu(r, i, ed, gd, once)
                else:
                    r.add(self.out_fmt, ed, gd, tag=f"v{i}")
                    if once and _zero_sign_differs(self.out_fmt, ed, gd):
                        self.zero_sign_wrong += 1
        if per_mode:
            ok, viol = True, []
            for m, r in sorted(per_mode.items()):
                mok, mviol = self.mode_budgets[m].verdict(r)
                ok = ok and mok
                viol += [f"accuracy mode {m}: {v}" for v in mviol]
        else:
            ok, viol = self.budget.verdict(rep)
        exact_all = any(name == "bit_exact" for name, _, _ in self.budget.bounds)
        if exact_all or self.mode_budgets:
            different = sum(_is_hex(lines[i]) and int(lines[i], 16) != self.expected[i]
                            and (exact_all or any(name == "bit_exact" for name, _, _ in
                                 self.mode_budgets[self.accuracy_mode_of(i)].bounds)) for i in range(n))
            if different:
                ok = False
                viol.append(f"{different} output vectors differ under the bit-exact contract")
        exact_bad = sum(1 for i in range(n) if _is_hex(lines[i])
                        and self.meta[i].get("exact") and int(lines[i], 16) != self.expected[i])
        if exact_bad:
            ok = False
            viol.append(f"{exact_bad} slot vectors differ from the loaded "
                        f"table's polynomial (bit-exact)")
        for name in exact_outs:
            wrong = self.exact_output_wrong[name]
            if wrong:
                ok = False
                viol.append(f"{wrong} vectors differ in the {name} output, "
                            f"which is bit-exact under every budget")
        if self.zero_sign_wrong:
            ok = False
            viol.append(f"{self.zero_sign_wrong} results differ in the sign of "
                        f"zero, which carries no numerical distance")
        if len(lines) != len(self.expected):
            ok = False
            viol.append(f"dump has {len(lines)} of {len(self.expected)} "
                        f"lines")
        if protocol_fail:
            ok = False
            viol.append(f"{protocol_fail} invalid output words or protocol failures (TIMEOUT)")
        if self.spec.get("unit") == "vec_sfu":
            from chialu.sfu_accuracy import report_fixed
            self.algorithm_pass = None
            decision = self.spec.get("sfu_accuracy") or {}
            if report_fixed(self.spec) and decision.get("family") in ("direct_lut", "compressed_lut"):
                # Value tables implement correctly rounded functions. Their
                # complete output words therefore have an exact contract.
                self.algorithm_pass = self.range_execution_complete and all(
                    valid_word(line) and int(line, 16) == word for line, word in zip(lines, self.expected))
                self.algorithm_mismatches = [self.explain(f"MISMATCH i={i} in=0 got={line} expect={word:x}")
                                             for i, (line, word) in enumerate(zip(lines, self.expected))
                                             if valid_word(line) and int(line, 16) != word][:10]
                if not self.algorithm_pass:
                    ok = False
                    viol.append("value-table outputs differ from the independent correctly rounded contract")
            elif report_fixed(self.spec):
                ok = False
                viol.append("an independent whole-seed algorithm contract is not available for this fixed SFU implementation")
            if report_fixed(self.spec) and not (self.spec.get("_sfu_range_plan") or {}).get("complete"):
                ok = False
                viol.append("full implementation error range is not established; sampled maxima are not a range certificate")
        if ok and self.spec.get("unit") == "vec_dot_acc" and self.spec.get("dot_contract") == "architecture":
            from chialu.verify.architecture_accuracy import dot_error_report
            rep = dot_error_report(self)
            if self.spec.get("budget"):
                ok, viol = _one_budget(self.spec["budget"]).verdict(rep)
        return ok, viol, rep

    def explain(self, line: str) -> str:
        """A MISMATCH line of the self-checking testbench rendered for a
        reader: the vector's mode, op and control values, every operand
        with its decoded value, and the expected versus produced results
        (per value, decoded) and flags."""
        import re
        m = re.match(r".*i=(\d+) in=([0-9a-fA-FxX]+) got=([0-9a-fA-FxX]+) expect=([0-9a-fA-F]+)", line)
        if not m:
            return line
        i = int(m.group(1))
        if i >= len(self.meta):
            return line
        meta = self.meta[i]
        try:
            got = int(m.group(3), 16)
        except ValueError:
            return f"vector {i}: the output carries X bits ({m.group(3)[:24]}...)"
        exp = int(m.group(4), 16)
        outs = {}
        hi = self.out_w
        for p in self.ports:
            if p.direction != "out":
                continue
            outs[p.name] = ((exp >> (hi - p.width)) & ((1 << p.width) - 1),
                            (got >> (hi - p.width)) & ((1 << p.width) - 1))
            hi -= p.width
        unit = self.spec.get("unit")
        if unit != "alu":
            parts = [f"vector {i}: mode {meta.get('mode', 0)}"]
            for name, (e, g) in outs.items():
                parts.append(f"{name} expected 0x{e:x} got 0x{g:x}")
            return "; ".join(parts)
        from chialu.verify import alu_ref as A
        count, fmt = self._modes[meta["mode"]]
        op = meta["op"]
        ctrl = A.vector_ctrl(self.spec, meta.get("ctrl"))
        head = (f"vector {i}: mode {meta['mode']} ({count} x {fmt.name}), op {op}, "
                + ", ".join(f"{k}={v}" for k, v in ctrl.items()))
        ops_ = []
        for k, operands in enumerate(meta["lane_pairs"]):
            pa, pb = operands[0], operands[1]
            ops_.append(f"a[{k}]=0x{pa:x} ({_val(fmt, pa)})" + (f" b[{k}]=0x{pb:x} ({_val(fmt, pb)})"
                                                            if not A.is_unary(op) else "")
                        + (f" c[{k}]=0x{operands[2]:x} ({_val(fmt, operands[2])})" if len(operands) > 2 else ""))
        tgt = A.cvt_target(op)
        rf = tgt if tgt is not None else fmt
        if op == "mul_wide":
            from chialu.verify.formats import BCDFormat, IntFormat
            rf = BCDFormat(2 * fmt.width) if isinstance(fmt, BCDFormat) else IntFormat(2 * fmt.width, fmt.encoding)
        w_out = A.result_width(op, fmt, count)
        n_res = max(1, w_out // rf.width)
        res = []
        ey, gy = outs.get("y", (0, 0))
        pattern_op = op in ("cmp", "fcmp") or A.op_class(op) in ("shift", "logic")
        for k in range(n_res):
            e = (ey >> (k * rf.width)) & ((1 << rf.width) - 1)
            g = (gy >> (k * rf.width)) & ((1 << rf.width) - 1)
            if e != g:
                res.append(f"y[{k}] expected 0x{e:x}" + ("" if pattern_op else f" ({_val(rf, e)})")
                           + f" got 0x{g:x}" + ("" if pattern_op else f" ({_val(rf, g)})"))
        if (ey >> w_out) != (gy >> w_out):
            res.append(f"bits of y above {w_out} must be 0 (got 0x{gy >> w_out:x})")
        for name in ("d", "flags"):
            if name in outs and outs[name][0] != outs[name][1]:
                e, g = outs[name]
                res.append(f"{name} expected 0x{e:x} got 0x{g:x}")
        return head + "; " + "; ".join(ops_) + "; " + "; ".join(res or ["outputs differ"])

    def _score_alu(self, rep, i, exp_y, got_y, once=False):
        """Score the results packed in y one by one, each in its own
        format (blocks per element); the bits above the results must
        match exactly. `once` asks for the separate counts of the run
        report, which the per-mode reports do not repeat."""
        from chialu.verify import alu_ref as A
        from chialu.verify.formats import BlockFormat, IntFormat, BCDFormat
        m = self.meta[i]
        count, fmt = self._modes[m["mode"]]
        op = m["op"]
        tgt = A.cvt_target(op)
        if op == "mul_wide":
            rf = BCDFormat(2 * fmt.width) if isinstance(fmt, BCDFormat) \
                else IntFormat(2 * fmt.width, fmt.encoding)
        elif tgt is not None:
            rf = tgt
        else:
            rf = fmt
        w_out = A.result_width(op, fmt, count)
        n_res = w_out // rf.width
        pattern_op = op in ("cmp", "fcmp") or A.op_class(op) in ("shift", "logic")
        used = n_res * rf.width
        if (exp_y >> used) != (got_y >> used):
            rep.add(IntFormat(8, "unsigned"), 1, 0, tag=f"v{i}:upper")
        if pattern_op:
            # cmp, fcmp, shift and logic produce a bit pattern per lane. A
            # pattern has no numerical distance, so each lane scores as
            # exact or wrong and contributes to no value metric. A wrong
            # lane raises errors.Budget's "no finite numerical error bound"
            # violation, which is the verdict an approximate budget owes it.
            for k in range(n_res):
                eb = (exp_y >> (k * rf.width)) & ((1 << rf.width) - 1)
                gb = (got_y >> (k * rf.width)) & ((1 << rf.width) - 1)
                rep._record(PairScore(exact=eb == gb, special_mismatch=eb != gb),
                            eb, gb, tag=f"v{i}:{k}")
            return
        for k in range(n_res):
            eb = (exp_y >> (k * rf.width)) & ((1 << rf.width) - 1)
            gb = (got_y >> (k * rf.width)) & ((1 << rf.width) - 1)
            if isinstance(rf, BlockFormat):
                ev, gv = rf.decode(eb), rf.decode(gb)
                for j, (e1, g1) in enumerate(zip(ev, gv)):
                    rep.add_values(e1, g1, rf.ulp_at(eb), tag=f"v{i}:{k}.{j}")
            else:
                rep.add(rf, eb, gb, tag=f"v{i}:{k}")
                if once and _zero_sign_differs(rf, eb, gb):
                    self.zero_sign_wrong += 1

    def _score_sfu(self, rep, i, exp_y, got_y, once=False):
        from chialu.verify.formats import BlockFormat
        m = self.meta[i]
        count, fmt = self._modes[m["mode"]]
        w = fmt.width
        for k in range(count):
            eb = (exp_y >> (k * w)) & ((1 << w) - 1)
            gb = (got_y >> (k * w)) & ((1 << w) - 1)
            if isinstance(fmt, BlockFormat):
                ev, gv = fmt.decode(eb), fmt.decode(gb)
                for j, (e1, g1) in enumerate(zip(ev, gv)):
                    rep.add_values(e1, g1, fmt.ulp_at(eb), tag=f"v{i}:{k}.{j}")
            else:
                rep.add(fmt, eb, gb, tag=f"v{i}:{k}")
                if once and _zero_sign_differs(fmt, eb, gb):
                    self.zero_sign_wrong += 1

    def _fields(self, cat):
        """{port name: value} of one concatenated dump word (outputs
        concatenated in declared order, first at MSB)."""
        out = {}
        hi = self.out_w
        for p in self.ports:
            if p.direction != "out":
                continue
            out[p.name] = (cat >> (hi - p.width)) & ((1 << p.width) - 1)
            hi -= p.width
        return out

    def _data_field(self, cat):
        """Extract the primary data output from the concatenated dump
        word (outputs concatenated in declared order, first at MSB)."""
        hi = self.out_w
        for p in self.ports:
            if p.direction != "out":
                continue
            if p.name in ("y", "d"):
                return (cat >> (hi - p.width)) & ((1 << p.width) - 1)
            hi -= p.width
        return cat


def _val(fmt, bits):
    """A decoded value for a message (blocks as their element list)."""
    try:
        v = fmt.decode(bits)
    except Exception:  # noqa: BLE001
        return "invalid"
    if isinstance(v, list):
        return "[" + ", ".join(_short(x) for x in v[:6]) + (", ..." if len(v) > 6 else "") + "]"
    return _short(v)


def _short(v):
    from fractions import Fraction
    if isinstance(v, Fraction):
        if v.denominator == 1:
            return str(v.numerator)
        f = float(v)
        return f"{f:.6g}" if abs(f) < 1e300 else f"{v.numerator}/{v.denominator}"
    return str(v)


def _is_hex(s):
    try:
        int(s, 16)
        return True
    except ValueError:
        return False


# ---------------------------------------------------------------- build --


def build_verification(spec, out_dir, emit_stub=False):
    unit = spec["unit"]
    n_random = spec.get("n_random", 200)
    seed = spec.get("seed", 1)
    if unit == "alu":
        ports, vecs, meta, expected, out_fmt = _build_alu(spec, n_random,
                                                          seed)
    elif unit == "vec_sfu":
        ports, vecs, meta, expected, out_fmt = _build_sfu(spec, n_random,
                                                          seed)
    elif unit == "vec_dot_acc":
        ports, vecs, meta, expected, out_fmt = _build_dot(spec, n_random,
                                                          seed)
    else:
        raise ValueError(f"unknown unit {unit}")

    ref_fn = spec.get("expected_fn")
    if ref_fn is not None:
        # frozen-algorithm reference (loop conformance gates): the
        # expected word comes from the target's own model, not from
        # the ideal operator
        expected = [ref_fn(v) for v in vecs]
    budget = _budget_from_spec(spec)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tb_driven = tuple(spec.get("_tb_driven") or ())
    in_ports = [p for p in ports if p.direction == "in" and p.name not in tb_driven]
    in_w = sum(p.width for p in in_ports)
    packed = []
    for v in vecs:
        word = 0
        for p in in_ports:
            word = (word << p.width) | (v.get(p.name, 0)
                                        & ((1 << p.width) - 1))
        packed.append(word)
    tb_gen.write_hex(out / "vectors.hex", packed, in_w)
    exact_gate = any(name == "bit_exact" for name, _o, _b in budget.bounds)
    out_w = sum(p.width for p in ports if p.direction == "out")
    exp_file = None
    if exact_gate:
        tb_gen.write_hex(out / "expected.hex", expected, out_w)
        exp_file = "expected.hex"
    dut = spec.get("dut_name") or {"alu": "alu_core",
                                   "vec_sfu": "sfu_core",
                                   "vec_dot_acc": "dot_core"}[unit]
    tb = tb_gen.emit_tb(dut, ports, len(vecs),
                        latency=spec.get("latency_cycles", 0),
                        var_latency=spec.get("variable_latency_max", 0),
                        expected_file=exp_file, tb_driven=tb_driven,
                        preload=spec.get("_preload"))
    (out / "tb.sv").write_text(tb)
    if emit_stub:
        (out / "stub.sv").write_text(tb_gen.emit_stub(
            dut, ports, clocked=spec.get("latency_cycles", 0) > 0
            or spec.get("variable_latency_max", 0) > 0,
            var_latency=spec.get("variable_latency_max", 0) > 0))
    freeze = {"spec": {k: v for k, v in spec.items()
                       if not callable(v) and k != "_preload"},
              "n_vectors": len(vecs),
              "vector_sha256": stimulus.freeze(vecs,
                                               [p.name for p in in_ports]),
              "ports": [[p.name, p.direction, p.width] for p in ports]}
    (out / "freeze.json").write_text(json.dumps(freeze, indent=1))
    return Verification(spec, ports, vecs, meta, expected,
                        out_fmt, budget, out, mode_budgets_of(spec))


def _one_budget(b):
    """A Budget of one {metric: bound} mapping; `bit_exact` is the exact
    gate rather than a bound."""
    if b.get("bit_exact") is True:
        return Budget.exact()
    return Budget([(k, "<=", v) for k, v in b.items()])


def mode_budgets_of(spec):
    """{accuracy mode: its Budget} when the core's operating mode is a
    runtime control, else None. The judge scores each mode's vectors
    against that mode's budget rather than the run against one bound."""
    if not spec.get("accuracy_mode") or not isinstance(spec.get("budget"), (list, tuple)):
        return None
    from chialu.verify.alu_ref import accuracy_budgets
    return {i: _one_budget(b) for i, b in enumerate(accuracy_budgets(spec))}


def _budget_from_spec(spec):
    from chialu.sfu_accuracy import report_fixed
    if report_fixed(spec):
        return Budget([])
    if spec.get("unit") == "vec_dot_acc" and spec.get("dot_contract") == "architecture":
        return Budget.exact()
    b = spec.get("budget")
    if isinstance(b, (list, tuple)):
        # the run's gate over every mode: bit-exact only when every mode is
        from chialu.verify.alu_ref import accuracy_budgets
        per = accuracy_budgets(spec)
        if per and all(x.get("bit_exact") is True for x in per):
            return Budget.exact()
        bounds = {}
        for one in per:
            for k, v in one.items():
                if k != "bit_exact":
                    bounds[k] = max(bounds.get(k, v), v)
        return Budget([(k, "<=", v) for k, v in bounds.items()]) if bounds else Budget([])
    if b:
        return _one_budget(b)
    if spec.get("constraints") is not None:
        return Budget.from_constraints(spec["constraints"])
    if spec.get("unit") == "vec_sfu":
        return Budget([("max_ulp", "<=", 1.0)])
    if spec.get("accuracy", "exact") == "exact":
        return Budget.exact()
    raise ValueError("approximate spec needs an explicit budget "
                     "({metric: bound}) or ADIR constraints")


# -- per-unit assembly ---------------------------------------------------


def _build_alu(spec, n_random, seed):
    """chialu.ALU over modes (docs/formats-and-options.md): the legal
    (mode, op) pairs, the ports, the vectors (with the runtime option
    selections and the sr_rnd words) and the expected y, d and flags."""
    from chialu.verify import alu_ref as A
    spec = A.normalize_spec(spec)
    lay = A.alu_layout(spec)
    modes, ops, legal = lay["modes"], lay["ops"], lay["legal"]
    for op in ops:
        if not any(o == op for _, o in legal):
            raise ValueError(f"op {op!r} is legal in none of the modes")
    ports = lay["core_in"] + lay["core_out"]
    sr = (lay["v_max"], lay["sr_bits"]) if lay["sr"] else None
    vecs, meta = stimulus.plan_alu(modes, ops, legal, n_random, seed,
                                   controls=lay["controls"], sr=sr,
                                   exhaustive=bool(spec.get("exhaustive")),
                                   unary=A.UNARY, ternary=set(A.FUSED_OPS))
    conv = A.conventions_of(spec)
    conv["quotient_semantics"] = list(spec.get("quotient_semantics") or ["truncate_zero"])
    options = {"sr_bits": lay["sr_bits"], "flags": lay["flags"],
               "tininess": spec.get("tininess", "after")}
    layout = {"y_w": lay["y_w"], "in_w": lay["in_w"], "d_w": lay["d_w"],
              "dual_in_y": lay["dual_in_y"]}
    out_ws = [p.width for p in lay["core_out"]]
    expected = []
    for v, m in zip(vecs, meta):
        ctrl = A.vector_ctrl(spec, m.get("ctrl"))
        y, d, fw = A.alu_expected(modes, m["mode"], m["op"], m["lane_pairs"],
                                  ctrl, conv, options, m.get("words"), layout)
        word = y
        vals = {"y": y, "d": d, "flags": fw}
        word = 0
        for p in lay["core_out"]:
            word = (word << p.width) | (vals[p.name] & ((1 << p.width) - 1))
        expected.append(word)
    out_fmt = modes[0][1]
    return ports, vecs, meta, expected, out_fmt


def _build_sfu(spec, n_random, seed):
    """chialu.VecSFU over modes: ports from sfu_layout, vectors and slot
    tables from plan_sfu, expected y and flags from sfu_expected. The
    table interface (clk, tbl_*) is driven by the testbench; slot vectors
    are tagged exact in the meta."""
    from chialu.verify import sfu_ref as S
    spec_in = spec
    spec = S.normalize_sfu_spec(spec)
    lay = S.sfu_layout(spec)
    S.validate_sfu_modes(lay["modes"], spec)
    ports = lay["core_in"] + lay["core_out"]
    sr = (lay["v_max"], lay["sr_bits"]) if lay["sr"] else None
    from chialu.sfu_accuracy import report_fixed
    complete = None
    if report_fixed(spec):
        from chialu.verify.sfu_range import complete_plan
        complete, evidence = complete_plan(lay, int(spec.get("range_max_vectors", 65536)))
        spec_in["_sfu_range_plan"] = evidence
    if complete is not None:
        vecs, meta, tables, preload = complete
    else:
        vecs, meta, tables, preload = stimulus.plan_sfu(
            lay, n_random, seed, controls=lay["controls"], sr=sr,
            exhaustive=bool(spec.get("exhaustive")))
    spec_in["_tables"] = [[list(c) for c in t] for t in tables]
    spec_in["_preload"] = preload
    spec_in["_tb_driven"] = ("clk", "tbl_we", "tbl_addr", "tbl_data") if lay["slots"] else ()
    expected = []
    for v, m in zip(vecs, meta):
        ctrl = S.vector_ctrl(spec, m.get("ctrl"))
        y, fw = S.sfu_expected(spec, lay, m["mode"], m["fn"], m["x"], ctrl, m.get("words"), tables)
        vals = {"y": y, "flags": fw}
        word = 0
        for p in lay["core_out"]:
            word = (word << p.width) | (vals[p.name] & ((1 << p.width) - 1))
        expected.append(word)
    return ports, vecs, meta, expected, lay["modes"][0][1]


def _build_dot(spec, n_random, seed):
    """chialu.VecDotAcc over modes: ports from dot_layout, vectors from
    plan_dot, expected d and flags from dot_expected."""
    from chialu.verify import dot_ref as D
    spec = D.normalize_dot_spec(spec)
    lay = D.dot_layout(spec)
    D.validate_dot_modes(lay["modes"], lay["accumulate"])
    ports = lay["core_in"] + lay["core_out"]
    sr = (lay["v_max"], lay["sr_bits"]) if lay["sr"] else None
    vecs, meta = stimulus.plan_dot(lay, n_random, seed, controls=lay["controls"], sr=sr)
    expected = []
    for v, m in zip(vecs, meta):
        ctrl = D.vector_ctrl(spec, m.get("ctrl"))
        vals = D.dot_outputs(spec, lay, m["mode"], m["a"], m["b"], m.get("c"), ctrl, m.get("words"))
        word = 0
        for p in lay["core_out"]:
            word = (word << p.width) | (vals[p.name] & ((1 << p.width) - 1))
        expected.append(word)
    return ports, vecs, meta, expected, lay["modes"][0]["fd"]


# -- checker-side bundle -------------------------------------------------


def build_fault_verification(spec, verification, out_dir,
                             n_random_masks=2000):
    """Fault bundle over an existing Verification: masks.hex +
    fault_tb.sv + a checker(dump) -> FaultReport verdict."""
    out = Path(out_dir)
    y = next(p for p in verification.ports
             if p.direction == "out" and p.name in ("y", "d"))
    plan = FaultPlan.build(y.width, len(verification.vecs),
                           spec.get("seed", 1), n_random_masks)
    tb_gen.write_hex(out / "masks.hex", [m for m, _ in plan.masks],
                     y.width)
    core = spec.get("dut_name", "alu_core")
    checker = spec.get("checker_name", "alu_checker")
    ports = list(verification.ports)
    kw = {}
    if spec.get("unit") == "alu":
        from chialu.verify import alu_ref as A
        lay = A.alu_layout(A.normalize_spec(spec))
        core_names = [p.name for p in lay["core_in"]]
        extra = list(lay["chk_extra"])
        ports = list(lay["core_in"]) + extra + list(lay["core_out"])
        chk_outs = []
        if lay["d_w"]:
            chk_outs.append("d")
        if lay["flags"] and spec.get("check_flags"):
            chk_outs.append("flags")
        kw = {"core_ins": core_names,
              "chk_ins": core_names + [p.name for p in extra],
              "chk_outs": chk_outs}
    elif spec.get("unit") == "vec_dot_acc":
        from chialu.verify import dot_ref as D
        lay = D.dot_layout(D.normalize_dot_spec(spec))
        core_names = [p.name for p in lay["core_in"]]
        extra = list(lay["chk_extra"])
        ports = list(lay["core_in"]) + extra + list(lay["core_out"])
        chk_outs = ["flags"] if (lay["flags"] and spec.get("check_flags")) else []
        kw = {"core_ins": core_names,
              "chk_ins": core_names + [p.name for p in extra],
              "chk_outs": chk_outs}
    tb = tb_gen.emit_fault_tb(core, checker, ports,
                              len(verification.vecs), len(plan.masks),
                              data_out=y.name, **kw)
    (out / "fault_tb.sv").write_text(tb)

    if spec.get("detect"):
        # explicit {metric: (op, bound)} bounds (loop targets)
        detect = DetectBudget([(k, op, b)
                               for k, (op, b) in spec["detect"].items()])
    elif spec.get("constraints"):
        detect = DetectBudget.from_constraints(spec["constraints"])
    else:
        detect = DetectBudget([("false_alarms", "==", 0),
                               ("single_bit_coverage", "==", 1.0)])

    # the checker checks the exact accuracy modes alone, so a mask landing on a
    # vector of an approximate mode is outside the gate (section 3.4 of the spec)
    checked = None
    if spec.get("unit") == "alu" and spec.get("accuracy_mode"):
        from chialu.verify.alu_ref import checked_modes
        ms = set(checked_modes(spec))
        n_vec = len(verification.vecs)
        checked = [i for i in range(len(plan.masks))
                   if verification.accuracy_mode_of(i % n_vec) in ms] if n_vec else []
        checked = set(checked)
    # a pair the check table leaves unchecked (detect none) raises no alarm by contract, so a mask
    # landing on its vector is outside the gate
    unchecked = {(int(mi), str(op)) for mi, op in ((spec.get("check") or {}).get("unchecked") or ())}
    if spec.get("unit") == "alu" and unchecked and verification.meta:
        n_vec = len(verification.vecs)
        keep = {i for i in range(len(plan.masks))
                if (verification.meta[i % n_vec]["mode"], verification.meta[i % n_vec]["op"]) not in unchecked}
        checked = keep if checked is None else (checked & keep)

    planned = {}
    for i, (_mask, kind) in enumerate(plan.masks):
        if checked is not None and i not in checked:
            continue
        planned[kind] = planned.get(kind, 0) + 1

    def check(dump_path):
        rep = FaultReport()
        lines = Path(dump_path).read_text().split()
        protocol_fail = 0
        for i, ((mask, kind), ln) in enumerate(zip(plan.masks, lines)):
            if checked is not None and i not in checked:
                continue
            if not _is_hex(ln):
                # an alarm the simulator leaves at X is a protocol failure,
                # as it is for the conformance judge; a row skipped here
                # would leave single_bit_coverage at its empty value of 1.0
                protocol_fail += 1
                continue
            alarm = (int(ln, 16) >> y.width) & 1
            if kind == "clean":
                rep.add_clean(alarm)
            else:
                rep.add_fault(kind, mask, alarm)
        ok, viol = detect.verdict(rep)
        if protocol_fail:
            ok = False
            viol.append(f"{protocol_fail} fault rows carry no hex alarm word "
                        f"(X or TIMEOUT)")
        counted = {"clean": rep.clean_n, "single": rep.single_n,
                   "random": rep.random_n, "stuck": rep.stuck_n}
        for kind in sorted(planned):
            if counted.get(kind, 0) != planned[kind]:
                ok = False
                viol.append(f"{counted.get(kind, 0)} of {planned[kind]} "
                            f"{kind} rows were counted")
        if len(lines) < len(plan.masks):
            ok = False
            viol.append(f"fault dump has {len(lines)} of "
                        f"{len(plan.masks)} lines")
        return ok, viol, rep

    return plan, check
