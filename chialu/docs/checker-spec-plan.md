# The check specification: a requirement per format and op

This replaces the run file's `check_en` plus `checker.*` variables with a
rule table that states, for each data format and each op, whether the
result is checked and how well.

## Realization (2026-09-15)

The four stages are realized; this section records where each lives and
where the realization departs from the text below.

| Stage | Realization |
| --- | --- |
| 1. `chialu.checkers` and `feasible_families` | `chialu/checkers.py` (`select`, `explain`, `floor`, `emit`) over `feasibility` / `feasible_families` in `chialu/targets/rtl/alu_checker.py`; `direct_compare` joined `two_rail_space()` (the honest fix); `chialu/verify/checkers_selftest.py` |
| 2. The checker as a kind of the database | kind `checker` in `chialu.synthdb` / `chialu.characterize`: one int mode at the width over the shared op set `CHAR_OPS` (the add class and `mul_wide`), so two rows compare on the same work; `select --pdk` orders by its rows, built locally at widths 8 and 16 (`chialu/synth/nangate45/checker.jsonl`, 288 rows) |
| 3. The rule table | the `check` Struct of `chialu.ALU` (`chialu/modules/check_rules.py`): rules over (format, op) pairs, `detect`, `choices`, `fallback`, `checker_choices`, `default`; the variables `check.<rule>.family`, `check.<rule>.<family>.<pin>`, `.comparator.*` and the adder slots to two levels, narrowed by `feasible_families` at elaboration; the template default `check.*: {search: all}`; `check_manifest.json` in the verify bundle; the generator builds one code per rule group plus one replica (`check_groups`, `alu_checker_sv`); the `check_en` + `checker.*` spelling stays as the one-rule form |
| 4. The fault campaign | `chialu.eda.fault` runs, beside the seam campaign, the grouped campaign (`FaultPlan.build_grouped`, `tb_gen.emit_fault_tb_sites`, `chialu/verify/fault_sites.py`): the masks partitioned by the vector's (mode, op) into the rule groups, each group under seam masks and under one-bit corruptions of the internal nets its units declare; `escape` per group, gated by the rule's `detect` (`DetectBudget.for_rule`) |

Departures and limits:

* A family chosen by the search reaches the checker through the node
  `chialu.eda.checker_gen` (inputs `files: artifacts.verify_bundle`,
  `decl: decl.check`), whose `rtl_text` the `fault` node reads; a
  generator that depends on a searched variable is a node rather than a
  bind-time artifact (ADIR design 3.7). The bind-time `artifacts.checker`
  is the seed's checker (every searched variable at its default).
* The variables place the family name between the rule and the pin, as
  specified; the adder slots of a family are opened to two levels
  (`check.<rule>.<family>.<slot>.family` and that family's own choices).
* The internal sites of stage 4 are the nets a unit module, its lane
  modules and the modules they instantiate declare with a literal
  width, to four levels under the unit instance; a library module's
  parametric nets contribute their one-bit nets alone. A corruption the
  datapath masks is not a fault. This is a one-bit transient at a net,
  which is the single stuck-at model per vector; a burst inside a
  library adder is reached where the lane module declares the net.
* The rule's `random_alias` bounds both quantities: the seam alias
  (`output_alias`) and the measured `escape`, each plus three standard
  deviations of a rate over `verify.n_random_masks` faults.
* `check_flags` keeps today's meaning: every pair is a replica pair,
  since the codes do not predict the flags; the manifest says so.
* The database rows measure one integer mode; a float rule's
  `reduced_precision` point has no row, so `select` leaves its columns
  empty.
* Block-level checking stays the separate document this text describes.

Two defects found on the way are fixed in this realization: the
synthesis nodes dropped nothing before `synth -flatten`, so the ripple
chunk's `keep_hierarchy` attribute (a simulation-side marker) made every
design with a ripple-carry adder fail `synth_ppa` with "synthesis left a
module hierarchy" (`chialu/eda.py:HIERARCHY_RESET`); and the seam plan
applied mask `i` to vector `i mod N`, so a stimulus longer than the mask
list left its later ops, in stimulus order, without a fault (the grouped
plan names the vector of every row). A rule either names a checker family and
its pins or states a detection requirement and leaves the family to the
search, which then optimizes area and delay inside the set of families
that meet it.

## What the run file says today

```yaml
    check_en:
      fixed: true
    checker.family:
      fixed: residue
    checker.modulus:
      fixed: 31
    checker.generator_style:
      fixed: csa_tree
    checker.comparator.family:
      fixed: direct_compare
```

`check_en` is one boolean for the whole unit and `checker.family` is one
family for the whole unit. Three things follow.

* Checking is all or nothing. A unit that needs its multiply checked and
  does not care about its bitwise ops pays for both.
* The op mix decides the cost and the run file cannot see it. Of the 42
  ops, `residue` codes 7 and `chialu/targets/rtl/alu_checker.py:414`
  gives the other 35 a flat replica of the datapath. On an int16 and
  fp16 unit over `add sub mul_wide and shl fadd fsub fmul` the residue
  checker is 4,851 cells against a core of 4,940, and duplication is
  6,064: the code saves 20% because five of the eight ops are duplicated
  either way.
* A detection requirement cannot be stated. `chialu/verify/harness.py:544`
  defaults the budget to `false_alarms == 0` and
  `single_bit_coverage == 1.0` and nothing constrains the alias rate,
  although `chialu/targets/rtl/alu_checker.py:1088` already models it.

## The `check` block

```yaml
    check:
      default:
        detect: none
      rules:
        - name: int_arith
          formats: [int16]
          ops: [add, sub, adc, sbb, neg, abs, mul_wide]
          detect: {random_alias: 5.0e-2, single_bit: 1.0}
          choices:
            - family: multi_residue
              moduli_count: [2, 3]
              moduli_set: low_cost_2a_minus_1
              comparator.family: [direct_compare, two_rail_tree]
            - family: rns_redundant
              base_moduli_count: 3
              redundant_moduli: [1, 2]

        - name: int_logic
          formats: [int16]
          ops: [and, or, xor, not, shl, shr_arith]
          detect: {random_alias: 0, single_bit: 1.0}

        - name: float
          formats: [fp16]
          ops: [fadd, fmul]
          choices:
            - family: reduced_precision
              replica_width_bits: 8
              bound_type: absolute
              replica_adder.family: [parallel_prefix, carry_select]
              replica_adder.topology: kogge_stone

      fallback: duplicate
```

A rule selects the (format, op) pairs its `formats` and `ops` name, and a
pair a later rule selects again takes the later rule. `default` covers
every pair no rule selects. `detect: none` leaves a pair unchecked.

### `choices` is a restriction of the checker space

A rule's `choices` is a list, one entry per candidate family. Each entry
carries that family's own pins and its slots' pins and nothing else, so
no pin is shared between two families and no pin has to be dropped for
the family that does not own it. The list is a restriction of
`checker_space()`: an entry narrows one family's domain, and a family
with no entry is excluded.

| declaration | domain |
| --- | --- |
| `choices` omitted | every family, every pin, filtered by `detect` |
| one entry, `family` alone | that family, every pin of it |
| one entry, every pin a scalar | one point |
| several entries | the union of their domains |

An entry is identified by its family, so a family appears at most once in
a rule's list.

Inside an entry, a pin takes the three forms the run file already uses
for `core.subword.family`: a scalar fixes it, a list is the set the
search chooses from, and an omitted pin opens the family's whole domain
for it. `"*": {search: all}` is not needed, since omission already means
that. A slot's pins come by their dotted path, so
`replica_adder.family: parallel_prefix` with `replica_adder.topology:
kogge_stone` names the adder the reduced-precision replica is built
from.

`checker_choices` at the top of `check:` sets the list every rule that
declares none inherits, which is how a unit that wants one candidate set
across all its ops writes it once.

### A family that covers part of a rule's ops

Three families cover one op class each: `parity_prediction_adder` and
`berger` cover the arithmetic class, `parity_prediction_multiplier`
covers the multiply class. Naming one as the family of a rule whose ops
go beyond that class means "this mechanism for its class, a replica for
the rest", which is a combination rather than a family.

That needs no new notation. The rule is the granularity: a rule whose
ops are the arithmetic class and whose entry names
`parity_prediction_adder` is exactly the mechanism, complete over its
own pairs. A rule whose ops go beyond the class gets the combination,
`fallback` decides whether the replica is allowed at all, and the check
manifest reports per (format, op) which mechanism covered it — so the
combination is visible rather than hidden, which was the only real
objection to it.

An earlier draft moved the three out of `choices` into entry keys,
`allow_parity_pred_add`, `allow_parity_pred_mul` and `allow_berger_add`.
That is dropped.

* For an op that is an adder or a multiplier, the keys said what a rule
  over that op class already says, so they were a second spelling of the
  same thing.
* For an op that contains an adder, `fadd` being twelve slots of which
  the keys cover two, they bought nothing: a replica cannot skip a block
  in the middle of a datapath, since it needs the significand sum to
  continue, so covering that adder by parity removes nothing from the
  replica's work. The keys pay there only when every slot of the op is
  covered and the replica is gone, which is the block-level document.
* `allow_parity_pred_mul` would never be set. Measured on nangate45 at
  int32 over a multiply-only unit, the parity prediction is 1.20 times
  the core's area against duplication's 1.03 and residue's 0.14, and its
  delay is 7,314 ps against the core's 2,020, so it is dominated on
  every axis and `chialu.checkers select` will not return it.

So the adder and multiplier inside a composite op have no notation in
this specification, and that is the correct state: they are the
block-level document's first question, not a key on a unit checker.

### The pins each family carries

| family | own pins | slots |
| --- | --- | --- |
| `residue` | `modulus` (3, 7, 15, 31, 63, 255), `generator_style` (csa_tree, modular_ripple, lut) | `comparator` |
| `inverse_residue` | `modulus` (3, 7, 15), `inverse_on` | `comparator` |
| `multi_residue` | `moduli_count` (2 to 4), `moduli_set` | `comparator` |
| `an_code` | `A` (3, 7, 15, 31) | `comparator`, `coded_adder` |
| `rns_redundant` | `base_moduli_count` (3 to 8), `redundant_moduli` (1 to 3) | none |
| `berger` | `construction` | `comparator`, `carry_replica` |
| `parity_prediction_adder` | `parity_groups`, `carry_scheme`, `interleaving` | `comparator`, `carry_replica` |
| `parity_prediction_multiplier` | `recoding` | `comparator`, `row_adder` |

The last three cover one op class each, so a rule that names one carries
the ops of that class or accepts the combination the section above
describes.
| `duplication` | `replication` (2 or 3) | `comparator`, which alone admits `majority_voter` |
| `reduced_precision` | `replica_width_bits` (4 to 24 by 4), `bound_type` | `replica_adder` |

`comparator.family` is `direct_compare`, `two_rail_tree`,
`m_out_of_n_checker` or, under `duplication`, `majority_voter`, with the
pins `tree_arity`, `code_class`, `realization` and `inputs`.
`coded_adder`, `carry_replica`, `row_adder` and `replica_adder` are
adder spaces: their `family` is any of the 15 adder families and their
pins are that family's.

`direct_compare` is the generator's default (`alu_checker.py:200`) and is
not a member of the two-rail space, so `feasible_families` has to add it
to the comparator's domain explicitly or the space has to gain it. The
second is the honest fix.

### How `detect` and `choices` meet

The declared domain is intersected with the feasible set, and the
intersection is what the search sees.

* An empty intersection fails the build and names the reason.
* An entry the requirement rejects in part is pruned in part: a
  `residue` entry whose `modulus` list holds one value that meets the
  bound and one that does not keeps the first.
* A fully pinned entry is checked rather than trusted, so a single entry
  whose point misses the rule's `detect` is a build failure rather than
  a silent acceptance.
* A rule with `choices` and no `detect` states no requirement, so the
  build reports the achieved numbers in the manifest and gates nothing.
  The `float` rule above is that case, since the reduced-precision
  replica leaves the bits below its resolution uncovered by design.

`detect` carries two independent quantities, because the existing model
reports two.

| key | meaning | model |
| --- | --- | --- |
| `random_alias` | the largest share of random multi-bit corruptions that may escape | `alias_probability` (`alu_checker.py:1088`) |
| `single_bit` | the share of one-bit corruptions that must alarm | `single_bit_floor` (`alu_checker.py:1136`) |

Which family and which pins meet a given bound is a question for the
model rather than for this document, because the answer moves whenever a
modulus set, a family or the model itself changes. `chialu.checkers`
answers it; the section below specifies that tool. Nothing in a run file
or in this document restates a number the tool computes.

`random_alias` names two quantities that are not interchangeable, and
what a rule asks for is the one that costs the most to answer. "What
`random_alias` means, and what it costs to answer" below defines both.

`fallback` decides what happens to a pair whose requirement stands but
whose chosen code does not cover it.

| value | effect |
| --- | --- |
| `duplicate` | the pair gets a replica of the datapath, which is today's unconditional behavior |
| `none` | the pair is left unchecked, which is legal only where the rule's `detect` is `none` |
| `error` | the build fails and names the pairs, so a run file cannot silently buy duplication |

## `chialu.checkers`: which parameters meet a bound

A new module, `chialu/checkers.py`, answers the question a rule's
`detect` asks, so a user narrows a `choices` list from a measured answer
rather than from a table.

```
python3 -m chialu.checkers select --formats int16,fp16 \
    --ops add,sub,adc,sbb,neg,abs,mul_wide \
    --random-alias 5e-2 --single-bit 1.0 [--fallback duplicate]
    [--families multi_residue,rns_redundant] [--pdk nangate45]
```

It walks every family and every point of every family's own choices,
computes `alias_probability` and `single_bit_floor` for the named
formats, keeps the points that meet both bounds and that cover the named
ops under the given fallback, and prints them sorted by the area the
synthesis database holds for that point.

```
family          pins                              random_alias  single_bit  area um2  delay ps
multi_residue   moduli_count=2                        ...          ...        ...       ...
multi_residue   moduli_count=3                        ...          ...        ...       ...
rns_redundant   base_moduli_count=3,redundant=1       ...          ...        ...       ...
[chialu.checkers] 4 of 37 points meet the bound; 12 rejected on the alias,
                  9 on the single-bit floor, 12 on op coverage
```

Three further subcommands:

* `explain --family residue --modulus 7 --formats int16` prints the two
  numbers for one point and the reason a bound rejects it, so a rejected
  choice is diagnosable.
* `floor --formats int16` prints the lowest `random_alias` each family
  reaches over its own domain, which is what a user consults before
  setting a bound they cannot meet.
* `emit --...` prints the surviving points as a `choices` block ready to
  paste into a run file, optionally capped at the cheapest N.

The area and delay columns come from `chialu.synthdb`, so `checkers`
answers "which of these is cheapest" only once the checker is a kind of
the database. Until then the columns are empty and the ordering is by
the alias rate. Adding the checker to the database is a prerequisite of
this tool being useful rather than merely correct.

`feasible_families` is the library function behind `select`, and the
build calls the same function, so a run file cannot be admitted by a
rule the tool would have rejected.

## Block-level checking is a different axis, and it is not this one

An earlier draft gave a `choices` entry a `placement` of `unit` or
`block`. It is dropped. Every family of `checker_space()` is a
unit-level mechanism, and naming one of them cannot describe a
block-level scheme.

### The checker space describes a unit, not a block

A family of the checker space answers one question: given the unit's
inputs and its data output, how is the output shown to be right. That is
why `CODED_OPS` (`alu_checker.py:156`) is keyed by op rather than by
structure, and why `parity_prediction_adder` and
`parity_prediction_multiplier` are named after the op class each covers
rather than after a structure. Their prediction needs a carry vector or
a partial-product reduction that the core does not expose, and since the
checker may not reach inside the core, each carries a slot
(`carry_replica`, `row_adder`) and builds its own. Those slots exist
because the family is unit-level; they are the mark of it.

### Naming one family cannot describe a block-level scheme

`fadd` is where this breaks. A single-path float adder is twelve slots:
a significand adder, an exponent adder, an alignment shifter with its
trailing-zero counter, a normalization shifter, a leading-zero path with
its encoder, and the rounder. A family that covers the adder says
nothing about the other ten. There is no
`parity_prediction_shifter` and no `parity_prediction_normalizer` in the
space, and there is no reason there should be: a shifter's check is not
a family of the same kind as an ALU's check.

A block-level scheme therefore needs two things this specification does
not have.

* A checker per structure kind, declared where the structure is
  declared. The natural spelling is a slot pin, `core.sig_adder.check.*`
  beside `core.sig_adder.family`, so a structure carries its own check
  the way it carries its own family.
* A statement of which code survives each structure kind and what the
  structure must expose for it to. A residue survives a shift when the
  shifted-out bits are given, a rounder's truncation when the dropped
  bits are given, and nothing at all through a bitwise op or a
  comparison. That is a design per structure kind, not a pin on an ALU's
  checker.

Until both exist, `placement: block` would be a key a run file could
write and the generator could not honor.

### What this specification does instead

Every entry of `choices` is a unit-level checker. The rule table, the
detection requirement, `chialu.checkers`, the manifest and the fault
campaign all stand as specified; only the `placement` and `compare` keys
are gone, and with them the block sections of the staging.

Block-level checking is worth a document of its own. Its first question
is not which family to name but which structure kinds can carry a code
at all, which the analysis in this repository's history answers for the
integer structures and not for the float ones.

### Comparing at every block is a non-goal

The same draft gave an entry `compare: end | per_block`. It is dropped
for a reason that survives the rest of this section, so it is recorded
here: the contract asks whether the final result is wrong.

* The only thing `per_block` buys is naming the block a fault came from,
  and that needs one alarm bit per block at the module's boundary. Or-ed
  into the one `check_err` the interface carries, N comparators say
  exactly what one comparator says.
* A fault the blocks after it mask leaves the result correct, and
  `chialu/verify/faults.py` already does not count a mask that leaves
  the output unchanged. So catching such a fault early is not coverage
  under the contract, and raising `check_err` for it is a false alarm.
* For a replica it costs the replica's independence. The replica is flat
  behavioral text today (`alu_ref_module(..., hierarchical=False)`);
  comparing at block boundaries needs it to expose the same intermediate
  values the core does, so it has to be structured like the core, share
  its place and route, and become likelier to fail the same way.

The one argument this does not answer is timing: a comparison at the end
sits after the last block, and per-block comparisons do not. If that
ever matters, it belongs to the block-level document above, with the
alarm bits in the interface.

## What `random_alias` means, and what it costs to answer

Two quantities live under one name today, and the specification has to
separate them.

| quantity | definition | what it depends on |
| --- | --- | --- |
| `output_alias` | the code misses a corruption of the word it checks, the corruption drawn uniformly over that word | the code and the word's width |
| `escape` | a fault at a node inside the datapath reaches the unit's output and raises no alarm | the fault's site, every structure between that site and the output, and the code |

`alias_probability` (`alu_checker.py:1088`) computes `output_alias`. The
fault campaign measures `output_alias` as well, because
`chialu/verify/faults.py` XORs its masks onto the core's data output and
says so: "Internal nodes are never referenced." The model and the
measurement therefore agree with each other and neither is `escape`.

A rule's `detect` asks about `escape`, because a run file cares whether
a fault in the unit reaches the output unnoticed, not whether a code
would have caught a corruption nobody's datapath produces.

### An exact compare needs no composition

`duplication` recomputes the result and compares bit for bit;
`an_code` compares an AN-coded replica and its divisibility by A. A
compare with no blind spot alarms on every corruption whatever its
distribution, so `escape` is zero for a fault in the core and the
residual risk is a fault in the checker itself and a common-mode fault
between the core and the replica. Nothing has to be composed, and
nothing has to be simulated.

This is the other half of why duplication is the baseline every cheaper
checker is measured against: it is not only the coverage ceiling, it is
the only mechanism whose coverage is knowable without simulating the
core.

### Every coded compare needs a composition over the core's structure

A checker predicts the output's code from the inputs and compares. A
fault at a node in layer k reaches it only as the corruption it has
become at the unit's output, after every layer above k has transformed
it. Computing `escape` needs, for each fault site, the map from that
site to the output — which is the core's structure, and the core's
structure is what the search is varying.

The consequences are four.

* `escape` is not a property of the checker. Two run files with the same
  checker and different `core.*` families have different `escape`.
* The corruption reaching the output is not uniform, so `output_alias`
  is not a bound on `escape` in either direction. A code has structured
  blind spots, and a datapath produces structured corruptions, and
  whether they meet is the whole question.
* A residue code shows this exactly. A carry chain turns a fault into a
  burst, so the output corruption is `2^k * (2^j - 1)` for a burst of
  length j starting at bit k. For a modulus `2^a - 1` that is congruent
  to zero precisely when `a` divides `j`, since the modulus divides
  `2^j - 1` only then. So the escaping bursts are the ones whose length
  is a multiple of `a`, and their share is about `1/a` rather than
  `1/(2^a - 1)`. Over the 16-bit bursts and modulus 31 the escape rate
  is 0.154 where `output_alias` is 0.032, and over modulus 255 it is
  0.074 where `output_alias` is 0.004.
* Which bursts a datapath produces is a core family choice. A
  ripple-carry adder's fault becomes a long burst; a prefix adder's
  becomes a different pattern under a different distribution. So the
  checker that meets a bound depends on the adder the search picked,
  which is a coupling the current model does not have and this
  specification must not pretend away.

`reduced_precision` sits between the two: its compare is within a bound,
so a corruption below the replica's resolution escapes wherever it came
from, and the composition runs over the bit positions a fault reaches
rather than over a code's blind spots.

### How the specification handles it

* The static model is a necessary condition and nothing more.
  `chialu.checkers select` prunes the points whose `output_alias`
  already exceeds the bound, since a code that misses a uniform
  corruption at a rate above the bound cannot meet the bound against any
  distribution that includes it. It never admits a point: it reports the
  survivors as candidates.
* The sufficient check is fault injection at internal nodes. That is a
  change to `chialu/verify/faults.py`, which injects at the output seam
  today, and it is the reason the per-group fault measurement is a stage
  of its own rather than a detail of the manifest.
* The check manifest carries which quantity each row's number is, under
  the keys `output_alias` and `escape`, and `escape` is absent until an
  internal-node campaign has produced it. A row with `output_alias`
  alone is a prediction; a row with `escape` is a measurement.
* An exact-compare entry is the exception: its `escape` is zero by
  construction and the manifest says so without a campaign.

This is the part of the specification most likely to be wrong in detail,
because the composition over a datapath's layers is the standard hard
problem of concurrent error detection and the literature reports it per
design rather than in closed form. The specification's position is that
the model prunes and the campaign decides, so a wrong model costs search
time rather than a false claim of coverage.

## The variables ADIR sees

A rule's `choices` is a space, so it expands the way a space does: one
categorical variable naming the entry, and the entry's pins live only
under it.

```
check.int_arith.family                   search [multi_residue, rns_redundant]
check.int_arith.multi_residue.moduli_count       search [2, 3]
check.int_arith.multi_residue.moduli_set         fixed low_cost_2a_minus_1
check.int_arith.multi_residue.comparator.family  search [direct_compare, two_rail_tree]
check.int_arith.rns_redundant.base_moduli_count  fixed 3
check.int_arith.rns_redundant.redundant_moduli   search [1, 2]
check.float.family                       fixed reduced_precision
check.float.reduced_precision.replica_width_bits fixed 8
check.float.reduced_precision.replica_adder.family   search [parallel_prefix, carry_select]
check.float.reduced_precision.replica_adder.topology fixed kogge_stone
```

The family name sits between the rule and the pin, so two entries never
collide and no pin has to be reinterpreted per family. The nesting
matches what the spaces already do, where a family's choices are live
only when that family is bound, so the search needs nothing new.

## The piece that has to be written

`feasible_families(pairs, requirement, fallback, declared) -> list[dict]`
in `chialu/targets/rtl/alu_checker.py`, where `declared` is the rule's
own declarations. It walks the families the declaration admits and, for
each, the pin combinations the declaration admits, and asks three
questions:

1. does `CODED_OPS[family]` (`alu_checker.py:156`) cover the rule's ops,
   and where it does not, does `fallback` allow a replica?
2. is `alias_probability(...)` at most `detect.random_alias` over the
   rule's formats?
3. is `single_bit_floor(...)` at least `detect.single_bit`?
Question 2 prunes rather than admits. It drops a point whose
`output_alias` already exceeds the bound and passes the rest through as
candidates, because `escape` at the unit's output is not a function of
the checker alone. An exact-compare family is the exception: its
`escape` is zero by construction, so question 2 admits it outright.

The answer is the rule's variable domains. Everything it needs already
exists; what is new is asking the questions in this order, intersecting
with what the run file declared, and returning a set rather than
validating one choice. A slot pin does not enter the questions, because
neither model depends on which adder the carry replica is built from: a
slot's domain passes through to the search untouched, and the search
separates the slot choices on area and delay alone.

## The check manifest

The build writes `check_manifest.json` beside the structure manifest,
one row per (format, op):

```json
{"format": "...", "op": "...", "rule": "...",
 "mechanism": "code", "family": "...", "pins": {},
 "output_alias": 0.0, "single_bit": 0.0}
{"format": "...", "op": "...", "rule": "...",
 "mechanism": "replica", "family": "...", "escape": 0.0}
{"format": "...", "op": "...", "rule": "default", "mechanism": "unchecked"}
```

The numbers are the model's, written at build time rather than quoted
anywhere, and `output_alias` and `escape` are separate keys because one
is a prediction and the other a measurement. This is what makes the cost
of a checker readable: which ops the code actually covers, which fell
back to a replica, and which are not checked at all. Today that division
exists in `coded_pairs` (`alu_checker.py:404`) and is never reported.

## The generator

`chialu/targets/rtl/alu_checker.py` builds one code plus one replica.
Under this specification it builds one code per rule group plus one
replica for the pairs no group's code covers.

* `coded_pairs` becomes `{group: pairs}`.
* One code path per group that needs one: a residue generator per
  modulus and width, a parity path, a Berger counter.
* `alu_ref_module(spec, skip=...)` (`alu_seed.py:775`) takes the union
  of every group's coded pairs and every unchecked pair, so an unchecked
  op costs nothing at all, which `check_en: false` cannot express today
  except by dropping the checker entirely.
* `check_err` is the disjunction of the groups' verdicts. A per-group
  error bus is optional and costs one bit per group.

## The fault campaign

`chialu/verify/faults.py` injects an XOR mask on the core's data output
and reports `false_alarms`, `single_bit_coverage` and `random_alias` for
the unit as a whole. The requirement is per group, so the measurement
has to be too.

* `FaultPlan` partitions its masks by the vector's (mode, op), the way
  `harness.py:548` already partitions by accuracy mode.
* The injection moves from the output seam to the core's internal
  nodes, because the seam measures `output_alias` and the rule asks for
  `escape`. This is the change that makes the measurement answer the
  question the run file asked, and it is why the campaign is a stage
  rather than a detail.
* `FaultReport.summary` reports the three rates per group.
* `DetectBudget` compares each group against its own rule rather than
  against one unit-wide bound.

The loop then closes: the run file declares the requirement, the
feasibility model predicts, the fault campaign measures, and a
disagreement between the prediction and the measurement is a defect in
the model rather than a tuning knob.

## Staging

1. `chialu.checkers` and `feasible_families`, against the model as it
   stands. Nothing in the run file changes, and the tool alone says what
   meets a bound.
2. The checker as a kind of the synthesis database, so `select` can
   order its answer by area and delay. Without this the tool is correct
   and not yet useful.
3. The rule table, one family per rule group chosen by the search,
   `fallback` honored, and the check manifest.
4. The fault campaign injecting at internal nodes and partitioning per
   rule group, so the requirement the run file declares is the one
   measured.

Each stage keeps the run files loading and the ALU matrix passing.
Block-level checking is not a stage of this work; it is the separate
document the section above describes.

## What this makes expressible, and what it exposes

Expressible: check the multiply and not the bitwise ops; hold one format
to a loose bound and another to no aliasing at all; let the search find
the cheapest family that reaches a bound; and forbid duplication.

Exposed, and this is a property of the codes rather than of the
specification: with `fallback: error`, only `targets/approx_alu.yaml` has
an op set a single code covers, which is `add`, `mul` and `mul_wide`. The
other five ALU targets carry at least one op no separable code predicts.
`fp_alu` has `fmin`, `fmax` and `fcmp`; `int_subword_alu` has the whole
logic class; `mixed_cvt_alu` and `posit_alu` have `min` and the
conversions. Each of those either gives the pair `detect: none` or
accepts a replica, and the specification's value is that the run file
says which.
