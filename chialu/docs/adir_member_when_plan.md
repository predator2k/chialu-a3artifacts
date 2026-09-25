# Member-level `when` in ADIR: a member admissible under a sibling's value

A member condition makes one member of an Enum choice admissible only
while another variable of the same instance holds one of a named set of
values. The other variable is not the member's parent; it is a sibling
choice of the same family, a choice of another slot at the same structure
index, or a static variable, and it may itself be searched. The member
stays in the domain, the prompt shows it with its condition, and every
place ADIR reads a value narrows the domain to the members the decided
values admit. Three rules of `chialu/behavior_rules.py` were `deferred`
because they needed this; two of them become active rules under this
change, and the third stays deferred with the reasoning below.

## The representation

The condition lives on the `Variable`, as `member_when`:

```python
Variable("core.unpacker.*.denormal_handling", Enum(("in_unpack", "in_datapath")),
         when=("core.unpacker.*.family", (...)), indexed_by="structures:unpacker",
         member_when={"in_datapath": ("core.fp_fma.*.family",
                                      ("classic_fma", "reduced_latency_fma", "multipath_fma"),
                                      "a separate multiplier folds the product bits below the X "
                                      "and needs normalized significands from the unpacker")})
```

* `member_when` maps a member to `(variable, allowed_values)` or
  `(variable, allowed_values, doc)`. `__post_init__` normalizes the entry
  to a three-tuple with the values as a tuple.
* The named variable is written as a template name. `Variable.expand`
  substitutes the index into a `*` of that name, as it does for `when`,
  so `core.unpacker.m1.denormal_handling` is conditioned on
  `core.fp_fma.m1.family`.
* A member named in `member_when` must be a member of the variable's
  domain, and at least one member of the domain, and of every
  `index_domains` entry, must be unconditioned. A variable whose every
  member depends on the same condition is an existence condition, which
  `when` already expresses, and the tree refuses the `member_when` form.
  This keeps two facts: a member condition never empties a domain, and a
  default always exists.
* One condition per member. A member that would need two conditions, or
  a disjunction, is out of scope and stays a render-time check.

The alternatives rejected:

| alternative | why not |
| --- | --- |
| on the `Enum` domain (`Enum.member_when`) | a domain is a value object without a namespace; `_union` compares domains across families, `narrow` builds new Enums for `search: [...]`, and `Bool` has no such field, so the condition would be lost or duplicated at each of those points |
| a registry-only rule kind that ADIR never sees | the loader, the declaration check, the composer and the numeric backends read values in ADIR; a rule ADIR cannot see leaves the render-time raise as the only check, which is the deferred state |
| a variable-level `when` per member (one variable per member) | it changes the variable's identity and the declaration's `VAR` lines; the agent declares a member, not a variable |

## Where a value is read, and what the sibling's state means

Every read goes through one helper, `adir.variables.member_exclusions(var,
domain, lookup)`, which returns `{member: reason}` for the members of
`domain` that the conditions exclude. `lookup(name)` reports the sibling's
state as `(time, value)`:

| the sibling's state | the conditioned member is |
| --- | --- |
| `fixed` to `v` | admissible iff `v` is in the allowed values |
| `runtime` over provisioned members | admissible iff every provisioned member is allowed, since the member is built once and serves every run-time selection |
| `search`, decided to `v` (declared, or defaulted where the read has defaults) | admissible iff `v` is allowed |
| `search`, undecided (`OPEN`) | admissible; the search may still choose an allowed sibling value |
| absent (inactive under its parent, or the expanded name resolves to no variable) | inadmissible, as a child of an absent parent is inactive under `when`; the reason names the absence |

The reason text is ADIR's: `'in_datapath' is admissible when
core.fp_fma.m0.family is one of [classic_fma, reduced_latency_fma,
multipath_fma]; it is separate_multiplier_and_adder (a separate multiplier
folds ...)`. The domain library's `doc` follows in parentheses.

The four evaluation points:

| where | the sibling's `search` state | what changes |
| --- | --- | --- |
| `bind_variables`, `bind_one` (a fixed or runtime binding of the conditioned variable) | undecided | a fixed value or a provisioned member the conditions exclude is a `BindError` naming the condition and the sibling's value; a `search` binding is never checked here, since its members are decided per candidate |
| `Bindings._descend`, `_defaults_under` (which children the defaults open) | decided to its declared value, else to its own default under the same rule, recursively | `default_view(b)` becomes `Bindings.default_of(name, values)`: the first admissible member of the search domain |
| `check_declaration` (the VAR lines, in `variable_order`) | decided to the declared value, else to the default computed earlier in the same pass; a sibling the pass skipped as inactive or rejected is absent | a declared conditioned member is rejected with the condition; an undeclared variable takes the first admissible member, and `outputs["defaulted_under"]` records every variable whose default moved off the domain's first member, with the sibling and its value; a fixed conditioned variable whose member the declaration's values exclude is a problem too, naming the sibling to change |
| `families_of` (chiALU's seed values) | decided to the override, the fixed value, or the default | no registered rule conditions a domain's first member, so `value_of`'s `b.domain.default()` is correct today; the general form is `adir.variables.default_under(var, b.domain, lookup)` with `lookup` over `value_of`, which is a one-line change in `chialu/modules/generators.py` and is left to that file's owner |

Ordering: `_topological` visits a variable after its `when` parent and
after every `member_when` sibling, so `variable_order`, the declaration
check, the seed walk and `space_json` see a sibling before the member it
conditions. `VariableTree.__init__` runs the sort over the templates and
raises `a cycle of conditions` on a cycle, and it rejects a sibling
template the tree does not hold, a static variable conditioned on an
indexed sibling, and an all-members condition. `Bindings.materialize`
materializes the siblings before `bind_one`, as it does the parent.

## Defaults

The default of a conditioned variable under decided values is the first
admissible member of the search domain, in domain order; deterministic
because the order is the domain's and the values are the declaration's.
The default of the domain itself (`Domain.default()`, the loader's view
before any value is decided) is unchanged, so a run file's fixed defaults
and `space_hash` do not move. A default that moves is reported in
`check_declaration`'s `defaulted_under` output and counted in its
`detail`; the composer's operator section marks a member the parent's
values exclude.

## The prompt

* The decisions section's introduction states that a member listed with
  a condition is admissible only under the named value of the other
  variable, and that a `VAR` line naming it otherwise is rejected.
* A root decision lists a conditioned member as `` in_datapath (when
  `core.fp_fma.*.family` is one of [classic_fma, ...]) `` in every
  depth that lists members.
* The `structural` operator section lists the parent's active decisions
  with their members; a conditioned member carries its condition, and
  one the parent's decided values exclude carries `` (not under the
  parent's `core.fp_fma.m0.family`=separate_multiplier_and_adder) ``.
* `unexplored_values` names a conditioned member with its condition.
* A nested choice (a choice whose `when` names a sibling choice, see the
  `nested` rule kind below) is listed under its family with `` (under
  string_form=dual_pos_neg_strings) ``.
* A rejected `VAR` line reads `VAR core.unpacker.m0.denormal_handling=
  in_datapath: 'in_datapath' is admissible when core.fp_fma.m0.family is
  one of [...]; it is separate_multiplier_and_adder (...)`.

## The search

An LLM backend proposes through the prompt and the declaration check
rejects a violation, so the prompt text above is its guard. The numeric
backends propose values themselves:

* `sample_declaration` samples a conditioned variable among the members
  the already-sampled values admit (parents and siblings come first in
  `variable_order`).
* `_prune`, which every backend applies to a full assignment, repairs a
  member the assignment's other values exclude to the first admissible
  member, so a grid point, a SMAC configuration and an NSGA-II
  individual never reach the evaluator with an inadmissible member.
* `_smac` adds a `ForbiddenAndConjunction` of `ForbiddenEqualsClause`
  (the member) and `ForbiddenInClause` (the sibling's disallowed
  members) where both variables are searched, so SMAC's own sampler
  respects the condition.
* `space_json` exports the conditions under `forbiddens` in that shape,
  so a reader of `space.json` sees them.

## The hash

`space_hash` covers `member_when` through the template entry: a template
with conditions appends `{"member_when": {member: [sibling, allowed]}}`,
and one without appends nothing, so an instance without conditions keeps
its hash. The `doc` is not part of the identity. A conditioned member is
in the domain, so `Enum.excluded` and `index_domains` are unchanged by a
condition, and a member both statically excluded at one index and
conditioned at another is handled per index: `member_exclusions` reports
a member only where the index's domain contains it.

## The registry: a rule with a sibling condition

* `Predicate` gains `sibling=(path, values)`. Its `holds` stays `None`,
  since the contract cannot evaluate it; the prune lowers it into
  `member_when`. `path` is `<slot>.<choice>` relative to the unit
  (`fp_fma.family`, `fp_adder.operand_order`), or a bare choice name for a
  choice of the same family (`string_form`). `values` is a tuple or a
  callable returning one, evaluated at lowering.
* `Rule` gains `under`: contract predicates under which the rule applies.
  Where one fails the rule is inert and the member is admitted without a
  condition. The rule on `in_datapath` applies under `x_form_tight`.
* `prune_slot` lowers a member rule whose predicate has a sibling into
  `member_when` on the compiled variable. A union variable takes the
  condition only where every declaring family agrees on it; a family that
  admits the member unconditionally keeps it unconditioned and the report
  names the disagreement, as for exclusions.
* A choice-level rule (`family|choice|*`) with a bare sibling path is the
  kind `nested`: the choice is a decision under the sibling choice's
  member alone. The prune lowers it into the variable's `when`,
  `(sibling, allowed)`, after checking that the sibling variable exists in
  the slot with the same `when` as the choice, so the family condition
  holds transitively. This is the form for `split_string_select`, which
  `families/fp.py:add_sv` reads only for the dual strings.
* `chialu.ALU.elaborate` and `chialu.VecDotAcc.elaborate` finish with
  `BR.bind_member_conditions(variables, report)`, which resolves each
  condition's sibling against every compiled template. A sibling template
  the unit does not compile (a unit with no `fp_fma` slot) turns the
  condition into a static exclusion with the same reason, since an absent
  sibling fails the condition.
* `Report` gains `conditions` (variable, member, sibling, allowed, reason,
  rule), `to_json` gains `conditioned`, `prompt_text` states each
  condition once, and `python3 -m chialu.behavior_rules report` prints
  them.
* The lint checks that a sibling path resolves to a choice of a space the
  library defines, that a `nested` rule has a bare sibling path and the
  member `*`, that a rule whose predicates are all evaluable or
  sibling-bound is not `deferred`, and that a `deferred` rule names a
  predicate that is neither.

## The three rules

| rule | resolution |
| --- | --- |
| `*\|denormal_handling\|in_datapath` in the unpacker under `x_form: guard_round_sticky` | active: `requires=("fp_fma_fused_in_mode",)`, `under=("x_form_tight",)`; the sibling is `fp_fma.family` and the allowed values are every family of `fp_fma_space` other than `separate_multiplier_and_adder`, computed at lowering so a fused family a parallel branch adds is admitted; a mode without an `fp_fma` structure (a float mode with `fcmp` alone) has an absent sibling and loses the member, as `alu_mode.tight_x` raises there |
| `lza\|string_form\|dual_pos_neg_strings` in `fp_adder.lz` and `fp_adder.near_lz` | active: the sibling is `fp_adder.operand_order`, allowed `shift_each_operand` |
| `lza\|split_string_select\|*` | `nested` under `string_form = dual_pos_neg_strings`: the choice is inert under a single string (`add_sv` selects between two strings alone), and the dual strings are admissible under `shift_each_operand` alone, so the chain gives the deferred rule's intent without a rule that would empty the domain under `swap_before_shift` |
| the equal pins of `shared_across_formats` across the modes that select it (rounder, unpacker, and `sharing` on the fp_fma families) | stays deferred, registered as `deferred` rules naming `pins_equal_across_sharing_modes` so the lint counts them |

The reasoning on the third: the constraint is `pins(m_i) == pins(m_j)`
for every pair of modes that select the sharing. A member condition fixes
one allowed set per member, while equality allows, for each member `v` of
`m1`'s pin, the set `{v}` of `m0`'s pin, and only while both families are
`shared_across_formats`, which is a conjunction over three variables. The
feature that fits is an alias: the modes that select the sharing declare
one set of variables, which is what the sharing physically is (one
datapath). chiALU's `normalize_declaration` already aliases a group's
members (a STRUCTURE `group=`), and the seed builds the shared rounder and
unpacker from the first selected mode's pins, so the alias belongs there
or in ADIR's declaration normalization, and the render-time check in
`alu_seed.py` ("requires compatible pins on its one physical datapath")
stays the defense. That file is edited by a parallel branch, so the alias
is left to it.

## Tests

ADIR (`third_party/adir/tests/test_member_when.py`, over a second toy
template `toy.Cond` and `tests/toy_cond.yaml`):

* a fixed conditioned member binds under an allowed fixed sibling, errors
  under a disallowed one naming the sibling and its value, and binds
  under a searched sibling;
* a runtime sibling admits the member only where every provisioned
  member is allowed;
* `check_declaration` rejects the member under the sibling's declared
  value and under its default, accepts it under an allowed declared
  value, and reports a default that moves in `defaulted_under`;
* a nested choice is active under the sibling's member alone, and a
  `VAR` on it otherwise reads `declared, but inactive`;
* an indexed member is conditioned on the sibling at its own index, and
  an index whose sibling does not exist loses the member with the
  absence in the reason;
* the tree rejects a cycle, an unknown sibling, a static variable
  conditioned on an indexed sibling, and an all-members condition;
* `space_hash` differs with and without a condition, and the template
  identity of an unconditioned variable keeps its four fields;
* `space_json` carries the condition under `forbiddens`;
* the prompt lists the member with its condition, the operator section
  marks a member the parent's values exclude, and `unexplored_values`
  names the condition;
* `sample_declaration` never proposes the member under a disallowed
  sibling, and `_prune` repairs one.

chiALU (`chialu/verify/behavior_rules_selftest.py`, added cases):

* the elaboration at `x_form: guard_round_sticky` conditions
  `core.unpacker.*.denormal_handling`'s `in_datapath` on
  `core.fp_fma.*.family` and leaves it unconditioned at `exact`;
* a declaration with `in_datapath` under the default
  `separate_multiplier_and_adder` is rejected naming
  `core.fp_fma.m0.family`; forced through the seed it raises in
  `tight_x`; with `classic_fma` it is accepted and the fp16 seed
  conforms on 64 vectors at the tight X;
* `core.fp_adder.*.lz.string_form`'s `dual_pos_neg_strings` is
  conditioned on `core.fp_adder.*.operand_order`; a declaration under
  `swap_before_shift` is rejected naming it; forced it raises in
  `add_sv`; under `shift_each_operand` it is accepted and the seed
  conforms;
* `split_string_select`'s `when` is the string form, and a `VAR` on it
  under a single string is inactive;
* the deferred list names the sharing rule alone, and the lint is clean.

## Results (2026-09-18, on the development machine)

ADIR (`third_party/adir`, branch `member-when`):

* `python3 -m pytest tests -q`: 34 tests pass before the change and 49
  after; the 15 new ones are `tests/test_member_when.py`.
* The change touches `variables.py`, `declaration.py`, `instance.py`,
  `composer.py`, `prompts.py`, `backends/numeric.py`, `docs/design.md`
  and the tests; `domains.py` and `spaces.py` are unchanged, since the
  condition lives on the variable.

chiALU (branch `member-when`, the submodule pointer on ADIR's commit):

* `python3 -m chialu.behavior_rules lint`: 198 families (141 neutral,
  5 conditional, 52 selector), 54 rules (8 retired, 3 on a sibling,
  3 deferred), 0 unregistered, 0 stale; exit 0.
* `python3 -m chialu.archdocs`: 0 undescribed members, 0 unmet claims;
  exit 0.
* Every run file under `targets/` and `targets/eval/` loads, its seeds
  render and its core RTL assembles: 26 of 26. The float units carry
  2 member conditions (`lz` and `near_lz` `string_form`) and 2 nested
  choices; the FPnew and HardFloat bindings fix `in_datapath` under a
  fixed `classic_fma`, which the loader admits; no run file reports a
  condition it could not lower.
* `fp_alu_cmp_fpnew.yaml` loads in 21.0 s.
* `python3 -m chialu.verify.<name>_selftest`: family_space 14 s,
  check_rules 3 s, float_seed 3 s, fp_cpa 5 s, alu_fidelity 47 s,
  module_collector 6 s, mode_ops 1 s, exponent_rounder 54 s,
  dot_structural 6 s, formats 2 s; every one exits 0.
* `python3 -m chialu.verify.behavior_rules_selftest` passes in 21 s with
  the two new cases:
  * `in_datapath` under the tight X: conditioned on
    `core.fp_fma.*.family`; the VAR line under the default
    `separate_multiplier_and_adder` is rejected naming
    `core.fp_fma.m0.family`; forced through the seed it raises in
    `tight_x`; with `classic_fma` it is accepted and the fp16 seed
    conforms on 64 vectors; a unit with `fcmp` alone loses the member
    statically with `the unit has no core.fp_fma.*.family`.
  * `dual_pos_neg_strings`: conditioned on `core.fp_adder.*.operand_order`
    in `lz` and `near_lz`; rejected under `swap_before_shift` naming it;
    forced it raises in `add_sv`; under `shift_each_operand` accepted
    and conforming; `split_string_select` is inactive under a single
    string and defaults to `true_sign` under the dual strings.
* Conformance through `adir.registry.underlying(chialu.eda.conformance)`:
  `fp_alu_cmp` bit-exact (6.3 s after a 20.7 s load), `fp_alu_cmp_fpnew`
  bit-exact (3.6 s after 21.0 s), `fp_alu_cmp_hardfloat` bit-exact (4.4 s
  after 20.6 s).
* The prompt over `targets/fp_alu.yaml` (the exact X) lists
  `split_string_select (2, under string_form=dual_pos_neg_strings)`
  under `lza` and no condition on `denormal_handling`, since the rule
  is inert at the exact X; no run file with searched slots binds the
  tight X, so the tight-X rendering is covered by the ADIR tests alone.

What stays open:

* The pin equality of `shared_across_formats`, as three `deferred` rules
  (above).
* `families_of.value_of` takes a conditioned variable's default from
  `b.domain.default()`; no registered rule conditions a domain's first
  member, so the seed's values are unchanged, and the one-line change to
  `adir.variables.default_under` belongs to `chialu/modules/generators.py`.
* A fixed conditioned member does not narrow a searched sibling's domain
  at load (the FPnew binding's fixed `in_datapath` would not remove
  `separate_multiplier_and_adder` from a searched `core.fp_fma.m0.family`);
  the declaration check rejects the incompatible declaration naming the
  fixed member and the sibling.
* One condition per member; a disjunction (`indicator_restriction:
  positive_result_only` under the swapped datapath or the dual strings)
  stays a render-time check.
