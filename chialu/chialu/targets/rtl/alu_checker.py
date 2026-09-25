"""Generated checker RTL for chialu.ALU (the GENERATED submodule the loop
never edits). The checker sees the module inputs and the data outputs
only, never the core's structure (docs/formats-and-options.md section 7).

The spec's `checker_family` picks the coded check; every (mode, op)
pair the code does not cover is duplicated:
  residue                  integer and fixed-point add, sub, adc, sbb, neg, abs
                           (the wrap of a W-bit result is recovered from the
                           patterns: carry = y < a for add, borrow = a < b for
                           sub, ...) and mul_wide (the exact product): r(y)
                           predicted from r(a), r(b) and the wrap, mod M; two's
                           complement and unsigned patterns
  inverse_residue          the same prediction carried as its modular complement
                           M - r, so the coded word (r(y) + check) is congruent
                           to zero (JPL STAR): a check channel stuck at a
                           plausible constant still mismatches
  multi_residue            the residue check under two or three low-cost moduli
                           2^a - 1 with coprime a (3, 7, 31): an error escapes
                           only when every modulus misses it
  rns_redundant            the residue check under a base set of low-cost
                           moduli plus redundant ones (base_moduli_count +
                           redundant_moduli channels of 2^a - 1, a prime); the
                           per-channel disagreements form the syndrome that
                           locates a single faulty channel (correction), the
                           verdict is any disagreement (the interface carries no
                           corrected result)
  an_code                  the checker's own AN-coded replica: the operands
                           premultiplied by A (3, 7, 15, 31), the add-class ops
                           and mul_wide computed on the codewords with the wrap
                           recovered as the residue family recovers it; the
                           verdict is A*y differing from the coded result or the
                           coded result failing its own divisibility by A (the
                           replica's self-check). d3_correct: the correct result
                           is the coded result divided by A (the decode), at
                           per_op or domain_exit
  parity_prediction_adder  add, sub, adc, sbb, neg, abs: the result parity is
                           the parity of the two addends, the carry-in and the
                           carry vector, the carries from the checker's own
                           replica chain (duplicate_carry); the compare is one
                           parity bit per lane
  parity_prediction_multiplier
                           mul_wide and mul: the product parity predicted from
                           the parity of the partial-product rows (an AND array
                           or radix-4 Booth rows, `recoding`) and the parity of
                           the carry vectors of the checker's own row-by-row
                           reduction (P(s) = P(x) ^ P(r) ^ P(c) per addition);
                           the compare is one parity bit; the check is over
                           the replica
  berger                   the same ops as the parity adder: the ones count of
                           the sum predicted from the addends' counts, the
                           carry-in and the carry vector (W(s) = W(a) + W(b) +
                           c_in - sum of the carries into bits 1..n-1 - 2
                           c_out), compared with the count of the result: every
                           unidirectional error moves the count
  reduced_precision        a narrow replica of replica_width_bits: the add class
                           and mul_wide of the integer modes on the top bits of
                           the operands (the low part's carry leaves the
                           result's top bits one replica ulp of uncertainty; the
                           product's top bits |a_hi| + |b_hi| + 1), fadd, fsub
                           and fmul of the float modes on significands truncated
                           to R bits through the engine, the result compared
                           within 2^(scale - R + 4) (bound_type absolute: the
                           scale of the operands, relative_ulp: the scale of the
                           result for the product); errors below the bound
                           escape by design (sub-linear area, coverage limited
                           to large errors)
  duplication              every pair: a pruned copy of the reference datapath
                           (chialu.targets.rtl.alu_seed) recomputes the result
                           and the checker compares bit for bit, the bits above
                           the op's result width included (they must be 0);
                           replication 3 compares two copies
  SR window                with check_sr false (or the check_sr_sel input low)
                           a stochastically rounded result is accepted when it
                           equals the truncated result or the one rounded away
                           from zero (two further copies of the reference with
                           forced rounding)
  flags, d                 compared against the copy when check_flags is set /
                           the unary_dual second result exists

The comparator slot (`checker.comparator.family`, the two-rail space)
realizes the final compare of every coded word and of the duplicated
outputs:
  direct_compare           a word equality (the default)
  two_rail_tree            the pairs (p_i, ~q_i) of the predicted and the
                           computed word through a tree of two-rail checker
                           cells (z0 = x0 y0 | x1 y1, z1 = x0 y1 | x1 y0) of
                           `tree_arity` inputs per node; the output pair is a
                           codeword (01 or 10) only when the words match and
                           the tree is fault-free, check_err = the pair is not
                           alternating; fail_safe_lockout and the
                           state_element realization need a state element the
                           combinational checker lacks, so the tree stands at
                           `none` / `translator`
  m_out_of_n_checker       the 2k-bit word {p, ~q} is a k-out-of-2k codeword
                           when the words' weights agree: the Anderson-Metze
                           checker over the two k-bit groups (f = OR over odd j
                           of T_j(A) T_(k-j)(B), g = the same over even j, T_j
                           the threshold "at least j ones"), as a literal
                           two-level AND-OR form for k <= 5, a cellular
                           threshold array (AND/OR, unate) otherwise or under
                           multilevel_unate / cellular_threshold_array, or as
                           2-out-of-4 translator cells over pairs of positions
                           feeding a two-rail tree (translator_cascade); the
                           weight check misses a corruption that moves one bit
                           each way, which the alias model and the single-bit
                           floor account for; code_class one_out_of_n checks
                           every pair as a 1-out-of-2 word through the two-rail
                           tree (a full equality)
  majority_voter           under duplication: `inputs` - 1 reference copies and
                           the datapath's output voted bit for bit, check_err =
                           the output differs from the vote (a faulty copy is
                           masked, a faulty datapath is caught);
                           another family keeps the direct compare
                           (a vote needs replicas)

The checker's contract per accuracy mode: a unit whose operating mode is
a runtime control (`accuracy_ctl: runtime`) drives `accuracy_mode_sel`,
and each mode carries its own budget. The checker checks the modes whose
budget is the exact result, where `check_err` means a fault, and holds
`check_err` low in a mode whose budget is a statistical bound, where a
disagreement with the reference is the approximation the mode asks for
rather than a fault. A unit with no exact mode is rejected at load, since
the checker would have nothing to check. The fault gate scores the masks
that land on a vector of a checked mode alone
(chialu.verify.harness.build_fault_verification).

At the core/checker seam the parity and the count checks need their
own carry replica, so their area is that of a carry chain plus a
narrow compare; their saving over duplication is the compare channel
(one parity bit, a log2 count) rather than the replica, which is what
the families save in a datapath that carries the code along. The AN
code and the reduced-precision replica are replicas too: the AN code
buys its self-check, the narrow replica its width.
"""
from __future__ import annotations

from itertools import combinations

from chialu.targets.rtl.alu_seed import alu_ref_module
from chialu.targets.rtl.engine import FORCE_NONE, FORCE_RAZ, FORCE_RTZ, Conventions, Engine
from chialu.targets.rtl.residue import residue_bits, residue_module
from chialu.targets.rtl import families as FAM
from chialu.targets.rtl.writer import SvModule
from chialu.verify import alu_ref as A
from chialu.verify.formats import BlockFormat, FixedFormat, FloatFormat, IntFormat, _floor_log2

FAMILIES = ("residue", "inverse_residue", "multi_residue", "parity_prediction_adder", "berger",
            "duplication", "an_code", "rns_redundant", "parity_prediction_multiplier", "reduced_precision")
COMPARATORS = ("direct_compare", "two_rail_tree", "m_out_of_n_checker", "majority_voter")
LOW_COST_MODULI = (3, 7, 31, 127)      # 2^a - 1 with pairwise coprime a (2, 3, 5, 7)
GENERAL_COPRIME_MODULI = (5, 9, 11, 13)   # pairwise coprime moduli that are not 2^a - 1 (their residue is a modulo)
LOW_COST_EXPONENTS = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31)   # primes: the moduli 2^a - 1 are pairwise coprime
RESIDUE_OPS = ("add", "sub", "adc", "sbb", "neg", "abs", "mul_wide")
ADDER_OPS = ("add", "sub", "adc", "sbb", "neg", "abs")
FLOAT_RP_OPS = ("fadd", "fsub", "fmul")
CODED_OPS = {"residue": RESIDUE_OPS, "inverse_residue": RESIDUE_OPS, "multi_residue": RESIDUE_OPS,
             "rns_redundant": RESIDUE_OPS, "an_code": RESIDUE_OPS,
             "parity_prediction_adder": ADDER_OPS, "berger": ADDER_OPS,
             "parity_prediction_multiplier": ("mul_wide", "mul"),
             "reduced_precision": ADDER_OPS + ("mul_wide",) + FLOAT_RP_OPS,
             "duplication": ()}
PATTERN_OPS = {"and", "or", "xor", "not", "popcount", "clz", "ctz", "shl",
               "shr_logical", "shr_arith", "rol", "ror", "cmp", "fcmp",
               "min", "max", "fmin", "fmax", "fabs", "fneg"}
# the pins of a family (spec["checker_pins"]) and their defaults (the first members of their domains)
PIN_DEFAULTS = {
    "residue": {"generator_style": "csa_tree"},
    "inverse_residue": {"inverse_on": "check_channel"},
    "multi_residue": {"moduli_set": "low_cost_2a_minus_1"},
    "an_code": {"A": 3},
    "rns_redundant": {"base_moduli_count": 3, "redundant_moduli": 1},
    "berger": {"construction": "berger"},
    "parity_prediction_adder": {"parity_groups": 1, "carry_scheme": "duplicate_carry", "interleaving": False},
    "parity_prediction_multiplier": {"recoding": "none"},
    "reduced_precision": {"replica_width_bits": 4, "bound_type": "absolute"},
    "duplication": {"replication": 2},
}
COMPARATOR_PIN_DEFAULTS = {
    "direct_compare": {},
    "two_rail_tree": {"tree_arity": 2},
    "m_out_of_n_checker": {"code_class": "k_out_of_2k", "realization": "two_level_and_or"},
    "majority_voter": {"inputs": 3},
}


def checker_pins(spec: dict) -> dict:
    """The family's pins at their defaults, overridden by
    spec["checker_pins"]. `validate_pins` raises on a key the declared
    family does not declare and on a value outside a declared domain, so
    a misspelled key no longer renders the default in silence. The keys
    the family declares but this table does not hold, which are `modulus`
    and `moduli_count`, are read by `checker_params` from the spec
    instead, so they pass the check and leave the returned pins
    unchanged."""
    from chialu.targets.rtl.families import validate_pins
    family = str(spec.get("checker_family") or "residue")
    supplied = dict(spec.get("checker_pins") or {})
    validate_pins("checker", family, supplied)
    out = dict(PIN_DEFAULTS.get(family, {}))
    for k, v in supplied.items():
        if k in out:
            out[k] = v
    return out


def comparator_of(spec: dict) -> tuple:
    """(comparator family, pins) of a spec (spec["comparator"] =
    {"family": ..., pin: value}); direct_compare when undeclared.
    `validate_pins` raises on a key the declared comparator family does
    not declare and on a value outside a declared domain."""
    from chialu.targets.rtl.families import validate_pins
    c = dict(spec.get("comparator") or {})
    fam = str(c.pop("family", "direct_compare") or "direct_compare")
    if fam not in COMPARATORS:
        raise ValueError(f"checker comparator {fam!r}: one of {COMPARATORS}")
    validate_pins("checker_comparator", fam, c)
    pins = dict(COMPARATOR_PIN_DEFAULTS.get(fam, {}))
    for k, v in c.items():
        if k in pins:
            pins[k] = v
    return fam, pins


def checker_params(spec: dict) -> tuple:
    """(family, moduli) of a spec: the moduli are the residue-like
    families' ([] for the others)."""
    family = str(spec.get("checker_family") or "residue")
    if family not in FAMILIES:
        raise ValueError(f"checker family {family!r}: one of {FAMILIES}")
    if family in ("residue", "inverse_residue"):
        return family, [int(spec.get("modulus") or 15)]
    if family == "multi_residue":
        pins = checker_pins(spec)
        base = GENERAL_COPRIME_MODULI if str(pins.get("moduli_set", "low_cost_2a_minus_1")) == "general_coprime" else LOW_COST_MODULI
        moduli = spec.get("moduli") or base[:int(spec.get("moduli_count") or 2)]
        return family, [int(m) for m in moduli]
    if family == "rns_redundant":
        pins = checker_pins(spec)
        n = int(pins["base_moduli_count"]) + int(pins["redundant_moduli"])
        return family, [(1 << a) - 1 for a in LOW_COST_EXPONENTS[:n]]
    return family, []


def coded_eligible(family: str, fmt, op, dual_possible) -> bool:
    """The coded check applies to integer patterns in two's complement or
    unsigned (fixed point shares them); the reduced-precision replica
    also to fadd, fsub and fmul of a float mode with a significand; a
    dual-capable unary op is duplicated instead (its second result lives
    in d or the upper y)."""
    if op not in CODED_OPS[family]:
        return False
    if family == "reduced_precision" and op in FLOAT_RP_OPS:
        return isinstance(fmt, FloatFormat) and fmt.man_bits > 0 and not fmt.exp_only
    if isinstance(fmt, (FixedFormat, IntFormat)):
        enc = fmt.encoding
    else:
        return False
    if enc not in ("twos_complement", "unsigned"):
        return False
    if op in ("neg", "abs") and dual_possible:
        return False
    return True


def residue_eligible(fmt, op, dual_possible) -> bool:
    return coded_eligible("residue", fmt, op, dual_possible)


# ---------------------------------------------------------------- comparators

def _trc_cell(p, q):
    """The two-rail checker cell over two pairs (x0, x1): a codeword
    output (01 or 10) only when both inputs are codewords."""
    return (f"({p[0]} & {q[0]}) | ({p[1]} & {q[1]})", f"({p[0]} & {q[1]}) | ({p[1]} & {q[0]})")


def two_rail_tree_module(name: str, n: int, arity: int = 2) -> str:
    """A tree of two-rail checker cells over n pairs (x1[i], x0[i]):
    every node folds `arity` pairs; the root pair is (z0, z1)."""
    m = SvModule(name)
    m.port("x1", "in", n)
    m.port("x0", "in", n)
    m.port("z0", "out", 1)
    m.port("z1", "out", 1)
    pairs = [(f"x0[{i}]", f"x1[{i}]") for i in range(n)]
    lvl = 0
    while len(pairs) > 1:
        nxt = []
        for j in range(0, len(pairs), arity):
            group = pairs[j:j + arity]
            cur = group[0]
            for k, q in enumerate(group[1:]):
                z0, z1 = _trc_cell(cur, q)
                w0 = m.logic(f"l{lvl}_{j}_{k}_0")
                w1 = m.logic(f"l{lvl}_{j}_{k}_1")
                m.assign(w0, z0)
                m.assign(w1, z1)
                cur = (w0, w1)
            nxt.append(cur)
        pairs = nxt
        lvl += 1
    m.assign("z0", pairs[0][0])
    m.assign("z1", pairs[0][1])
    return m.render()


def _threshold_wires(m: SvModule, x: str, k: int, tag: str, two_level: bool) -> list:
    """T_j(x) for j = 0..k ("at least j of the k bits set"): a literal
    OR of ANDs over the j-subsets (two_level) or the cellular threshold
    array t[i][j] = t[i-1][j] | (x_i & t[i-1][j-1]) (AND/OR alone)."""
    out = ["1'b1"]
    if two_level:
        for j in range(1, k + 1):
            terms = [" & ".join(f"{x}[{b}]" for b in c) for c in combinations(range(k), j)]
            w = m.logic(f"{tag}t{j}")
            m.assign(w, " | ".join(f"({t})" for t in terms))
            out.append(w)
        return out
    prev = ["1'b1"] + ["1'b0"] * k
    for i in range(k):
        cur = ["1'b1"]
        for j in range(1, k + 1):
            w = m.logic(f"{tag}c{i}_{j}")
            m.assign(w, f"{prev[j]} | ({x}[{i}] & {prev[j-1]})")
            cur.append(w)
        prev = cur
    return prev


def k_out_of_2k_module(name: str, k: int, realization: str = "two_level_and_or") -> str:
    """The Anderson-Metze checker of the k-out-of-2k code over the 2k-bit
    word {x1, x0}: with A = x1 and B = x0 (a balanced partition), f = OR
    over odd j of T_j(A) & T_(k-j)(B), g = the same over even j; (f, g)
    is 01 or 10 for a codeword, 00 (weight below k) or 11 (above)
    otherwise. The threshold functions are a literal two-level form for
    k <= 5 under two_level_and_or, a cellular AND/OR array otherwise."""
    m = SvModule(name)
    m.port("x1", "in", k)
    m.port("x0", "in", k)
    m.port("f", "out", 1)
    m.port("g", "out", 1)
    two_level = realization == "two_level_and_or" and k <= 5
    ta = _threshold_wires(m, "x1", k, "a", two_level)
    tb = _threshold_wires(m, "x0", k, "b", two_level)
    odd = [f"({ta[j]} & {tb[k-j]})" for j in range(1, k + 1, 2)]
    even = [f"({ta[j]} & {tb[k-j]})" for j in range(0, k + 1, 2)]
    m.assign("f", " | ".join(odd) if odd else "1'b0")
    m.assign("g", " | ".join(even))
    return m.render()


def translator_cascade_module(name: str, k: int) -> str:
    """Pairs of positions as 2-out-of-4 words checked by translator
    cells (f = (a0 | a1) & (b0 | b1), g = a0 a1 | b0 b1: a two-rail
    pair), the cells' pairs and a leftover pair folded by a two-rail
    tree (Marouf-Friedman cascade)."""
    m = SvModule(name)
    m.port("x1", "in", k)
    m.port("x0", "in", k)
    m.port("f", "out", 1)
    m.port("g", "out", 1)
    pairs = []
    for i in range(0, k - 1, 2):
        f = m.logic(f"c{i}_f")
        g = m.logic(f"c{i}_g")
        m.assign(f, f"(x1[{i}] | x1[{i+1}]) & (x0[{i}] | x0[{i+1}])")
        m.assign(g, f"(x1[{i}] & x1[{i+1}]) | (x0[{i}] & x0[{i+1}])")
        pairs.append((f, g))
    if k % 2:
        pairs.append((f"x0[{k-1}]", f"x1[{k-1}]"))
    lvl = 0
    while len(pairs) > 1:
        nxt = []
        for j in range(0, len(pairs) - 1, 2):
            z0, z1 = _trc_cell(pairs[j], pairs[j + 1])
            w0 = m.logic(f"l{lvl}_{j}_0")
            w1 = m.logic(f"l{lvl}_{j}_1")
            m.assign(w0, z0)
            m.assign(w1, z1)
            nxt.append((w0, w1))
        if len(pairs) % 2:
            nxt.append(pairs[-1])
        pairs = nxt
        lvl += 1
    m.assign("f", pairs[0][1])
    m.assign("g", pairs[0][0])
    return m.render()


# ---------------------------------------------------------------- the checker

class _Group:
    """One check rule group: the (mode, op) pairs it selects, the family
    the group binds with its own pins, its comparator and its adder
    slots, and the pairs the code covers (`coded`) against the ones the
    fallback decides (`replica`, `unchecked`)."""
    __slots__ = ("gid", "name", "pairs", "family", "moduli", "pins", "cmp_fam", "cmp_pins", "slots",
                 "detect", "fallback", "coded", "replica", "unchecked", "residue_like")

    def __init__(self, gid, name, pairs, family, moduli, pins, cmp_fam, cmp_pins, slots, detect, fallback):
        self.gid, self.name, self.pairs = gid, name, frozenset(pairs)
        self.family, self.moduli, self.pins = family, list(moduli), dict(pins)
        self.cmp_fam, self.cmp_pins, self.slots = cmp_fam, dict(cmp_pins), dict(slots)
        self.detect, self.fallback = detect, fallback
        self.coded, self.replica, self.unchecked = frozenset(), frozenset(), frozenset()
        self.residue_like = family in ("residue", "inverse_residue", "multi_residue", "rns_redundant")


def _legacy_group(spec: dict, legal) -> list:
    """The one group of the `check_en` + `checker.*` spelling: the unit's
    family over every legal pair, a replica for the rest."""
    family, moduli = checker_params(spec)
    cmp_fam, cmp_pins = comparator_of(spec)
    slots = {k: dict(spec[k]) for k in CHECKER_SLOTS if k != "comparator" and isinstance(spec.get(k), dict)}
    pins = checker_pins(spec)
    if family in ("residue", "inverse_residue"):
        pins["modulus"] = moduli[0]
    if family == "multi_residue":
        pins["moduli_count"] = len(moduli)
    return [_Group(0, "all", legal, family, moduli, pins, cmp_fam, cmp_pins, slots,
                   spec.get("detect"), "duplicate")]


def _rule_groups(spec: dict, legal) -> tuple:
    """The groups of a `check` block (spec["check"]: groups with their
    pairs, family, pins, comparator, slots, detect and fallback, plus the
    unchecked pairs of `detect: none`)."""
    table = spec["check"]
    groups = []
    for gid, rec in enumerate(table.get("groups") or []):
        family = str(rec["family"])
        if family not in FAMILIES:
            raise ValueError(f"check rule {rec.get('name')!r}: checker family {family!r} has no generator")
        own = dict(rec.get("pins") or {})
        sub = {"checker_family": family, "checker_pins": own}
        if family in ("residue", "inverse_residue") and "modulus" in own:
            sub["modulus"] = int(own["modulus"])
        if family == "multi_residue" and "moduli_count" in own:
            sub["moduli_count"] = int(own["moduli_count"])
        _fam, moduli = checker_params(sub)
        comp = dict(rec.get("comparator") or {})
        cmp_fam, cmp_pins = comparator_of({"comparator": comp} if comp else {})
        pairs = {(int(mi), str(op)) for mi, op in rec.get("pairs") or ()}
        outside = pairs - set(legal)
        if outside:
            raise ValueError(f"check rule {rec.get('name')!r}: pairs outside the unit's legal pairs: {sorted(outside)}")
        groups.append(_Group(gid, str(rec.get("name") or f"rule{gid}"), pairs, family, moduli, dict(checker_pins(sub), **own),
                             cmp_fam, cmp_pins, {k: dict(v) for k, v in (rec.get("slots") or {}).items()},
                             rec.get("detect"), str(rec.get("fallback") or table.get("fallback") or "duplicate")))
    unchecked = {(int(mi), str(op)) for mi, op in table.get("unchecked") or ()}
    return groups, unchecked


def check_groups(spec: dict) -> tuple:
    """(groups, unchecked pairs, replica pairs) of a normalized checked
    spec, under either spelling. A group's pairs split into the pairs
    its family's code covers (`coded`), the pairs its fallback hands to
    the replica, and the pairs it leaves unchecked; `fallback: error`
    over an uncovered pair is an error here, so a build never buys a
    replica a rule forbade. Under `check_flags` every pair is a replica
    pair, since the data codes do not predict the flags."""
    spec = A.normalize_spec(spec)
    lay = A.alu_layout(spec)
    modes, legal = lay["modes"], lay["legal"]
    dual_possible = lay["d_w"] > 0 or lay["dual_in_y"]
    check_flags = bool(spec.get("check_flags"))
    if isinstance(spec.get("check"), dict):
        groups, unchecked = _rule_groups(spec, legal)
    else:
        groups, unchecked = _legacy_group(spec, legal), set()
    seen: dict = {}
    for g in groups:
        for pr in g.pairs:
            if pr in seen:
                raise ValueError(f"check rules {seen[pr]!r} and {g.name!r} both select {pr}")
            seen[pr] = g.name
        coded = {(mi, op) for mi, op in g.pairs if coded_eligible(g.family, modes[mi][1], op, dual_possible) and not check_flags}
        rest = g.pairs - coded
        if rest and g.fallback == "error":
            raise ValueError(f"check rule {g.name!r} ({g.family}): fallback error, and the code does not cover "
                             + ", ".join(f"{modes[mi][1].name}/{op}" for mi, op in sorted(rest)))
        g.coded = frozenset(coded)
        if g.fallback == "none":
            g.unchecked, g.replica = frozenset(rest), frozenset()
        else:
            g.replica, g.unchecked = frozenset(rest), frozenset()
    all_unchecked = set(unchecked) | {pr for g in groups for pr in g.unchecked}
    replica = {pr for g in groups for pr in g.replica}
    return groups, all_unchecked, replica


def check_manifest(spec: dict) -> list:
    """One row per legal (format, op) pair: the rule that selected it,
    the mechanism (`code`, `replica`, `unchecked`), the family and its
    pins where a code covers it, and the model's `output_alias` and
    `single_bit` for that code (a prediction; `escape` is a measurement
    the fault campaign adds). Written beside the verification files as
    check_manifest.json."""
    spec = A.normalize_spec(spec)
    lay = A.alu_layout(spec)
    modes = lay["modes"]
    groups, unchecked, _replica = check_groups(spec)
    by_pair = {}
    for g in groups:
        for pr in g.pairs:
            by_pair[pr] = g
    rows = []
    for mi, op in sorted(lay["legal"], key=lambda t: (t[0], modes[t[0]][1].name, t[1])):
        count, fmt = modes[mi]
        g = by_pair.get((mi, op))
        row = {"mode": mi, "format": fmt.name, "op": op, "rule": g.name if g else "default"}
        if (mi, op) in unchecked or g is None:
            row["mechanism"] = "unchecked"
        elif (mi, op) in g.coded:
            comparator = {"family": g.cmp_fam, **g.cmp_pins}
            row.update(mechanism="code", family=g.family, pins=dict(g.pins), comparator=comparator,
                       moduli=list(g.moduli),
                       output_alias=alias_probability(g.family, g.moduli, [(count, fmt)], g.pins, comparator),
                       single_bit=single_bit_floor(g.family, [(count, fmt)], g.pins, comparator))
        else:
            row.update(mechanism="replica", family=g.family, escape=0.0,
                       reason="check_flags" if spec.get("check_flags") else "the code does not cover the op")
        if g is not None and g.detect:
            row["detect"] = dict(g.detect)
        rows.append(row)
    return rows


def alu_checker_sv(spec: dict, name: str = "alu_checker") -> tuple[str, list]:
    """The checker module for an ALU spec under its `checker_family`.
    Returns (rtl, protected_ops) where protected_ops lists the ops the
    code checks (the rest are compared against the reference copy,
    which detects any corruption)."""
    spec = A.normalize_spec(spec)
    groups, unchecked_pairs, replica_pairs = check_groups(spec)
    lay = A.alu_layout(spec)
    modes, ops, legal = lay["modes"], lay["ops"], lay["legal"]
    y_w, d_w, v_max = lay["y_w"], lay["d_w"], lay["v_max"]
    flags = lay["flags"]
    nf = len(flags)
    check_flags = bool(spec.get("check_flags"))
    dual_possible = d_w > 0 or lay["dual_in_y"]
    check_sr_vals = list(spec.get("check_sr") or [True])
    sr = lay["sr"]
    window_possible = sr and (False in check_sr_vals)
    window_runtime = sr and len(check_sr_vals) > 1
    opw = max(1, (len(ops) - 1).bit_length())
    mdw = max(1, (len(modes) - 1).bit_length())
    core_in = lay["core_in"]
    # ---- which pairs each group's code covers; the rest are replica pairs or unchecked
    coded_pairs = {pr for g in groups for pr in g.coded}
    by_pair = {pr: g for g in groups for pr in g.pairs}
    protected = sorted({op for _, op in coded_pairs})
    # ---- the replica: one reference copy (the coded and the unchecked pairs pruned from it); the duplication
    # group with the most copies sets the copy count, and a majority voter in a duplication group votes
    dup_groups = [g for g in groups if g.family == "duplication"]
    vote = any(g.cmp_fam == "majority_voter" for g in dup_groups)
    n_copies = 1
    for g in dup_groups:
        n_copies = max(n_copies, int(g.cmp_pins["inputs"]) - 1 if g.cmp_fam == "majority_voter"
                       else max(1, int(g.pins.get("replication", 2)) - 1))
    # the comparator of the replica compare: the first group that hands pairs to the replica
    replica_cmp = next(((g.cmp_fam, g.cmp_pins) for g in groups if g.replica or g.family == "duplication"),
                       (groups[0].cmp_fam, groups[0].cmp_pins) if groups else ("direct_compare", {}))
    G = None                                   # the group whose verdicts the helpers below render
    mods = [alu_ref_module(spec, f"{name}_ref", FORCE_NONE, skip=coded_pairs | unchecked_pairs)]
    for j in range(1, n_copies):
        mods.append(mods[0].replace(f"module {name}_ref", f"module {name}_ref{j}", 1))
    if window_possible:
        # the window copies serve only pairs that round: pattern ops are pruned
        skip_w = coded_pairs | unchecked_pairs | {(mi, op) for mi, op in legal if op in PATTERN_OPS}
        mods.append(alu_ref_module(spec, f"{name}_ref_t", FORCE_RTZ, skip=skip_w))
        mods.append(alu_ref_module(spec, f"{name}_ref_u", FORCE_RAZ, skip=skip_w))
    res_mods: dict = {}
    for g in groups:
        if not g.residue_like:
            continue
        widths = set()
        for mi, op in g.coded:
            f = modes[mi][1]
            widths.add(f.width)
            if op == "mul_wide":
                widths.add(2 * f.width)
        for M in g.moduli:
            for w in sorted(widths):
                res_mods.setdefault(f"{name}_res{w}_m{M}",
                                    residue_module(f"{name}_res{w}_m{M}", w, M, str(g.pins.get("generator_style", "csa_tree"))))
    mods += list(res_mods.values())
    cmp_mods: dict = {}
    # ---- the checker module
    m = SvModule(name)
    m.ports_from(core_in)
    m.ports_from(lay["chk_extra"])
    m.port("y", "in", y_w)
    if d_w:
        m.port("d", "in", d_w)
    if nf and check_flags:
        m.port("flags", "in", v_max * nf)
    m.port("check_err", "out", 1)
    conns = {p.name: p.name for p in core_in}
    for g in groups:
        pairs_text = ", ".join(f"{modes[mi][1].name}/{op}" for mi, op in sorted(g.pairs, key=lambda t: (t[0], t[1])))
        m.raw(f"  // check rule {g.name}: {g.family} over {pairs_text}" + (f"; fallback {g.fallback}" if g.replica or g.unchecked else ""))
        if g.family == "rns_redundant":
            nb = int(g.pins["base_moduli_count"])
            m.raw(f"  //   rns_redundant: base moduli {list(g.moduli[:nb])}, redundant moduli {list(g.moduli[nb:])}; the "
                  f"per-channel disagreements are the syndrome")
        if g.family == "an_code":
            m.raw(f"  //   an_code: A = {g.pins['A']}")
        if g.family == "parity_prediction_multiplier":
            m.raw(f"  //   parity_prediction_multiplier: {g.pins['recoding']} rows")
        if g.family == "reduced_precision":
            m.raw(f"  //   reduced_precision: replica of {g.pins['replica_width_bits']} bits, bound {g.pins['bound_type']}")
        if g.cmp_fam != "direct_compare":
            m.raw(f"  //   comparator: {g.cmp_fam} " + ", ".join(f"{k}={v}" for k, v in g.cmp_pins.items()))
    if unchecked_pairs:
        m.raw("  // unchecked pairs (detect none): " + ", ".join(f"{modes[mi][1].name}/{op}" for mi, op in sorted(unchecked_pairs)))
    outs = {"y": "y_ref"}
    m.logic("y_ref", y_w)
    if d_w:
        m.logic("d_ref", d_w)
        outs["d"] = "d_ref"
    if nf:
        m.logic("flags_ref", v_max * nf)
        outs["flags"] = "flags_ref"
    m.instance(f"{name}_ref", "u_ref", {**conns, **outs})
    copies = [("y_ref", "d_ref", "flags_ref")]
    for j in range(1, n_copies):
        o = {"y": f"y_ref{j}"}
        m.logic(f"y_ref{j}", y_w)
        if d_w:
            m.logic(f"d_ref{j}", d_w)
            o["d"] = f"d_ref{j}"
        if nf:
            m.logic(f"flags_ref{j}", v_max * nf)
            o["flags"] = f"flags_ref{j}"
        m.instance(f"{name}_ref{j}", f"u_ref{j}", {**conns, **o})
        copies.append((f"y_ref{j}", f"d_ref{j}", f"flags_ref{j}"))
    if window_possible:
        for sfx in ("t", "u"):
            m.logic(f"y_{sfx}", y_w)
            o = {"y": f"y_{sfx}"}
            if d_w:
                m.logic(f"d_{sfx}", d_w)
                o["d"] = f"d_{sfx}"
            if nf:
                m.logic(f"fl_{sfx}_unused", v_max * nf)
                o["flags"] = f"fl_{sfx}_unused"
            m.instance(f"{name}_ref_{sfx}", f"u_{sfx}", {**conns, **o})
        # is the rounding in effect SR?
        rnds = list(spec["rounding"])
        m.logic("sr_now")
        if len(rnds) > 1:
            sel_w = max(1, (len(rnds) - 1).bit_length())
            m.assign("sr_now", " || ".join(f"(rounding_sel == {sel_w}'d{i})"
                                            for i, r in enumerate(rnds) if r == "SR"))
        else:
            m.assign("sr_now", "1'b1")
        m.logic("win")
        if window_runtime:
            m.assign("win", f"sr_now && !(check_sr_sel ? 1'b{1 if check_sr_vals[1] else 0} : "
                            f"1'b{1 if check_sr_vals[0] else 0})")
        else:
            m.assign("win", "sr_now")
    dual_ctrl = list(spec["unary_dual"])
    m.logic("dual")
    if len(dual_ctrl) > 1:
        m.assign("dual", f"unary_dual_sel[0] ? 1'b{1 if dual_ctrl[1] else 0} : 1'b{1 if dual_ctrl[0] else 0}")
    else:
        m.assign("dual", f"1'b{1 if dual_ctrl[0] else 0}")

    def tmp(nm, expr, width, replica=None):
        m.logic(nm, width)
        if replica is not None:
            a_, b_, cin_, tg = replica
            return slot_add(nm, a_, b_, cin_, width, tg, "carry_replica")
        m.assign(nm, expr)
        return nm

    def slot_add(nm, a_, b_, cin_, width, tg, slot_name, sub=False, signed=False):
        """nm (width bits, the carry-out on top) = a_ + b_ + cin_ (a_ - b_
        under `sub`) through the adder family of the checker's `slot_name`
        slot (the checker's own arithmetic: its carry replica, its row
        chain, its coded operands); the operator when the family has no
        module."""
        slot = G.slots.get(slot_name) or {}
        fam_ = str(slot.get("family") or "ripple_carry")
        sp_ = {k: v for k, v in slot.items() if k != "family"}
        w = width - 1
        # The code/replica arithmetic consumes binary sums and carries,
        # including when its selected CPA has a modular native encoding.
        from chialu.targets.rtl.families.binary_cpa import adder_module
        mod = adder_module(fam_, sp_, w)
        if mod is None:
            m.assign(nm, f"{{1'b0, {a_}}} {'-' if sub else '+'} {{1'b0, {b_}}}" + (f" + {width}'d{cin_}" if cin_ and not sub else ""))
            return nm
        bb = b_
        if sub:
            bb = f"{nm}_nb"
            m.logic(bb, w)
            m.assign(bb, f"~{b_}[{w-1}:0]" if not b_.startswith("{") else f"~({b_})")
        if mod.text:
            cmp_mods.setdefault(mod.name, mod.text)
        ps = ", ".join(f".{k}({v})" for k, v in mod.params.items())
        m.raw(f"  // {tg}: the checker's {slot_name} adder ({fam_})")
        m.raw(f"  {mod.name} " + (f"#({ps}) " if ps else "") + f"u_{tg}_{slot_name} (.a({a_}[{w-1}:0]), .b({bb}), "
              f".cin(1'b{1 if sub else cin_}), .s({nm}[{w-1}:0]), .cout({nm}[{w}]));")
        return nm

    def compare(lhs: str, rhs: str, width: int, tag: str) -> str:
        """The mismatch of two `width`-bit words under the comparator family."""
        cmp_fam, cmp_pins = (G.cmp_fam, G.cmp_pins) if G is not None else replica_cmp
        if cmp_fam == "two_rail_tree" or (cmp_fam == "m_out_of_n_checker" and cmp_pins["code_class"] == "one_out_of_n"):
            arity = int(cmp_pins.get("tree_arity", 2)) if cmp_fam == "two_rail_tree" else 2
            mname = f"{name}_trc{width}_a{arity}"
            if mname not in cmp_mods:
                cmp_mods[mname] = two_rail_tree_module(mname, width, arity)
            z0, z1 = m.logic(f"{tag}_z0"), m.logic(f"{tag}_z1")
            m.instance(mname, f"u_{tag}", {"x1": lhs, "x0": f"~({rhs})", "z0": z0, "z1": z1})
            return f"(~({z0} ^ {z1}))"
        if cmp_fam == "m_out_of_n_checker":
            real = str(cmp_pins["realization"])
            if real == "translator_cascade":
                mname = f"{name}_k2k{width}_tc"
                if mname not in cmp_mods:
                    cmp_mods[mname] = translator_cascade_module(mname, width)
            else:
                style = "sop" if real == "two_level_and_or" else "cell"
                mname = f"{name}_k2k{width}_{style}"
                if mname not in cmp_mods:
                    cmp_mods[mname] = k_out_of_2k_module(mname, width, real)
            f, g = m.logic(f"{tag}_f"), m.logic(f"{tag}_g")
            m.instance(mname, f"u_{tag}", {"x1": lhs, "x0": f"~({rhs})", "f": f, "g": g})
            return f"(~({f} ^ {g}))"
        return f"(({lhs}) != ({rhs}))"

    # duplication verdicts (whole outputs: the copy drives the unused bits to 0 too)
    m.logic("err_dup")
    dup = []
    if vote:
        words = [("y", y_w)] + ([("d", d_w)] if d_w else []) + ([("flags", v_max * nf)] if nf and check_flags else [])
        n_in = n_copies + 1
        for k, (word, ww) in enumerate(words):
            ins = [word] + [c[k] for c in copies]
            v = m.logic(f"{word}_vote", ww)
            if n_in == 3:
                m.assign(v, f"({ins[0]} & {ins[1]}) | ({ins[0]} & {ins[2]}) | ({ins[1]} & {ins[2]})")
            else:
                cnt_w = n_in.bit_length()
                m.raw(f"  always_comb begin\n    for (int b = 0; b < {ww}; b = b + 1) {v}[b] = ("
                      + " + ".join(f"{cnt_w}'({x}[b])" for x in ins) + f") >= {cnt_w}'d{(n_in + 1) // 2};\n  end")
            dup.append(f"({word} != {v})")
    else:
        G = None                                   # compare() reads the replica comparator
        for c in copies:
            dup.append(compare("y", c[0], y_w, f"dup{c[0]}"))
            if d_w:
                dup.append(compare("d", c[1], d_w, f"dup{c[1]}"))
            if nf and check_flags:
                dup.append(compare("flags", c[2], v_max * nf, f"dup{c[2]}"))
    m.assign("err_dup", " | ".join(dup))
    # ---- the coded verdicts per (mode, op)
    verdict = {}          # (mi, op) -> SV expression

    def lane(mi, i, lw):
        """The lane slices of a, b and y, declared once."""
        aL, bL, yn = f"ca{mi}_{i}", f"cb{mi}_{i}", f"cy{mi}_{i}"
        if not m.declared(aL):
            tmp(aL, f"a[{i*lw+lw-1}:{i*lw}]", lw)
            tmp(bL, f"b[{i*lw+lw-1}:{i*lw}]", lw)
            tmp(yn, f"y[{i*lw+lw-1}:{i*lw}]", lw)
        return aL, bL, yn

    def wide(mi, i, lw):
        """The lane's double-width result slice, declared once."""
        if not m.declared(f"cyw{mi}_{i}"):
            tmp(f"cyw{mi}_{i}", f"y[{i*2*lw+2*lw-1}:{i*2*lw}]", 2 * lw)
        return f"cyw{mi}_{i}"

    def res(src, nm, w, M):
        """The residue of `src` mod M as `nm`, declared once."""
        if not m.declared(nm):
            m.logic(nm, residue_bits(M))
            m.instance(f"{name}_res{w}_m{M}", f"u{nm}", {"x": src, "r": nm})
        return nm

    def residue_err(mi, i, op, fmt, M):
        """The residue verdict of one lane under one modulus."""
        lw = fmt.width
        k = residue_bits(M)
        KW = k + 2
        signed = getattr(fmt, "encoding", "") == "twos_complement"
        c_lw = (1 << lw) % M
        c_2lw = (1 << (2 * lw)) % M
        aL, bL, yn = lane(mi, i, lw)
        ra = res(aL, f"ra{mi}_{i}_m{M}", lw, M)
        rb = res(bL, f"rb{mi}_{i}_m{M}", lw, M)
        ry = res(yn, f"ry{mi}_{i}_m{M}", lw, M)
        tag = f"t{mi}_{i}_{ops.index(op)}_m{M}"
        if op == "mul_wide":
            yw = wide(mi, i, lw)
            ryw = res(yw, f"ryw{mi}_{i}_m{M}", 2 * lw, M)
            if signed:
                ras = tmp(f"{tag}a", f"({KW}'d{2*M} + {ra} - ({aL}[{lw-1}] ? {KW}'d{c_lw} : {KW}'d0)) % {KW}'d{M}", KW)
                rbs = tmp(f"{tag}b", f"({KW}'d{2*M} + {rb} - ({bL}[{lw-1}] ? {KW}'d{c_lw} : {KW}'d0)) % {KW}'d{M}", KW)
                got = tmp(f"{tag}y", f"({KW}'d{2*M} + {ryw} - ({yw}[{2*lw-1}] ? {KW}'d{c_2lw} : {KW}'d0)) % {KW}'d{M}", KW)
                pr = tmp(f"{tag}p", f"({ras} * {rbs}) % {2*KW}'d{M}", 2 * KW)
            else:
                got = tmp(f"{tag}y", f"{{{KW-k}'d0, {ryw}}}", KW)
                pr = tmp(f"{tag}p", f"({ra} * {rb}) % {2*KW}'d{M}", 2 * KW)
        else:
            got = tmp(f"{tag}y", f"{{{KW-k}'d0, {ry}}}", KW)
            if op in ("add", "adc"):
                carry = f"({yn} < {aL})" if op == "add" else f"({yn} <= {aL})"
                pr = tmp(tag, f"({KW}'d{2*M} + {ra} + {rb}" + (f" + {KW}'d1" if op == "adc" else "")
                         + f" - ({carry} ? {KW}'d{c_lw} : {KW}'d0)) % {KW}'d{M}", KW)
            elif op in ("sub", "sbb"):
                borrow = f"({aL} < {bL})" if op == "sub" else f"({yn} >= {aL})"
                pr = tmp(tag, f"({KW}'d{2*M} + {ra} - {rb}" + (f" - {KW}'d1" if op == "sbb" else "")
                         + f" + ({borrow} ? {KW}'d{c_lw} : {KW}'d0)) % {KW}'d{M}", KW)
            elif op == "neg":
                pr = tmp(tag, f"({KW}'d{2*M} - {ra} + (({aL} != {lw}'d0) ? {KW}'d{c_lw} : {KW}'d0)) % {KW}'d{M}", KW)
            else:   # abs
                if signed:
                    pr = tmp(tag, f"({aL}[{lw-1}] ? ({KW}'d{2*M} - {ra} + {KW}'d{c_lw}) : ({KW}'d{2*M} + {ra})) % {KW}'d{M}", KW)
                else:
                    pr = tmp(tag, f"{{{KW-k}'d0, {ra}}}", KW)
        if G.family == "inverse_residue":
            # the check channel carries M - r: the coded word sums to 0 mod M; under both_channels the result's
            # residue is complemented as well, so the two complements sum to 0 mod M in the same way
            chk = tmp(f"{tag}c", f"({KW}'d{M} - {pr}[{k-1}:0]) % {KW}'d{M}", KW)
            if str(G.pins.get("inverse_on", "check_channel")) == "both_channels":
                gotc = tmp(f"{tag}g", f"({KW}'d{M} - {got}[{k-1}:0]) % {KW}'d{M}", KW)
                zsum = tmp(f"{tag}z", f"({gotc} + {pr}[{k-1}:0]) % {KW}'d{M}", KW)
                return compare(zsum, f"{KW}'d0", KW, tag)
            zsum = tmp(f"{tag}z", f"({got} + {chk}) % {KW}'d{M}", KW)
            return compare(zsum, f"{KW}'d0", KW, tag)
        return compare(f"{got}[{k-1}:0]", f"{pr}[{k-1}:0]", k, tag)

    def an_err(mi, i, op, fmt):
        """The AN-code verdict of one lane: the checker's coded replica
        (operands times A, the wrap recovered from the patterns) against
        A times the result, plus the replica's own divisibility check."""
        A_ = int(G.pins["A"])
        lw = fmt.width
        abits = A_.bit_length()
        KW = 2 * lw + abits + 3
        signed = getattr(fmt, "encoding", "") == "twos_complement"
        aL, bL, yn = lane(mi, i, lw)
        tag = f"an{mi}_{i}_{ops.index(op)}"
        Ak = f"{KW}'sd{A_}"

        def u(x, w):                                       # the pattern as a positive KW-bit value
            return f"$signed({{{{{KW-w}{{1'b0}}}}, {x}}})"

        def sx(x, w):                                      # the pattern sign-extended
            return f"$signed({{{{{KW-w}{{{x}[{w-1}]}}}}, {x}}})"

        if op == "mul_wide":
            yw = wide(mi, i, lw)
            ext = sx if signed else u
            pred = tmp(f"{tag}p", f"{Ak} * {ext(aL, lw)} * {ext(bL, lw)}", KW)
            got = tmp(f"{tag}g", f"{Ak} * {ext(yw, 2 * lw)}", KW)
        else:
            ca = tmp(f"{tag}a", f"{Ak} * {u(aL, lw)}", KW)
            cb = tmp(f"{tag}b", f"{Ak} * {u(bL, lw)}", KW)
            wrap = f"({Ak} * {KW}'sd{1 << lw})"
            zero = f"{KW}'sd0"
            # the coded operands' sum or difference through the coded_adder slot, the wrap correction after it
            if op in ("add", "adc"):
                m.logic(f"{tag}s", KW + 1)
                slot_add(f"{tag}s", ca, cb, 0, KW + 1, f"{tag}ab", "coded_adder")
                base = f"$signed({tag}s[{KW-1}:0])"
                expr = (f"{base} - (({yn} < {aL}) ? {wrap} : {zero})" if op == "add"
                        else f"{base} + {Ak} - (({yn} <= {aL}) ? {wrap} : {zero})")
            elif op in ("sub", "sbb"):
                m.logic(f"{tag}s", KW + 1)
                slot_add(f"{tag}s", ca, cb, 0, KW + 1, f"{tag}ab", "coded_adder", sub=True)
                base = f"$signed({tag}s[{KW-1}:0])"
                expr = (f"{base} + (({aL} < {bL}) ? {wrap} : {zero})" if op == "sub"
                        else f"{base} - {Ak} + (({yn} >= {aL}) ? {wrap} : {zero})")
            elif op == "neg":
                expr = f"(({aL} != {lw}'d0) ? {wrap} : {zero}) - {ca}"
            else:   # abs
                expr = f"{aL}[{lw-1}] ? ({wrap} - {ca}) : {ca}" if signed else ca
            pred = tmp(f"{tag}p", expr, KW)
            got = tmp(f"{tag}g", f"{Ak} * {u(yn, lw)}", KW)
        selfcheck = f"(({pred} % {Ak}) != {KW}'sd0)"
        return f"({compare(got, pred, KW, tag)} | {selfcheck})"

    def ppm_err(mi, i, op, fmt):
        """The parity verdict of a product: the parity of the partial
        product rows and of the carry vectors of the checker's own
        row-by-row reduction (P(s) = P(x) ^ P(r) ^ P(c) per addition)."""
        lw = fmt.width
        signed = getattr(fmt, "encoding", "") == "twos_complement"
        WW = 2 * lw if op == "mul_wide" else lw
        aL, bL, yn = lane(mi, i, lw)
        yv = wide(mi, i, lw) if op == "mul_wide" else yn
        tag = f"pm{mi}_{i}_{ops.index(op)}"
        if WW > lw:
            a_ext = (f"$signed({{{{{WW-lw}{{{aL}[{lw-1}]}}}}, {aL}}})" if signed
                     else f"$signed({{{{{WW-lw}{{1'b0}}}}, {aL}}})")
        else:
            a_ext = f"$signed({aL})"
        rows = []
        if G.pins["recoding"] == "booth2":
            nd = (lw + 2) // 2 if signed else lw // 2 + 1
            top = 2 * nd - lw                                  # bits above b: the sign (signed) or zeros
            bx = tmp(f"{tag}bx", f"{{{{{top}{{{bL}[{lw-1}]}}}}, {bL}, 1'b0}}" if signed
                     else f"{{{{{top}{{1'b0}}}}, {bL}, 1'b0}}", 2 * nd + 1)
            a2 = f"({a_ext} <<< 1)"
            for j in range(nd):
                t = f"{bx}[{2*j+2}:{2*j}]"
                val = (f"({t} == 3'b011) ? {a2} : ({t} == 3'b100) ? (-{a2}) : "
                       f"({t} == 3'b001 || {t} == 3'b010) ? {a_ext} : ({t} == 3'b101 || {t} == 3'b110) ? (-{a_ext}) : {WW}'sd0")
                rows.append(tmp(f"{tag}r{j}", f"({val}) <<< {2*j}", WW))
        else:
            for j in range(lw):
                neg = "-" if signed and j == lw - 1 else ""       # the sign row of a two's complement array weighs -2^(lw-1)
                rows.append(tmp(f"{tag}r{j}", f"{bL}[{j}] ? (({neg}{a_ext}) <<< {j}) : {WW}'sd0", WW))
        parity = [f"(^{r})" for r in rows]
        s = rows[0]
        for j, r in enumerate(rows[1:], 1):
            m.logic(f"{tag}s{j}x", WW + 1)
            slot_add(f"{tag}s{j}x", s, r, 0, WW + 1, f"{tag}s{j}", "row_adder")
            nxt = tmp(f"{tag}s{j}", f"{tag}s{j}x[{WW-1}:0]", WW)
            cv = tmp(f"{tag}c{j}", f"{s} ^ {r} ^ {nxt}", WW)
            parity.append(f"(^{cv})")
            s = nxt
        pred = tmp(f"{tag}pp", " ^ ".join(parity), 1)
        return compare(f"(^{yv})", pred, 1, tag)

    def rp_err_int(mi, i, op, fmt):
        """The reduced-precision verdict of an integer lane: the op on the
        top R bits of the operands; the result's top bits may differ by
        the low part's carry (0 or 1 replica ulp), the wide product's by
        |a_hi| + |b_hi| + 1."""
        lw = fmt.width
        R = min(int(G.pins["replica_width_bits"]), lw)
        k = lw - R
        signed = getattr(fmt, "encoding", "") == "twos_complement"
        aL, bL, yn = lane(mi, i, lw)
        tag = f"rp{mi}_{i}_{ops.index(op)}"
        ah = tmp(f"{tag}ah", f"{aL}[{lw-1}:{k}]", R)
        bh = tmp(f"{tag}bh", f"{bL}[{lw-1}:{k}]", R)
        if op == "mul_wide":
            W2 = 2 * R + 3
            yw = wide(mi, i, lw)
            yq = tmp(f"{tag}yq", f"{yw}[{2*lw-1}:{2*k}]", 2 * R)

            def ext(x, w):
                return (f"$signed({{{{{W2-w}{{{x}[{w-1}]}}}}, {x}}})" if signed
                        else f"$signed({{{{{W2-w}{{1'b0}}}}, {x}}})")
            pr = tmp(f"{tag}pr", f"{ext(ah, R)} * {ext(bh, R)}", W2)
            m.logic(f"{tag}dfx", W2 + 1)
            slot_add(f"{tag}dfx", tmp(f"{tag}yqx", f"{ext(yq, 2 * R)}", W2), tmp(f"{tag}prx", pr, W2), 0, W2 + 1,
                     f"{tag}d", "replica_adder", sub=True)
            dif = tmp(f"{tag}df", f"$signed({tag}dfx[{W2-1}:0])", W2)
            mag = tmp(f"{tag}mg", f"({dif} < 0) ? -{dif} : {dif}", W2)
            ma = f"(({ext(ah, R)} < 0) ? -{ext(ah, R)} : {ext(ah, R)})"
            mb = f"(({ext(bh, R)} < 0) ? -{ext(bh, R)} : {ext(bh, R)})"
            bnd = tmp(f"{tag}bd", f"{ma} + {mb} + {W2}'sd1", W2)
            return f"({mag} > {bnd})"
        yh = tmp(f"{tag}yh", f"{yn}[{lw-1}:{k}]", R)
        if op == "add":
            base, deltas = f"{ah} + {bh}", (0, 1)
        elif op == "adc":
            base, deltas = f"{ah} + {bh} + {R}'d1", (0, 1)
        elif op in ("sub", "sbb"):
            base, deltas = f"{ah} - {bh}", (0, -1)
        elif op == "neg":
            base, deltas = f"-{ah}", (0, -1)
        else:   # abs
            if signed:
                base, deltas = f"({aL}[{lw-1}] ? -{ah} : {ah})", (0, -1)
            else:
                base, deltas = ah, (0,)
        m.logic(f"{tag}dx", R + 1)
        slot_add(f"{tag}dx", yh, tmp(f"{tag}bs", base, R), 0, R + 1, f"{tag}b", "replica_adder", sub=True)
        dif = tmp(f"{tag}d", f"{tag}dx[{R-1}:0]", R)
        ok = " || ".join(f"({dif} == {R}'d{d % (1 << R)})" for d in deltas)
        return f"!({ok})"

    engines: dict = {}

    def rp_float_fn(mi, fmt):
        """The per-mode check function of the float replica, declared once."""
        fn = f"rp{mi}g{G.gid}_chk"
        if (mi, G.gid) in engines:
            return fn
        e = Engine(f"rp{mi}g{G.gid}", fmt, lay["sr_bits"], sr, targets=[fmt], conv=Conventions.from_spec(spec))
        engines[(mi, G.gid)] = e
        for text in (e.vdecl(), e.arith(), e.unpack_float(fmt, "s")):
            m.function(text)
        P, XT, XW, EW, VW = e.p, e.XT, e.XW, e.EW, e.VW
        W = fmt.width
        R = min(int(G.pins["replica_width_bits"]), fmt.man_bits + 1)
        rel = 1 if G.pins["bound_type"] == "relative_ulp" else 0
        etop = _floor_log2(fmt.max_finite())
        emin = 1 - fmt.bias
        has_nan = 1 if fmt.has_nan else 0
        has_inf = 1 if fmt.has_inf else 0

        def E(nm, x):
            return (f"    {nm} = (({x}[{XW}:1] == 0) && !{x}[0]) ? -100000 : "
                    f"$signed({x}[{XW+EW}:{XW+1}]) + {XW-1};")
        m.function(f'''
  // reduced_precision: the replica of {fmt.name} on {R}-bit significands; err when the result lies beyond
  // 2^(scale - {R} + 4) of the replica's (kind: 0 add, 1 sub, 2 mul)
  function automatic {fn}(input [{W-1}:0] a, input [{W-1}:0] b, input [{W-1}:0] y, input [1:0] kind, input daz);
    logic [{XT-1}:0] xa, xb, xy, na, nb, ar, br, yr, nyr, nxy, d; logic [{VW}:0] ua, ub, uy;
    integer ea, eb, ey, er, ed, eref; logic [1:0] spy, spr; logic zy;
    ua = {P}_unpack_s(a, daz); ub = {P}_unpack_s(b, daz); uy = {P}_unpack_s(y, 1'b0);
    xa = {P}_x(ua[{VW-1}:0]); xb = {P}_x(ub[{VW-1}:0]); xy = {P}_x(uy[{VW-1}:0]);
    na = {P}_norm(xa); nb = {P}_norm(xb);
    // the replica's operands: the top {R} significand bits, the rest and the sticky dropped
    ar = {{na[{XT-1}:{XW+1}], na[{XW}:{XW-R+1}], {{{XW-R}{{1'b0}}}}, 1'b0}};
    br = {{nb[{XT-1}:{XW+1}], nb[{XW}:{XW-R+1}], {{{XW-R}{{1'b0}}}}, 1'b0}};
    yr = (kind == 2'd2) ? {P}_mul(ar, br) : {P}_add(ar, br, kind[0]);
    nyr = {P}_norm(yr); nxy = {P}_norm(xy);
    spy = nxy[{XT-1}:{XT-2}]; spr = nyr[{XT-1}:{XT-2}];
    zy = (nxy[{XW}:1] == 0) && !nxy[0];
{E("ea", "na")}
{E("eb", "nb")}
{E("ey", "nxy")}
{E("er", "nyr")}
    if (spy == 2'd1 || spr == 2'd1) {fn} = (spy != spr) && {has_nan};
    else if (spy == 2'd2 || spr == 2'd2) begin
      // an infinite result: the other side infinite of the same sign, or finite at the top of the range
      // (an overflow the truncated replica or the rounding mode misses)
      if (spy == 2'd2 && spr == 2'd2) {fn} = nxy[{XT-3}] != nyr[{XT-3}];
      else if (spy == 2'd2) {fn} = !(er >= {etop} - 1);
      else {fn} = {has_inf} && !(ey >= {etop} - 1);
    end else if (ey >= {etop} && er >= {etop} - 1) {fn} = 1'b0;   // an overflow saturated by the rounding mode
    else begin
      // the difference on the significands alone (a sticky below the replica's lsb is dropped: the engine's
      // subtraction borrows it, which wraps two equal magnitudes)
      d = {P}_norm({P}_add({{nxy[{XT-1}:1], 1'b0}}, {{nyr[{XT-1}:1], 1'b0}}, 1'b1));
      if ((d[{XW}:1] == 0) && !d[0]) {fn} = 1'b0;
      else begin
        ed = $signed(d[{XW+EW}:{XW+1}]) + {XW-1};
        // the scale of the replica's error: the larger operand for a sum, the product's own magnitude
        // (relative_ulp) or the operands' exponent sum (absolute) for a product
        if (kind == 2'd2) eref = {rel} ? ((ey > er) ? ey : er) : (ea + eb + 2);
        else eref = (ea > eb) ? ea : eb;
        {fn} = ed > eref - {R} + 3;
        if (zy && er < {emin}) {fn} = 1'b0;    // a tiny result flushed to zero
      end
    end
  endfunction''')
        return fn

    def rp_err_float(mi, i, op, fmt):
        lw = fmt.width
        aL, bL, yn = lane(mi, i, lw)
        fn = rp_float_fn(mi, fmt)
        if not m.declared("rp_daz"):
            dz = list(spec["daz_in"])
            m.logic("rp_daz")
            m.assign("rp_daz", f"daz_in_sel[0] ? 1'b{1 if dz[1] else 0} : 1'b{1 if dz[0] else 0}" if len(dz) > 1
                     else f"1'b{1 if dz[0] else 0}")
        kind = {"fadd": 0, "fsub": 1, "fmul": 2}[op]
        return f"{fn}({aL}, {bL}, {yn}, 2'd{kind}, rp_daz)"

    def count_err(mi, i, op, fmt):
        """The parity or the ones-count verdict of one lane: the checker's
        own carry replica gives the carry vector."""
        lw = fmt.width
        signed = getattr(fmt, "encoding", "") == "twos_complement"
        aL, bL, yn = lane(mi, i, lw)
        tag = f"p{mi}_{i}_{ops.index(op)}"

        def form(sfx, a_expr, b_expr, cin):
            """The verdict for y = a' + b' + cin."""
            ap = tmp(f"{tag}{sfx}a", a_expr, lw)
            bp = tmp(f"{tag}{sfx}b", b_expr, lw)
            scheme = str(G.pins.get("carry_scheme", "duplicate_carry")) if G.family == "parity_prediction_adder" else "duplicate_carry"
            if scheme == "carry_dependent_sum" and G.family == "parity_prediction_adder":
                # the carries read off the checked sum itself (c_j = a_j ^ b_j ^ s_j) and the carry-out from the
                # operands' and the sum's top bits: no replica adder, one xor row
                cv = tmp(f"{tag}{sfx}c", f"{ap} ^ {bp} ^ {yn}", lw)
                cout = tmp(f"{tag}{sfx}o", f"(({ap}[{lw-1}] & {bp}[{lw-1}]) | (({ap}[{lw-1}] ^ {bp}[{lw-1}]) & {cv}[{lw-1}]))", 1)
            else:
                # an independent replica adder of the carry_replica family gives the carry vector
                rw = tmp(f"{tag}{sfx}r", None, lw + 1, replica=(ap, bp, cin, f"{tag}{sfx}"))
                cv = tmp(f"{tag}{sfx}c", f"{ap} ^ {bp} ^ {rw}[{lw-1}:0]", lw)
                cout = f"{rw}[{lw}]"
            if G.family == "parity_prediction_adder":
                # P(s) = P(a) ^ P(b) ^ P(c), per parity group: the bits of a group (contiguous, or interleaved
                # every g-th bit), so a group's parity covers its own bits alone
                g = max(1, min(int(G.pins.get("parity_groups", 1)), lw))
                inter = bool(G.pins.get("interleaving", False))
                verdicts = []
                for gi in range(g):
                    bits = list(range(gi, lw, g)) if inter else list(range(gi * lw // g, min(lw, (gi + 1) * lw // g)))
                    if not bits:
                        continue
                    sel = lambda w_: " ^ ".join(f"{w_}[{b}]" for b in bits)
                    pp = tmp(f"{tag}{sfx}p{gi}", f"({sel(ap)}) ^ ({sel(bp)}) ^ ({sel(cv)})", 1)
                    verdicts.append(compare(f"({sel(yn)})", pp, 1, f"{tag}{sfx}g{gi}"))
                return "(" + " | ".join(verdicts) + ")"
            # W(s) = W(a) + W(b) + c_0 - sum of c_1..c_{n-1} - 2 c_n, in the counts' own width; under
            # bose_lin_method2 the check symbol is that count modulo 2^r (r bits), which detects a unidirectional
            # error of at most 2^r - 1 bits rather than any
            cw = max(2, (2 * lw + 2).bit_length() + 1)
            hi = f" - {cw}'($countones({cv}[{lw-1}:1]))" if lw > 1 else ""
            pred_e = (f"{cw}'($countones({ap})) + {cw}'($countones({bp})) + {cw}'({cv}[0]){hi} - ({cw}'d2 * {cw}'({cout}))")
            pred = tmp(f"{tag}{sfx}n", pred_e, cw)
            got = tmp(f"{tag}{sfx}w", f"{cw}'($countones({yn}))", cw)
            if str(G.pins.get("construction", "berger")) == "bose_lin_method2":
                r_ = max(2, min(cw - 1, (lw.bit_length() + 1) // 2 + 1))
                return compare(f"{got}[{r_-1}:0]", f"{pred}[{r_-1}:0]", r_, f"{tag}{sfx}")
            return compare(got, pred, cw, f"{tag}{sfx}")

        if op == "add":
            return form("", aL, bL, 0)
        if op == "adc":
            return form("", aL, bL, 1)
        if op == "sub":
            return form("", aL, f"~{bL}", 1)
        if op == "sbb":
            return form("", aL, f"~{bL}", 0)
        if op == "neg":
            return form("", f"{lw}'d0", f"~{aL}", 1)
        # abs
        if not signed:
            return form("", aL, f"{lw}'d0", 0)
        return f"({aL}[{lw-1}] ? {form('n', f'{lw}' + chr(39) + 'd0', f'~{aL}', 1)} : {form('i', aL, f'{lw}' + chr(39) + 'd0', 0)})"

    for mi, (L, fmt) in enumerate(modes):
        for op in ops:
            if (mi, op) not in legal or (mi, op) not in coded_pairs:
                continue
            G = by_pair[(mi, op)]
            errs = []
            for i in range(L):
                if G.residue_like:
                    errs += [residue_err(mi, i, op, fmt, M) for M in G.moduli]
                elif G.family == "an_code":
                    errs.append(an_err(mi, i, op, fmt))
                elif G.family == "parity_prediction_multiplier":
                    errs.append(ppm_err(mi, i, op, fmt))
                elif G.family == "reduced_precision":
                    errs.append(rp_err_float(mi, i, op, fmt) if op in FLOAT_RP_OPS else rp_err_int(mi, i, op, fmt))
                else:
                    errs.append(count_err(mi, i, op, fmt))
            wout = A.result_width(op, fmt, L)
            hi_zero = f" | (y[{y_w-1}:{wout}] != {y_w-wout}'d0)" if wout < y_w else ""
            v = "(" + " | ".join(errs) + f"){hi_zero}"
            if d_w:
                v += " | (d != '0)"
            verdict[(mi, op)] = v
    G = None
    # ---- window verdicts per (mode, op) with rounded results
    if window_possible:
        for mi, (L, fmt) in enumerate(modes):
            for op in ops:
                if (mi, op) not in legal or (mi, op) in coded_pairs or (mi, op) in unchecked_pairs or op in PATTERN_OPS:
                    continue
                tgt = A.cvt_target(op)
                rf = tgt if tgt is not None else fmt
                terms = []
                res_sets = [("y", 0)]
                if A.is_unary(op) and dual_possible:
                    res_sets.append(("y", lay["y_w"] // 2) if lay["dual_in_y"] else ("d", 0))
                for src, base in res_sets:
                    n_res = A.result_width(op, fmt, L) // rf.width
                    for r in range(n_res):
                        off = base + r * rf.width
                        if isinstance(rf, BlockFormat):
                            we, sz, sw = rf.elem.width, rf.size, rf.scale.width
                            for j in range(sz):
                                o = off + j * we
                                terms.append(f"!({src}[{o} +: {we}] == {src}_t[{o} +: {we}] || {src}[{o} +: {we}] == {src}_u[{o} +: {we}])")
                            o = off + sz * we
                            terms.append(f"({src}[{o} +: {sw}] != {src}_t[{o} +: {sw}])")
                        else:
                            terms.append(f"!({src}[{off} +: {rf.width}] == {src}_t[{off} +: {rf.width}] || {src}[{off} +: {rf.width}] == {src}_u[{off} +: {rf.width}])")
                wout = A.result_width(op, fmt, L)
                if wout < y_w and not lay["dual_in_y"]:
                    terms.append(f"(y[{y_w-1}:{wout}] != {y_w-wout}'d0)")
                win_v = "(" + " | ".join(terms) + ")"
                if nf and check_flags:
                    win_v += " | (flags != flags_ref)"
                verdict[(mi, op, "win")] = win_v
    # ---- the verdict select
    # an approximate mode has no unique correct output, so the verdict stands in the
    # modes whose budget is the exact result and is held low in the others: a
    # disagreement there is the approximation, not a fault (spec section 3.4)
    amodes = list(spec.get("accuracy_mode") or ())
    checked_a = A.checked_modes(spec) if amodes else ()
    gated = bool(amodes) and len(checked_a) < len(amodes)
    tgt = "chk_raw" if gated else "check_err"
    if gated:
        aw = max(1, (len(amodes) - 1).bit_length())
        m.logic("chk_raw")
        m.logic("amode_checked")
        m.assign("amode_checked",
                 " || ".join(f"(accuracy_mode_sel == {aw}'d{k})" for k in checked_a) or "1'b0")
        m.raw(f"  // the checker checks accuracy mode{'s' if len(checked_a) != 1 else ''} "
              f"{', '.join(str(k) for k in checked_a) or 'none'} (the exact budget); in the "
              f"approximate modes check_err is held low")
        m.assign("check_err", "chk_raw && amode_checked")
    blk = m.comb()
    blk.stmt(f"{tgt} = err_dup;")
    if len(modes) > 1:
        blk.open("case (mode)")
    for mi in range(len(modes)):
        if len(modes) > 1:
            blk.open(f"{mdw}'d{mi}: begin")
        if len(ops) > 1:
            blk.open("case (op)")
        for oi, op in enumerate(ops):
            if (mi, op) not in legal:
                if len(ops) > 1:
                    blk.stmt(f"{opw}'d{oi}: {tgt} = 1'b0;   // illegal pair: unconstrained")
                continue
            v = verdict.get((mi, op))
            wv = verdict.get((mi, op, "win"))
            if (mi, op) in unchecked_pairs:
                expr = "1'b0"                          # detect none: the pair is not checked
            elif v is None and wv is None:
                expr = "err_dup"
            elif v is not None:
                expr = v
            else:
                expr = f"win ? ({wv}) : err_dup"
            if len(ops) > 1:
                blk.stmt(f"{opw}'d{oi}: {tgt} = {expr};")
            else:
                blk.stmt(f"{tgt} = {expr};")
        if len(ops) > 1:
            blk.stmt(f"default: {tgt} = 1'b1;")
            blk.close("endcase")
        if len(modes) > 1:
            blk.close("end")
    if len(modes) > 1:
        blk.stmt(f"default: {tgt} = 1'b1;")
        blk.close("endcase")
    mods += list(cmp_mods.values())
    return "\n".join(mods) + "\n" + m.render(), protected


def _count_escape(w: int) -> float:
    """The probability that a random corruption of a w-bit word keeps its
    ones count (the escape of a count or weight compare)."""
    from math import comb
    return sum(comb(w, k) / 2 ** w * comb(k, k // 2) / 2 ** k for k in range(0, w + 1, 2))


def _weight_check(comparator) -> bool:
    """Whether the comparator is a weight (k-out-of-2k) compare."""
    if isinstance(comparator, dict):
        return comparator.get("family") == "m_out_of_n_checker" and comparator.get("code_class", "k_out_of_2k") != "one_out_of_n"
    return comparator == "m_out_of_n_checker"


def alias_probability(family: str, moduli: list, modes, pins: dict | None = None, comparator=None) -> float:
    """The probability that a random corruption of one mode's result
    escapes the coded check, the worst mode: (1/M)^lanes for a residue
    code (the product over the moduli), 2^-lanes for the parities, the
    ones-count preservation probability per lane for berger, 2^-(R-1)
    per lane for the reduced-precision replica (a corruption confined
    to the bits below the replica's resolution), 0 for duplication and
    the AN code (exact compares). A k-out-of-2k comparator escapes a
    corruption that keeps the compared word's weight, which bounds the
    families whose compared words are wider than one bit. Pairs the
    code does not cover are duplicated and never alias, so this is an
    upper bound over the (mode, op) mixture."""
    pins = dict(PIN_DEFAULTS.get(family, {}), **(pins or {}))
    weight_check = _weight_check(comparator)
    worst = 0.0
    for L, fmt in modes:
        is_int = isinstance(fmt, (FixedFormat, IntFormat)) and fmt.encoding in ("twos_complement", "unsigned")
        is_flt = isinstance(fmt, FloatFormat) and fmt.man_bits > 0 and not fmt.exp_only
        if family == "duplication":
            p = _count_escape(L * fmt.width) if weight_check else 0.0
            worst = max(worst, p)
            continue
        if family == "reduced_precision":
            if not (is_int or is_flt):
                continue
            R = min(int(pins["replica_width_bits"]), fmt.width if is_int else fmt.man_bits + 1)
            p = 2.0 ** -(R - 1) if is_int else 2.0 ** -(R - 2)
            worst = max(worst, p ** max(1, L))
            continue
        if not is_int:
            continue
        if family in ("residue", "inverse_residue", "multi_residue", "rns_redundant"):
            p = 1.0
            for M in moduli:
                p /= M
            if weight_check:
                p = max(p, max(_count_escape(residue_bits(M)) for M in moduli))
        elif family in ("parity_prediction_adder", "parity_prediction_multiplier"):
            p = 0.5
        elif family == "an_code":
            p = _count_escape(2 * fmt.width + int(pins["A"]).bit_length() + 3) if weight_check else 0.0
        else:   # berger
            p = max(_count_escape(fmt.width), _count_escape(32) if weight_check else 0.0)
        worst = max(worst, p ** max(1, L))
    return worst


def single_bit_floor(family: str, modes, pins: dict | None = None, comparator=None) -> float:
    """The single-bit coverage a family guarantees by construction: 1.0
    for a code that moves under every one-bit corruption; the fraction
    of the result bits above the replica's resolution for the
    reduced-precision replica (the bits below escape by design; the
    product's wider bound halves the share); 0.5 under a weight
    comparator over words wider than one bit (a weight-preserving
    residue or count change escapes)."""
    pins = dict(PIN_DEFAULTS.get(family, {}), **(pins or {}))
    floor = 1.0
    if family == "reduced_precision":
        for L, fmt in modes:
            if isinstance(fmt, (FixedFormat, IntFormat)) and fmt.encoding in ("twos_complement", "unsigned"):
                R = min(int(pins["replica_width_bits"]), fmt.width)
                floor = min(floor, max(0.0, (R - 2) / (2.0 * fmt.width)))
            elif isinstance(fmt, FloatFormat) and fmt.man_bits > 0 and not fmt.exp_only:
                # the sign, the exponent and the top mantissa bits move the result beyond the bound, except
                # under a cancelled sum whose bound is the operands' scale: half of those bits as the floor
                R = min(int(pins["replica_width_bits"]), fmt.man_bits + 1)
                floor = min(floor, (1 + fmt.exp_bits + max(0, R - 4)) / (2.0 * fmt.width))
    if _weight_check(comparator) and family not in ("duplication", "parity_prediction_adder",
                                                    "parity_prediction_multiplier"):
        floor = min(floor, 0.5)
    return round(floor, 4)


# ---------------------------------------------------------------- feasibility (docs/checker-spec-plan.md)

# the requirement a check rule states, and the mechanism a (format, op) pair gets under a point
REQUIREMENT_KEYS = ("random_alias", "single_bit")
FALLBACKS = ("duplicate", "none", "error")
EXACT_FAMILIES = ("duplication", "an_code")       # an exact compare: escape zero by construction


def _members(domain) -> list:
    if not domain.finite():
        raise ValueError(f"the domain {domain.describe()} is not enumerable")
    return list(domain.members())


def _as_list(v) -> list:
    return list(v) if isinstance(v, (list, tuple, set, frozenset)) else [v]


def _entry_domains(family, entry: dict) -> tuple:
    """(own pin domains, comparator domains, pass-through slot pins) of a
    `choices` entry over one family of checker_space(): a scalar fixes a
    pin, a list is its set, an omitted pin opens the family's domain; a
    pin the family does not own, or a value outside its domain, is an
    error rather than a silent drop (the plan: no pin is shared between
    two families)."""
    own = {}
    for choice, dom in (family.design_choices or {}).items():
        allowed = _members(dom)
        if choice in entry:
            vals = _as_list(entry[choice])
            bad = [v for v in vals if not dom.contains(v)]
            if bad:
                raise ValueError(f"{family.name}.{choice}: {bad} outside {dom.describe()}")
            allowed = [v for v in allowed if v in vals] or vals
        own[choice] = allowed
    cmp_space = family.components.get("comparator")
    comparators = {}
    if cmp_space is not None:
        fams = [f.name for f in cmp_space.families]
        wanted = _as_list(entry["comparator.family"]) if "comparator.family" in entry else fams
        bad = [f for f in wanted if f not in fams]
        if bad:
            raise ValueError(f"{family.name}.comparator.family: {bad} outside {fams}")
        for f in cmp_space.families:
            if f.name not in wanted:
                continue
            pins = {}
            for choice, dom in (f.design_choices or {}).items():
                key = f"comparator.{choice}"
                allowed = _members(dom)
                if key in entry:
                    vals = _as_list(entry[key])
                    bad = [v for v in vals if not dom.contains(v)]
                    if bad:
                        raise ValueError(f"{family.name}.{key}: {bad} outside {dom.describe()}")
                    allowed = [v for v in allowed if v in vals] or vals
                pins[choice] = allowed
            comparators[f.name] = pins
    slots = {}
    known_cmp_pins = {f"comparator.{c}" for f in (cmp_space.families if cmp_space else ()) for c in f.design_choices}
    for k, v in entry.items():
        if k == "family" or k in (family.design_choices or {}) or k in known_cmp_pins \
                or (k == "comparator.family" and cmp_space is not None):
            continue
        slot = k.split(".", 1)[0]
        if slot not in family.components or slot == "comparator":
            raise ValueError(f"{family.name}: {k!r} is neither a pin of the family nor of a slot it opens "
                             f"(slots: {sorted(family.components)})")
        slots[k] = v
    return own, comparators, slots


def _product(domains: dict):
    from itertools import product
    keys = list(domains)
    for combo in product(*(domains[k] for k in keys)):
        yield dict(zip(keys, combo))


def _point_spec(family: str, own: dict) -> dict:
    """A spec fragment checker_params and checker_pins read."""
    spec = {"checker_family": family, "checker_pins": dict(own)}
    if family in ("residue", "inverse_residue") and "modulus" in own:
        spec["modulus"] = int(own["modulus"])
    if family == "multi_residue" and "moduli_count" in own:
        spec["moduli_count"] = int(own["moduli_count"])
    return spec


def feasibility(pairs, requirement=None, fallback: str = "duplicate", declared=None, *,
                dual_possible: bool = False, lanes=None) -> tuple:
    """(candidates, rejected) of a check rule over `pairs`, the (format,
    op) pairs the rule selects (a format as a Format or its name).

    `requirement` is the rule's `detect`: {random_alias: bound,
    single_bit: bound}, either key optional; None states no requirement
    (the numbers are reported and nothing is gated). `fallback` decides a
    pair the family's code does not cover: `duplicate` (a replica),
    `none` (unchecked, legal only without a requirement), `error` (the
    point is rejected). `declared` is the rule's `choices` list, one entry
    per family with its own pins and its slots' pins; None opens every
    family at every pin. `lanes` maps a format name to its lane count
    (one lane by default): a code's escape compounds per lane.

    Three questions, in this order (docs/checker-spec-plan.md): does the
    code cover the ops (else the fallback decides); is the point's
    `output_alias` at most the bound (a prune rather than an admission,
    since the escape at the unit's output is a property of the core's
    structure as well; an exact-compare family passes outright); is its
    single-bit floor at least the bound. A slot pin other than the
    comparator's passes through untouched: neither model depends on the
    adder a carry replica is built from. A point carries every number the
    manifest reports (`output_alias`, `single_bit`) and the mechanism per
    pair (`code`, `replica`, `unchecked`)."""
    from chialu.spaces.checker_spaces import checker_space
    from chialu.verify.formats import parse_format
    if fallback not in FALLBACKS:
        raise ValueError(f"fallback {fallback!r}: one of {FALLBACKS}")
    req = dict(requirement or {})
    bad = set(req) - set(REQUIREMENT_KEYS)
    if bad:
        raise ValueError(f"detect keys {sorted(bad)}: one of {REQUIREMENT_KEYS}")
    gated = any(req.get(k) is not None for k in REQUIREMENT_KEYS)
    def fmt_name(k):
        """A lane key: a format string, a canonical format name, or a Format."""
        if not isinstance(k, str):
            return k.name
        try:
            return parse_format(k).name
        except ValueError:
            return k
    lanes = {fmt_name(k): int(v) for k, v in (lanes or {}).items()}
    fmts = {}
    norm_pairs = []
    for fmt, op in pairs:
        f = parse_format(fmt) if isinstance(fmt, str) else fmt
        fmts.setdefault(f.name, f)
        norm_pairs.append((f.name, str(op)))
    modes = [(max(1, int(lanes.get(name, 1))), f) for name, f in fmts.items()]
    space = {f.name: f for f in checker_space().families}
    entries = list(declared) if declared is not None else [{"family": name} for name in FAMILIES]
    seen = set()
    candidates, rejected = [], []
    for entry in entries:
        entry = dict(entry)
        family = str(entry.get("family", ""))
        if family not in FAMILIES or family not in space:
            raise ValueError(f"checker family {family!r}: one of {FAMILIES}")
        if family in seen:
            raise ValueError(f"checker family {family!r} appears twice in the rule's choices")
        seen.add(family)
        own_doms, cmp_doms, slots = _entry_domains(space[family], entry)
        cmp_points = [None]
        if cmp_doms:
            cmp_points = []
            for cfam, pins in cmp_doms.items():
                # the weight compare enters the model through code_class alone; the other comparator pins pass through
                entering = {k: v for k, v in pins.items() if k == "code_class"}
                passing = {k: v for k, v in pins.items() if k != "code_class"}
                for combo in _product(entering):
                    cmp_points.append((cfam, combo, passing))
        for own in _product(own_doms):
            spec = _point_spec(family, own)
            fam, moduli = checker_params(spec)
            pins = checker_pins(spec)
            for cp in cmp_points:
                comparator = None
                if cp is not None:
                    cfam, entering, passing = cp
                    comparator = {"family": cfam, **entering}
                mechanism = {}
                for name, op in norm_pairs:
                    covered = coded_eligible(family, fmts[name], op, dual_possible)
                    mechanism[(name, op)] = "code" if covered else None
                uncovered = [k for k, v in mechanism.items() if v is None]
                point = {"family": family, "pins": dict(own), "comparator": comparator,
                         "comparator_pins": dict(cp[2]) if cp is not None else {}, "slots": dict(slots),
                         "moduli": list(moduli), "exact": family in EXACT_FAMILIES,
                         "output_alias": alias_probability(family, moduli, modes, pins, comparator),
                         "single_bit": single_bit_floor(family, modes, pins, comparator)}
                reason = None
                if uncovered:
                    if fallback == "error":
                        reason = ("coverage", f"{len(uncovered)} of {len(norm_pairs)} pairs need a replica under fallback error: "
                                              + ", ".join(f"{n}/{o}" for n, o in uncovered[:6]) + (" ..." if len(uncovered) > 6 else ""))
                    elif fallback == "none":
                        if gated:
                            reason = ("coverage", f"{len(uncovered)} pairs would be unchecked under a detection requirement")
                        for k in uncovered:
                            mechanism[k] = "unchecked"
                    else:
                        for k in uncovered:
                            mechanism[k] = "replica"
                point["mechanism"] = {f"{n}/{o}": v for (n, o), v in mechanism.items()}
                point["code_pairs"] = sum(1 for v in mechanism.values() if v == "code")
                point["replica_pairs"] = sum(1 for v in mechanism.values() if v == "replica")
                point["unchecked_pairs"] = sum(1 for v in mechanism.values() if v == "unchecked")
                if reason is None and req.get("random_alias") is not None and not point["exact"] \
                        and point["code_pairs"] and point["output_alias"] > float(req["random_alias"]):
                    reason = ("alias", f"output_alias {point['output_alias']:.4g} exceeds {float(req['random_alias']):.4g}")
                if reason is None and req.get("single_bit") is not None and point["code_pairs"] \
                        and point["single_bit"] < float(req["single_bit"]):
                    reason = ("single_bit", f"single_bit floor {point['single_bit']:.4g} is under {float(req['single_bit']):.4g}")
                if reason is None:
                    candidates.append(point)
                else:
                    rejected.append(dict(point, reject_class=reason[0], reject=reason[1]))
    return candidates, rejected


def feasible_families(pairs, requirement=None, fallback: str = "duplicate", declared=None, *,
                      dual_possible: bool = False, lanes=None) -> list:
    """The candidate points of a check rule (feasibility's survivors): the
    build and `chialu.checkers select` call this one function, so a run
    file is never admitted by a rule the tool would have rejected."""
    return feasibility(pairs, requirement, fallback, declared, dual_possible=dual_possible, lanes=lanes)[0]


# ---------------------------------------------------------------- the checker as a kind of the synthesis database

# the op set every checker row of the database shares: the add class and the wide product on one
# integer mode, so a row measures the family's code over the ops the codes cover and the replica
# of the rest, and two rows compare on the same work (docs/checker-spec-plan.md, staging 2)
CHAR_OPS = RESIDUE_OPS
CHECKER_SLOTS = ("comparator", "coded_adder", "carry_replica", "row_adder", "replica_adder")


def spec_from_pins(family: str, pins: dict, width: int, ops=CHAR_OPS, count: int = 1) -> dict:
    """A normalized checked ALU spec of one int mode at `width` whose
    checker is the point (family, pins): the own pins in the fields the
    generator reads, `comparator.*` in the comparator record, and the
    adder slots (`coded_adder.*`, `carry_replica.*`, `row_adder.*`,
    `replica_adder.*`) in their records."""
    from chialu.verify import alu_ref as A
    own, comparator, slots = {}, {}, {}
    for k, v in (pins or {}).items():
        k = str(k)
        if k.startswith("_"):
            continue
        head, sep, tail = k.partition(".")
        if sep and head in CHECKER_SLOTS:
            (comparator if head == "comparator" else slots.setdefault(head, {}))[tail] = v
        elif not sep:
            own[k] = v
        else:
            raise ValueError(f"checker point pin {k!r}: neither an own pin nor a slot of {CHECKER_SLOTS}")
    spec = {"unit": "alu", "modes": [{"count": int(count), "format": f"int{int(width)}"}], "ops": list(ops),
            "check_en": True, "dut_name": "alu_core", "checker_name": "alu_checker",
            "checker_family": family, "checker_pins": own}
    if family in ("residue", "inverse_residue") and "modulus" in own:
        spec["modulus"] = int(own["modulus"])
    if family == "multi_residue" and "moduli_count" in own:
        spec["moduli_count"] = int(own["moduli_count"])
    if comparator:
        spec["comparator"] = comparator
    for slot, rec in slots.items():
        spec[slot] = rec
    return A.normalize_spec(spec)


def checker_point_ports(width: int, ops=CHAR_OPS) -> list:
    """[(name, direction, width)] of a database point's checker: the
    core's inputs, the data output it reads and check_err; the same for
    every family, since the row op set is fixed."""
    from chialu.verify import alu_ref as A
    spec = spec_from_pins("residue", {"modulus": 31}, width, ops)
    lay = A.alu_layout(spec)
    ports = [(p.name, "in", p.width) for p in list(lay["core_in"]) + list(lay["chk_extra"])]
    ports.append(("y", "in", lay["y_w"]))
    if lay["d_w"]:
        ports.append(("d", "in", lay["d_w"]))
    ports.append(("check_err", "out", 1))
    return ports


def checker_point_module(family: str, pins: dict, width: int, ops=CHAR_OPS):
    """The library Module of a checker point (its text holds the checker,
    its reference copies, residue generators and comparators), or None
    where the generator rejects the point."""
    import hashlib
    import json
    from chialu.targets.rtl import families as FAM
    if family not in FAMILIES:
        return None
    try:
        spec = spec_from_pins(family, pins, width, ops)
    except ValueError:
        return None
    tag = hashlib.sha256(json.dumps({k: v for k, v in (pins or {}).items() if not str(k).startswith("_")},
                                    sort_keys=True, default=str).encode()).hexdigest()[:12]
    name = f"chk_{family}_w{int(width)}_{tag}"
    try:
        text, _protected = alu_checker_sv(spec, name)
    except (ValueError, KeyError, ZeroDivisionError) as e:   # a point the generator has no construction for
        raise ValueError(f"checker point {family} {pins} at {width} bits: {e}") from None
    return FAM.Module(name, {}, text)
