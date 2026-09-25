"""Error-checking model: golden expectations for checker verdicts.

Two campaigns (docs/checker-spec-plan.md, "What `random_alias` means"):

* the seam campaign (`FaultPlan.build`, the bundle's fault_tb.sv): an
  XOR mask on the core's data output before the checker sees it, a
  corruption drawn uniformly over the output word; it measures
  `output_alias` and the single-bit coverage of the code;
* the grouped campaign (`FaultPlan.build_grouped`, run by
  chialu.eda.fault per candidate): the masks partitioned by the
  vector's (mode, op) into the check rule groups, each group under the
  seam masks and under one-bit corruptions of the internal nets its
  units declare (chialu.verify.fault_sites); a corruption the datapath
  masks is not a fault, one that reaches the output and raises no alarm
  is an `escape`, which is the quantity a rule's `random_alias` asks
  about.

Contracts verified (ADIR ErrorDetect vocabulary):
  false_alarms == 0        clean vectors never raise check_err
  single_bit_coverage == c every 1-bit output corruption must alarm
                           (c = 1.0 in the shipped templates)
  random_alias <= r        fraction of random multi-bit corruptions
                           that escape without alarm
  escape <= r              fraction of internal corruptions that reach
                           the output and escape without alarm
"""

from __future__ import annotations

from dataclasses import dataclass, field

from chialu.verify.stimulus import Rng


def _stratified(items, count, rng):
    """`count` members of `items`, spread over the list and drawn from
    `rng`. The list is cut into `count` consecutive cells of near-equal
    size and one member of each cell is drawn, so a run of members that
    share a property takes a share of the picks in proportion to its
    length. A stimulus lays its vectors out in one run per (mode, op)
    pair, so a pick over a group's vector list reaches every pair of the
    group. Where `count` exceeds the list, every member is taken
    `count // len(items)` times and the remainder is spread over the
    list. The draw comes from `rng` alone, so the same seed gives the
    same pick."""
    items = list(items)
    n = len(items)
    if n == 0 or count <= 0:
        return []
    full, rest = divmod(count, n)
    out = items * full
    for j in range(rest):
        lo, hi = (j * n) // rest, ((j + 1) * n) // rest
        out.append(items[lo + rng.below(max(1, hi - lo))])
    return out


def _by_pair(value):
    """{(mode, op): [member]} of an input a caller gives per pair, or
    {None: [member]} of a flat sequence, which carries no pair."""
    if isinstance(value, dict):
        return {key: list(members) for key, members in value.items()}
    return {None: list(value or [])}


def _vectors_per_net(nets_by_pair, vectors_by_pair):
    """{(path, width): [vector index]} of the vectors the unit at each
    net serves. A net the caller lists under a (mode, op) pair takes the
    vectors of that pair, so a corruption of the net is driven while its
    unit is selected rather than while the unit is idle and masks it. A
    net the caller lists without a pair takes every vector of the
    group."""
    every = [i for pair in vectors_by_pair for i in vectors_by_pair[pair]]
    served: dict = {}
    for pair, nets in nets_by_pair.items():
        vectors = vectors_by_pair.get(pair) if pair is not None else None
        for net in nets:
            served.setdefault(tuple(net), []).extend(vectors or every)
    return served


@dataclass
class FaultPlan:
    out_width: int
    masks: list = field(default_factory=list)     # (mask, kind)
    # the grouped campaign (docs/checker-spec-plan.md): one row per fault, {"kind", "group", "vector", "site", "mask"};
    # sites[0] is the output seam (an XOR mask), sites[k] = (path, width, bit) an internal net's one-bit corruption
    rows: list = field(default_factory=list)
    sites: list = field(default_factory=lambda: [("seam", 0, 0)])
    groups: list = field(default_factory=list)

    @classmethod
    def build_grouped(cls, out_width, vectors_by_group, seed, n_random_masks=2000, n_clean=128,
                      sites_by_group=None, n_sites=None):
        """A campaign per rule group: clean vectors (the false-alarm pass),
        one-bit seam masks, random seam masks (`output_alias`), and
        one-bit corruptions of internal nets the group's units declare
        (`escape`), `n_sites` of them (the random mask count by default).
        Every row names its vector and its site explicitly.

        `_stratified` picks the vectors of each class from `seed`, so a
        class spreads over the group's (mode, op) pairs rather than over
        the head of the group's vector list, and the same seed gives the
        same plan. The stuck rows spread over the group's nets the same
        way, so the site set does not depend on how many nets the
        candidate declares.

        `vectors_by_group[group]` is a sequence of vector indices, or a
        mapping from a (mode, op) pair to the indices of its vectors.
        `sites_by_group[group]` is a sequence of (path, width) nets, or
        a mapping from a (mode, op) pair to the nets of the unit that
        serves the pair. Where both are mappings, a net's rows drive
        vectors of the pairs its unit serves, so the corruption reaches
        the data output instead of being masked by an idle unit."""
        rng = Rng(seed ^ 0xFA17)
        plan = cls(out_width)
        site_index = {("seam", 0, 0): 0}
        n_stuck = n_sites if n_sites is not None else n_random_masks
        for group in vectors_by_group:
            vectors_by_pair = _by_pair(vectors_by_group[group])
            vecs = [i for pair in vectors_by_pair for i in vectors_by_pair[pair]]
            if not vecs:
                continue
            plan.groups.append(group)
            for v in _stratified(vecs, min(len(vecs), n_clean), rng):
                plan.rows.append({"kind": "clean", "group": group, "vector": v, "site": 0, "mask": 0})
            for b, v in enumerate(_stratified(vecs, out_width, rng)):
                plan.rows.append({"kind": "single", "group": group, "vector": v, "site": 0, "mask": 1 << b})
            for v in _stratified(vecs, n_random_masks, rng):
                m = rng.bits(out_width)
                while m == 0:
                    m = rng.bits(out_width)
                plan.rows.append({"kind": "random", "group": group, "vector": v, "site": 0, "mask": m})
            served = _vectors_per_net(_by_pair((sites_by_group or {}).get(group)), vectors_by_pair)
            rows_per_net: dict = {}
            for net in _stratified(list(served), n_stuck, rng):
                rows_per_net[net] = rows_per_net.get(net, 0) + 1
            for (path, width), count in rows_per_net.items():
                for v in _stratified(served[(path, width)], count, rng):
                    bit = rng.bits(20) % max(1, width)
                    key = (path, width, bit)
                    if key not in site_index:
                        site_index[key] = len(plan.sites)
                        plan.sites.append(key)
                    plan.rows.append({"kind": "stuck", "group": group, "vector": v,
                                      "site": site_index[key], "mask": 0})
        plan.masks = [(r["mask"], r["kind"]) for r in plan.rows]
        return plan

    @classmethod
    def build(cls, out_width, n_vectors, seed, n_random_masks=2000,
              n_clean=None):
        """Zero masks (the false-alarm pass), single-bit masks and random
        multi-bit masks, interleaved over the mask index. Mask index i
        applies to vector i mod n_vectors, which is the map the harness
        and the testbench share, so the campaign reaches the first
        len(masks) vectors alone and a kind that holds a contiguous block
        of the index range reaches one (mode, op) pair alone.
        `_stratified` places each kind's masks over the whole index
        range from `seed`, so every kind reaches every pair the campaign
        reaches."""
        rng = Rng(seed ^ 0xFA17)
        n_clean = n_clean if n_clean is not None else min(n_vectors, 512)
        total = n_clean + out_width + n_random_masks
        single_at = set(_stratified(range(total), out_width, rng))
        clean_at = set(_stratified([i for i in range(total) if i not in single_at], n_clean, rng))
        masks, bit = [], 0
        for i in range(total):
            if i in single_at:
                masks.append((1 << bit, "single"))
                bit += 1
            elif i in clean_at:
                masks.append((0, "clean"))
            else:
                m = rng.bits(out_width)
                while m == 0:
                    m = rng.bits(out_width)
                masks.append((m, "random"))
        return cls(out_width, masks)


@dataclass
class FaultReport:
    clean_alarms: int = 0        # false alarms over the clean pass
    clean_n: int = 0
    single_missed: int = 0
    single_n: int = 0
    random_escaped: int = 0
    random_n: int = 0
    stuck_n: int = 0             # internal one-bit corruptions that reached the data output
    stuck_escaped: int = 0       # ... and raised no alarm: the escape
    stuck_masked: int = 0        # corruptions the datapath masked (the output unchanged): not faults
    missed_examples: list = field(default_factory=list)

    def add_clean(self, alarm):
        self.clean_n += 1
        if alarm:
            self.clean_alarms += 1

    def add_fault(self, kind, mask, alarm, changed_output=True):
        """changed_output: a mask that leaves the used output bits
        unchanged (e.g. beyond a narrow result) is not a fault."""
        if not changed_output:
            return
        if kind == "single":
            self.single_n += 1
            if not alarm:
                self.single_missed += 1
                if len(self.missed_examples) < 16:
                    self.missed_examples.append(("single", mask))
        elif kind == "stuck":
            self.stuck_n += 1
            if not alarm:
                self.stuck_escaped += 1
                if len(self.missed_examples) < 16:
                    self.missed_examples.append(("stuck", mask))
        else:
            self.random_n += 1
            if not alarm:
                self.random_escaped += 1

    def add_masked(self):
        """An internal corruption the datapath masked: the output is right, so no fault occurred."""
        self.stuck_masked += 1

    @property
    def escape(self):
        """The share of internal corruptions that reached the output and raised no alarm (None unmeasured)."""
        if not self.stuck_n:
            return None
        return self.stuck_escaped / self.stuck_n

    @property
    def single_bit_coverage(self):
        if not self.single_n:
            return 1.0
        return 1.0 - self.single_missed / self.single_n

    @property
    def random_alias(self):
        if not self.random_n:
            return 0.0
        return self.random_escaped / self.random_n

    def summary(self):
        out = {"false_alarms": self.clean_alarms,
               "clean_n": self.clean_n,
               "single_bit_coverage": self.single_bit_coverage,
               "single_n": self.single_n,
               "random_alias": self.random_alias,
               "random_n": self.random_n}
        if self.stuck_n or self.stuck_masked:
            out.update(escape=self.escape, stuck_n=self.stuck_n, stuck_masked=self.stuck_masked)
        return out


class DetectBudget:
    """Verdict from ErrorDetect constraints over a FaultReport."""

    def __init__(self, bounds):
        self.bounds = bounds

    @classmethod
    def for_rule(cls, detect: dict | None, n_masks: int):
        """The gate of one check rule group: no false alarm; the rule's
        `random_alias` as the bound on the measured seam alias and on the
        measured escape, plus three standard deviations of a rate measured
        over n_masks faults; the rule's `single_bit` as the coverage floor.
        A rule without a requirement gates the false alarms alone."""
        bounds = [("false_alarms", "==", 0)]
        detect = detect or {}
        if detect.get("random_alias") is not None:
            p = float(detect["random_alias"])
            bound = round(p + 3 * (p * (1 - p) / max(1, n_masks)) ** 0.5, 5)
            bounds += [("random_alias", "<=", bound), ("escape", "<=", bound)]
        if detect.get("single_bit") is not None:
            bounds.append(("single_bit_coverage", ">=", float(detect["single_bit"])))
        return cls(bounds)

    @classmethod
    def from_constraints(cls, constraints):
        bounds = []
        for c in constraints or []:
            if c.metric.objective == "ErrorDetect":
                bounds.append((c.metric.name, c.op, c.bound))
        return cls(bounds)

    def verdict(self, report: FaultReport):
        violations = []
        vals = {"false_alarms": report.clean_alarms,
                "single_bit_coverage": report.single_bit_coverage,
                "random_alias": report.random_alias,
                "escape": report.escape}
        for name, op, bound in self.bounds:
            v = vals.get(name)
            if v is None:
                continue
            ok = {"<=": lambda: v <= bound, ">=": lambda: v >= bound,
                  "==": lambda: v == bound}[op]()
            if not ok:
                violations.append(f"ErrorDetect.{name} {op} {bound}: "
                                  f"measured {v}")
        return (not violations), violations
