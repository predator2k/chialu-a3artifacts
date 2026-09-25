# The behavior checkers: every candidate a slot offers computes the contract

Two mechanisms keep the design-space search inside the behavior the YAML
specifies. `plan_behav_checker` removes, at elaboration, every family and
every enum member whose realization would change the packed result, the
flags or the specials `chialu/verify/alu_ref.py` defines under the bound
options, so the coding agent never sees such a candidate in a slot's
menu. `yaml_behav_checker` checks the YAML itself at load, so a fixed
microarchitecture binding cannot contradict the specified behavior. Both
read one registry, `chialu/behavior_rules.py`, whose entries are one-line
registrations that a family carries with it.

"Behavior" is the conformance criterion and nothing wider: the packed
result, the flags and the special values per `alu_ref` (and `dot_ref` for
the dot class) under the bound options. A rule is a claim about that
criterion. Conformance stays the last gate.

## Where each mechanism runs

| mechanism | where | what it reads | what it produces |
| --- | --- | --- | --- |
| `plan_behav_checker` | `chialu.ALU.elaborate` and `chialu.VecDotAcc.elaborate`, after the slot spaces compile to variables and before the artifacts render | the normalized spec, the slot's `Space`, the compiled variables, the structure index sets | narrowed domains (a removed member carries its reason), per-index domains where a rule differs across the modes of one slot, a fixed-only search domain for a selector numeric, `Elaboration.info["behavior_rules"]` for the prompt and `info["behavior_report"]` for the elaboration report |
| `yaml_behav_checker`, option half | the same `elaborate`, before the spaces compile | the unit options alone (`OPTION_RULES`) | a `BindError` in the YAML's terms (`x_form: guard_round_sticky needs no cvt op in a float mode; mode 1 (fp16) has cvt(int8)`) |
| `yaml_behav_checker`, binding half | ADIR's binding of the run file's `fixed` core variables, `chialu/plans.py:plan_vars` for a plan's family and pins, and ADIR's `check_declaration` for the agent's VAR lines | the narrowed domains the prune produced | the rule's reason appended to the rejection (`fixed: 'as_stored' outside enum['pseudo_normalized_wide_exponent']: subnormal_representation as_stored needs no SR in rounding; the unit provisions [RNE, SR]`) rather than "outside domain" alone |

The split of the two halves follows the binding time. A searched variable
is the prune's: the menu shrinks and the default is re-derived. A fixed
variable is the checker's: the option rules see the unit options
directly, and a fixed core binding, a plan pin or a declared VAR is
checked against the pruned domain, whose removed members carry the rule
that removed them. One rule table serves both, since the prune writes the
rule's reason into the domain and every rejection path reads it back.

## The registry

`chialu/behavior_rules.py` holds four tables and the evaluation over a
bound spec.

### The classification on `Family`

`adir.spaces.Family` gains three fields:

| field | meaning |
| --- | --- |
| `behavior` | `neutral`, `conditional` or `selector`; the empty default means unregistered |
| `requires` | the predicate names a `conditional` family needs, every one of which must hold |
| `evidence` | where the neutrality under the condition is shown (an fptest variant, a selftest, a render-time check that states the same fact) |

The three values:

* `neutral`: every member of every choice computes the contract under any
  bound options. The claim is stated explicitly; a default-free family is
  unregistered and excluded.
* `conditional`: the family computes the contract when its `requires`
  hold; the prune removes it where they do not.
* `selector`: the family selects the computed function (an approximate
  adder, a truncated multiplier, a block accumulation with a shared
  exponent, an SFU evaluator); it belongs to an approximate unit's space
  alone (a dot unit's under the explicit architecture contract).
  `selector` absorbs `algorithm_level`: a family that sets
  `algorithm_level=True` is a selector. The prune removes a selector from
  an exact unit's family enums with its reason, which replaces the former
  `exact_only` pass that dropped the families from the spaces before
  they compiled; a declaration naming one is now rejected with the
  reason rather than with "outside domain". `algorithm_level` keeps its
  narrower meaning for `chialu/sfu_accuracy.py`, which recomputes a
  pinned reference under it, so a selector need not set it.

A member inherits its family's classification. A registry rule narrows
one member, one choice or one family further.

### The predicate table

Every condition is a named predicate over the bound contract, defined once
with a one-line meaning, so the report and the prompt quote it. A rule
names predicates and never a lambda.

| predicate | meaning |
| --- | --- |
| `float_mode` | the unit has a mode whose format family is float |
| `no_sr` | `rounding` does not provision `SR` |
| `no_cvt_in_float_modes` | no float mode has a legal `cvt(...)` op |
| `x_form_exact` | `x_form` is `exact` |
| `fma_contract_fused_or_no_fused_op_in_mode` | the mode's legal ops hold no fused multiply-add op (`fmadd`, `fmsub`, `fnmsub`, `fnmadd`), or `fma_contract` is `fused` (evaluated per mode index; over every float mode where no index applies) |
| `fma_contract_sequential_or_no_fused_op_in_mode` | the mode's legal ops hold no fused multiply-add op, or `fma_contract` is `sequential` (per mode index) |
| `fma_contract_cascade_product_rounding` | `fma_contract` asks for the product rounded under the family's own fixed `cascade_product_rounding` before the add; neither `fused` nor `sequential` does, so no ALU contract holds it |
| `significand_in_mode` | the mode's float format has a significand (an exponent-only format such as `e8m0` has none; per mode index) |
| `two_float_formats` | two float modes or more, with distinct formats |
| `exact_unit` | `accuracy` is `exact` |
| `approximate_unit` | `accuracy` is `approximate` |
| `dot_contract_architecture` | `dot_contract` is `architecture` |
| `dot_contract_not_fused` | `dot_contract` is `sequential` or `architecture` |
| `rounding_rne_only` | `rounding` is `[RNE]` |
| `rounding_rtz_only` | `rounding` is `[RTZ]` |
| `sr_only` | `rounding` is `[SR]` |
| `daz_and_ftz` | `daz_in` and `ftz_out` are both fixed true |
| `no_daz_no_ftz` | `daz_in` and `ftz_out` are both fixed false |
| `daz_true`, `daz_false` | `daz_in` is fixed true, or fixed false |
| `ab_bf16` | every dot mode's operand format is bf16 |
| `ab_sig_wider_than_8` | every dot mode's operand significand is wider than 8 bits |
| `ab_fp8e4m3`, `ab_fp8e5m2` | every dot mode's operand format (the block element's) is that format |
| `ab_fp8_both` | the dot modes' operand formats include fp8e4m3 and fp8e5m2 |
| `c_d_fp16`, `c_d_bf16`, `c_d_fp32` | every dot mode's D, and its C where accumulated, is that format |
| `d_integer` | every dot mode's D is an integer or fixed-point format |
| `overflow_saturate` | `overflow` is `saturate` |
| `overflow_wrap_or_d_float` | `overflow` is `wrap`, or no D is an integer format |
| `binary_integer_adder_mode` | a mode's format is a two's complement or unsigned integer or fixed point |
| `no_float_cvt_target` | no cvt op targets a float format |
| `no_div_sqrt` | the ops hold neither `fdiv` nor `fsqrt` |
| `x_form_tight` | `x_form` is `guard_round_sticky` (an `under` gate) |
| `fp_fma_fused_in_mode` | a sibling predicate: `fp_fma.family` is a fused family (every family of the slot but `separate_multiplier_and_adder`); lowered into a member condition |
| `operand_order_shift_each` | a sibling predicate: `fp_adder.operand_order` is `shift_each_operand`; lowered into a member condition |
| `string_form_dual` | a sibling predicate on the same family's `string_form`, `dual_pos_neg_strings`; lowered into a nested choice's `when` |
| `sharing_dedicated_per_mode` | a sibling predicate on the same family's `sharing`, `dedicated_per_mode`; lowered into a member condition |
| `composition_style_cascade` | a sibling predicate on the same family's `composition_style`, `cascade_mul_then_add`; lowered into a nested choice's `when` |
| `pins_equal_across_sharing_modes` | not evaluable: an equality across the modes' variables; names the deferred rules |
| `subnormal_representation_read_by_bridge` | not evaluable: the choice reaches the netlist, which under `bridge_fma` with `composition_style: bridge_reuse` it does not; an inactivity under two siblings' values on a variable four families share, which one `when` does not state; names a deferred rule |

A sibling predicate carries `sibling=(path, values)` in place of `holds`:
`path` is `<slot>.<choice>` relative to the unit, or a bare choice name
of the same family; `values` is a tuple or a callable returning one,
evaluated at lowering. `docs/adir_member_when_plan.md` describes the
ADIR side (`Variable.member_when`) and the four reads that honor it.

### The rule table

A rule is `Rule(key, requires, kind, slot, evidence)`:

* `key` is an fnmatch pattern over `family|choice|member`, the
  `archdocs.MEMBER_ALLOWLIST` style; a family-level rule is `family|*|*`
  and a choice-level rule `family|choice|*`.
* `slot` is an fnmatch pattern over the slot path where the family stands
  (`fp_fma`, `fp_multiplier`, `dot`, `fp_adder.lz`); it separates the
  families two kinds share by name (the dot's and the fp_fma slot's
  `classic_fma`, the rounder's and the unpacker's `shared_per_lane`).
* `kind` is one of five:
  * `behavior`: the member computes the contract only under `requires`.
    A `requires` over the contract removes the member at elaboration; a
    sibling predicate becomes a member condition (`Variable.member_when`)
    that ADIR checks per candidate.
  * `selector`: the member selects the behavior. An enum member of this
    kind is excluded from an exact unit; a numeric choice of this kind
    (`window_bits`) is never searched and stands YAML-fixed, the
    conformance gate deciding at declaration.
  * `interface`: the member cannot be built under the unit's interface
    (formats, op set, mode count); reported apart from the behavioral
    rules. A `retired` interface rule names a member the space no longer
    holds, so the generator keeps rejecting old inputs.
  * `nested`: a choice-level rule (`family|choice|*`) whose sibling
    predicate names a bare choice of the same family: the choice is a
    decision under that sibling's member alone, and the prune moves the
    choice's `when` onto the sibling.
  * `deferred`: a rule the space cannot express at elaboration. It is
    reported, its render-time raise stays as the last defense, and the
    predicate it names is not evaluable.
* `under` names contract predicates the rule applies under; where one
  fails the rule is inert and the member is admitted without a condition.
* `evidence` points at the fptest variant, the selftest or the render-time
  check that shows the claim.
* a `retired` rule carries `retired_domain` (the former `values` or
  `range`) and its own `reason`; `retired_dot_choices()` renders these in
  the shape `fma_dot_spaces.UNSUPPORTED_DOT_CHOICES` had, which
  `dot_sv`, `variant_legality` and `dot_coverage_audit` keep reading.

The rules registered now:

| key | slot | kind | requires | evidence |
| --- | --- | --- | --- | --- |
| `*\|subnormal_representation\|as_stored` | `fp_fma` | behavior | `no_sr` | `families/fp.py:fma_sv` raises under SR; `fptest --sr` runs the fused variants normalized; the four fused families share the variable, and under `bridge_fma` with `bridge_reuse` the choice is inactive, so the narrowing loses no design there |
| `bridge_fma\|composition_style\|cascade_mul_then_add` | `fp_fma` | behavior | `fma_contract_cascade_product_rounding` | `families/fp.py:fma_sv` raises (the last defense); `variant_legality.own_reason` keeps it out of the sweep; `behavior_rules_selftest` shows the removal and the raise |
| `bridge_fma\|composition_style\|bridge_reuse` | `fp_fma` | behavior | `x_form_exact` | `families/fp.py:fma_sv` raises at the tight X (the last defense); `fptest --tight` skips the bridge; `behavior_rules_selftest` conforms with `bridge_reuse` at the exact X |
| `round_fused_in_reduction\|*\|*` | `fp_multiplier` | behavior | `x_form_exact` | `families/fp.py:mul_sv` raises at the tight X; `fptest --tight` skips it; `alu_fidelity_selftest` conforms at the exact X |
| `posit_adder_multiplier\|approximation\|logarithmic_fraction` | `posit_unit` | selector | `approximate_unit` | `alu_float.py:declare_posit_library` (the PLAM module, under the approximate contract) |
| `pairwise_tree\|per_level_truncation\|True` | `dot` | behavior | `dot_contract_architecture` | `dot_seed.py` raises: changes intermediate values |
| `multi_term_fused_dot\|rounding_contract\|faithful`, `\|truncated_with_guard` | `dot` | behavior | `dot_contract_architecture` | the same |
| `bridge_fma\|composition_style\|cascade_mul_then_add` | `dot` | behavior | `dot_contract_not_fused` | `families/dot.py:dot_family_requirements` (the sequential contract) |
| `mixed_precision_cascade_fma\|exact_product_preserved\|False` | `dot` | behavior | `dot_contract_not_fused` | the same |
| `mixed_precision_cascade_fma\|two_term_expansion_output\|True` | `dot` | behavior | `dot_contract_architecture` | `families/dot.py:validate_unit_binding` |
| `bf16_fma_datapath\|rounding_mode\|rne`, `\|rtz`, `\|round_to_odd` | `dot` | behavior | `rounding_rne_only`, `rounding_rtz_only`, `dot_contract_architecture` | `validate_unit_binding` |
| `bf16_fma_datapath\|flush_subnormals\|True`, `\|False` | `dot` | behavior | `daz_and_ftz`, `no_daz_no_ftz` | `validate_unit_binding` |
| `fp8_training_datapath\|stochastic_rounding\|True`, `\|False` | `dot` | behavior | `sr_only`, `no_sr` | `validate_unit_binding` |
| `fp8_training_datapath\|chunk_based_accumulation\|True` | `dot` | behavior | `dot_contract_architecture` | `dot_family_requirements` |
| `tensor_core_mixed_precision_mac\|subnormal_support\|True`, `\|False` | `dot` | behavior | `daz_false`, `daz_true` | `validate_unit_binding` |
| `integer_mac\|saturating_accumulate\|True` | `dot` | behavior | `d_integer`, `overflow_saturate` | `validate_unit_binding` |
| `integer_mac\|saturating_accumulate\|False` | `dot` | behavior | `overflow_wrap_or_d_float` | `validate_unit_binding` |
| `multi_term_fused_dot\|window_bits\|*` | `dot` | selector | (numeric: fixed-only) | commit d76bd41; `dot_window_selftest`; `families/dot.py` raises below the minimum |
| `streaming_accurate_accumulator\|window_bits\|*` | `dot` | selector | (numeric: fixed-only) | `dot_arch_ref.py` reads the pin; `families/dot.py` raises below the minimum |
| `kulisch_long_accumulator\|accumulator_width_bits\|*`, `integer_mac\|accumulator_width_bits\|*` | `dot` | selector | (numeric: fixed-only) | `families/dot.py` raises below the exact frame |
| `shared_across_formats\|*\|*` | `rounder`, `unpacker` | interface | `two_float_formats` | `alu_seed.py` raises: requires two distinct selected formats |
| `*\|sharing\|shared_across_formats` | `fp_fma` | interface | `two_float_formats` | the same |
| `partitioned_carry_chain\|*\|*` | `subword` | interface | `binary_integer_adder_mode` | `generators.py:families_of` |
| `posit_ieee_interop\|conversion_direction\|ieee_to_posit` | `posit_unit` | interface | `no_float_cvt_target` | `alu_float.py:declare_posit_library` |
| `posit_adder_multiplier\|operator_set\|add_mul` | `posit_unit` | interface | `no_div_sqrt` | `alu_float.py:declare_posit_library`; `generators.py:families_of` |
| `bf16_fma_datapath\|*\|*` | `dot` | interface | `c_d_fp32` | `validate_unit_binding` |
| `bf16_fma_datapath\|multi_word_composition\|False`, `\|True` | `dot` | interface | `ab_bf16`, `ab_sig_wider_than_8` | `validate_unit_binding` |
| `fp8_training_datapath\|format_policy\|single_e4m3`, `\|single_e5m2`, `\|hybrid_forward_e4m3_backward_e5m2` | `dot` | interface | `ab_fp8e4m3`, `ab_fp8e5m2`, `ab_fp8_both` | `validate_unit_binding` |
| `fp8_training_datapath\|accumulate_precision\|fp16`, `\|bf16`, `\|fp32` | `dot` | interface | `c_d_fp16`, `c_d_bf16`, `c_d_fp32` | `validate_unit_binding` |
| the eight former `UNSUPPORTED_DOT_CHOICES` entries | `dot` | interface, retired | (none) | `families/dot.py:dot_sv` rejects them; `fma_dot_spaces.UNSUPPORTED_DOT_CHOICES` is now a view of these rules |
| `*\|denormal_handling\|in_datapath` | `unpacker` | behavior (a member condition) | `fp_fma_fused_in_mode`, `under=x_form_tight` | `alu_mode.py:tight_x` raises (the last defense); `behavior_rules_selftest` conforms with `classic_fma` at the tight X |
| `lza\|string_form\|dual_pos_neg_strings` | `fp_adder.*` | behavior (a member condition) | `operand_order_shift_each` | `families/fp.py:add_sv` raises (the last defense); `behavior_rules_selftest` conforms under `shift_each_operand` |
| `reduced_latency_fma\|rounding_position\|fused_with_cpa_dual_sum` | `fp_fma` | behavior (two contract predicates and a member condition) | `x_form_exact`, `significand_in_mode`, `sharing_dedicated_per_mode` | `families/fp.py:fma_sv` raises at the tight X, without a significand and under `shared_across_formats` (the last defense); `fptest`'s two fused-rounding variants conform in the three roles at the exact X; `behavior_rules_selftest` shows the removal at the tight X, the condition on `sharing`, the rejected VAR line, the raise, and conformance under `dedicated_per_mode` |
| `lza\|split_string_select\|*` | `fp_adder.*` | nested | `string_form_dual` | `add_sv` selects between the two strings alone |
| `bridge_fma\|cascade_product_rounding\|*` | `*` (the dot and the fp_fma slot) | nested | `composition_style_cascade` | `families/dot.py:_bridge_sv` reads the rounding under the cascade alone; on the fp_fma slot the cascade is removed, so the choice is never active there |
| `shared_across_formats\|*\|*` | `rounder`, `unpacker` | deferred | `pins_equal_across_sharing_modes` | `alu_seed.py` raises: requires compatible pins on its one physical datapath |
| `*\|sharing\|shared_across_formats` | `fp_fma` | deferred | `pins_equal_across_sharing_modes` | `alu_seed.py` builds the shared datapath at the widest geometry; no pin check on the fp_fma sharing |
| `bridge_fma\|subnormal_representation\|*` | `fp_fma` | deferred | `subnormal_representation_read_by_bridge` | `alu_contracts.alu_active_parameters` names the choice inactive under `bridge_reuse` (the variant sweep rejects an explicit value); `families/fp.py:fma_sv` drops the pin there and keeps it under `monolithic_fused`, whose datapath is classic_fma's |

The family-level conditions live on the `Family`:

| family | slot | requires | evidence |
| --- | --- | --- | --- |
| `classic_fma`, `reduced_latency_fma`, `multipath_fma`, `bridge_fma` | `fp_fma` | `fma_contract_fused_or_no_fused_op_in_mode` | `alu_float.py:declare_library` raises for a fused family under `fma_contract: sequential` with a fused op (the last defense); `fptest` runs each fused variant as the adder, as the multiplier and on the fused ops; `behavior_rules_selftest` conforms with `classic_fma` on `fmadd` under `fused` and in a mode with `fadd` and `fsub` alone |
| `separate_multiplier_and_adder` | `fp_fma` | `fma_contract_sequential_or_no_fused_op_in_mode` | `alu_float.py:declare_library` raises for it under `fma_contract: fused` with a fused op (the last defense); `behavior_rules_selftest` conforms with it on `fmadd` under `sequential` |
| `streaming_accurate_accumulator`, `tensor_core_mixed_precision_mac` | `dot` | `dot_contract_architecture` | `dot_seed.py` raises: changes intermediate values; `dot_family_requirements` |

The option rules (`OPTION_RULES`, the checker's own half):

| option | value | requires | evidence |
| --- | --- | --- | --- |
| `x_form` | `guard_round_sticky` | `float_mode`, `no_cvt_in_float_modes`, `no_sr` | `fptest --tight` runs every float family at the tight X (the stochastic mode skipped); `alu_mode.py:tight_x` raises for a mode with conversion targets or SR |

### The rule granularity the space honors

* A family-level rule narrows the slot's family enum; the family's choice
  variables stay in the tree and are never active.
* A choice-level rule and a member-level rule narrow one variable. A
  choice shared by several families of one space is one union variable
  (`adir.spaces._union`), so a member is removed only where every family
  that declares the member excludes it under the contract. Where the
  families sharing a variable disagree, the member stays, the report
  names the disagreement, and the render-time check of the stricter
  family remains the defense. No registered rule hits this case today:
  the four fused fp_fma families share `subnormal_representation` and
  the rule applies to all four (under `bridge_fma` with `bridge_reuse`
  the choice is inactive, so the narrowing loses no design there, and a
  deferred rule records the inactivity).
* A member admissible under another searched choice's value is a member
  condition (ADIR's `Variable.member_when`): the member stays in the
  domain, the prompt lists it with its condition, and the declaration
  check rejects it under a sibling value outside the allowed ones. A
  union variable takes the condition only where every declaring family
  agrees on it; a disagreement is reported as for an exclusion.
  `docs/adir_member_when_plan.md` holds the design.
* A rule whose condition is an equality across the variables of several
  modes (the sharing pins) is a `deferred` rule.
* A rule whose per-mode predicate differs across the indexes of one slot
  narrows each index's domain separately through the per-index domains
  below; no slot is over-pruned for the unit.
* A family whose every member of one choice is excluded is excluded
  itself, with the choice named as the reason, so no variable is left
  with an empty domain.

## The `x_form` promotion

`x_form` was a design choice of the three rounder families
(`misc_spaces.X_FORM`), which every emitter of the mode read through the
declared family. It becomes a unit option of `chialu.ALU`, like
`sr_bits`:

* the variable `x_form`, `Enum(("exact", "guard_round_sticky"))`, fixed,
  loader default `exact` (`binding_defaults`, the class of defect
  `docs/issues.md` records for a missing default);
* `spec_from_bindings` copies it into the spec and `alu_ref.SPEC_DEFAULTS`
  carries `exact`, so `normalize_spec` always presents it;
* `omitted_options` names it off a unit without a float mode, so the
  prompt counts it among the options that do not apply;
* `alu_mode.tight_x` reads the spec rather than the rounder's pins; the
  option applies to the float modes of the unit, and an integer, posit or
  block mode keeps the exact X;
* the rounder families lose the choice; the cards under
  `chialu/knowledge/arch/round/` and `arch/unpack/` name the option;
  `docs/formats-and-options.md` section 3.9 gains the row;
* `targets/eval/fp_alu_cmp_fpnew.yaml` and `fp_alu_cmp_hardfloat.yaml`
  bind `x_form: {fixed: guard_round_sticky}` in place of the three
  per-mode rounder lines each.

Every rule about the X form then depends on the YAML alone. The rule on
`round_fused_in_reduction` becomes a prune, and the rule on
`guard_round_sticky` itself becomes an option rule the checker raises at
load.

## The pitfalls and the decision on each

| pitfall | decision |
| --- | --- |
| 1. A rule is a claim | A wrong rule either admits a behavior-changing member, which conformance catches, or excludes a valid one silently. Conformance stays the last gate. `chialu.eda.conformance` parses the candidate's declaration block on a failure and, where the declaration names a conditional member the rules admitted, marks the result `rule_defect_candidate: true` with the members named, so the archive separates those failures from ordinary ones; `python3 -m chialu.behavior_rules defects <results_db.jsonl>` lists them. A stronger classification (the candidate edited no region) needs `candidate.touched` as a node input and is deferred. |
| 2. Conditions on other searched choices | `x_form` is promoted, so `round_fused_in_reduction` and `guard_round_sticky` depend on the YAML alone. `denormal_handling: in_datapath` under the tight X and the dual LZA strings are member conditions (ADIR's `Variable.member_when`, `docs/adir_member_when_plan.md`): the member stays in the menu with its condition and ADIR rejects a declaration that names it under a disallowed sibling value, the render-time raise staying the last defense. The equal pins of `shared_across_formats` across modes stay `deferred`: an equality across several modes' variables is an alias of those variables rather than a member condition, and the render-time raise stays. The alternative for the first, a tight separate multiplier that normalizes its own product, is deferred: it adds a leading-zero count and a shifter over the 2 SW-bit product and an exponent subtract outside any slot inside `mul_sv`, which the coverage lint would flag as undeclared components. |
| 3. Per-mode conditions against one domain per template | ADIR's `Variable.index_domains` (below) gives each index of one template its own domain; the prune evaluates a per-mode predicate per index and narrows only the indexes it fails for. The fp_fma slot of a mode with a fused op under `fma_contract: fused` loses `separate_multiplier_and_adder` while a mode without a fused op keeps both organizations. A fused family serves any subset of `fadd`, `fsub` and `fmul` (the fused ops alone included), so the count of op classes in the mode is no condition; the former `fadd_and_fmul_in_mode` condition left with the merge of the fma-space line (2026-09-19). |
| 4. Default drift | The remaining members keep the domain's order, so the default is the first remaining member, deterministically. The prune reports every variable whose default changed (`core.fp_fma.*.subnormal_representation: default as_stored -> pseudo_normalized_wide_exponent`), and the seed's `_declared_value` follows the narrowed domain. |
| 5. A shared choice is one union variable | See the granularity above: a member is removed where every declaring family excludes it; a disagreement keeps the member and is reported; today no rule disagrees. |
| 6. Visibility | `info["behavior_rules"]` is a string the composer prints in the unit section: each behavior and interface removal with its rule and the option that triggered it, the selectors an exact unit sheds summarized per member (`approximate_truncated` alone leaves every nested adder slot, 60 of them on the fp_alu_cmp targets), and the sentence that a VAR line naming one is rejected. `info["behavior_report"]` holds the rows, the default changes, the deferred rules and the disagreements (`python3 -m chialu.behavior_rules report <run file>` prints them). `info["families"]` drops the families excluded at every structure of a slot. The cards keep describing every member. A removed member stays in the domain's `excluded` pairs with its reason, so ADIR's declaration check, the loader's fixed check and `plan_vars` report `fixed: 'as_stored' outside enum['pseudo_normalized_wide_exponent']: classic_fma subnormal_representation as_stored needs no_sr (rounding does not provision SR); the unit has rounding ['RNE', 'SR']` rather than `outside enum[...]` alone. |
| 7. Necessary and sufficient | `chialu/verify/behavior_rules_selftest.py` shows, for representative rules, that the excluded member under the excluding contract fails to render or fails conformance, and that the admitted member conforms under an admitting contract (the test plan below). |
| 8. Approximate units | Their behavior is the error budget, and the budget gate is their checker. Under `accuracy: approximate` the prune keeps the selectors and applies the interface rules only (`behavior_rules_apply` is false, `selector_admitted` true); the SFU class is not pruned, and its families are classified `selector` to state that its behavior is the budget's. `approx_alu.yaml` elaborates with 0 removals. |
| 9. Geometry-dependent numeric bounds | `multi_term_fused_dot.window_bits`, `streaming_accurate_accumulator.window_bits`, `kulisch_long_accumulator.accumulator_width_bits` and `integer_mac.accumulator_width_bits` are `selector` numerics: ADIR's `Variable.search_domain` (below) makes a `search` binding over them a one-member domain at the default (`core.*: {search: all}` keeps loading), while a `fixed` binding admits any value of the range and the conformance gate decides on the seed. `vec_dot_acc_cmp_fp16_tdw.yaml` binds `core.window_bits: {fixed: 76}` and keeps loading. |
| 10. Interface exclusions | The `interface` kind in the same registry, reported apart. The former `UNSUPPORTED_DOT_CHOICES` entries are `retired` interface rules, and `fma_dot_spaces.UNSUPPORTED_DOT_CHOICES` is derived from them so `dot_sv`, `variant_legality` and `dot_coverage_audit` keep their input. The format and option rules of `validate_unit_binding` join as interface and behavior rules; the geometry checks (a product count, a window below the minimum) stay at render time. |
| 11. The checker at load | `elaborate` raises on an option rule before any space compiles. The prune writes each removal's reason into the domain, so ADIR rejects a contradicting `fixed` binding at `bind_defaults`, before any artifact renders, and `plan_vars` and `check_declaration` reject a plan pin or a VAR line with the same text. Searched variables are the prune's; fixed ones are the checker's. |
| 12. Caches keyed on the space id | `space_hash` covers the templates' domains, so a narrowed domain, a per-index domain or a search domain moves the archive identity of the elaboration; the per-node caches key on the candidate text and the flow and do not move. |

## The ADIR question and its answer

ADIR can express a variable whose existence depends on one parent's value
(`when`), one domain per indexed template, and one domain per variable
for every binding time. It cannot express a member-level condition (a
domain that depends on a sibling's value) or a per-index domain, and
chialu cannot split an index set alone: two templates cannot share the
`*` name (`_bind_variables` rejects a duplicate), and a static copy of one
index breaks `VariableTree.children_of`, which keys the children on the
parent's template name. The checkers therefore take a small additive ADIR
change, committed on the submodule's `behav-checker` branch:

| file | change |
| --- | --- |
| `spaces.py` | `Family.behavior`, `Family.requires`, `Family.evidence`; an `algorithm_level` family without a `behavior` is a `selector`; `requires` on a family that is not `conditional` is an error |
| `domains.py` | `Domain.exclusion_reason(v)` (None) and `Domain.outside_detail(values)`; `Enum.excluded`, the (member, reason) pairs a check removed, kept out of the members and out of `to_json`'s choices; `Enum.without(reasons)` builds the narrowed enum and refuses to empty it; `narrow` names the reason for an excluded member |
| `variables.py` | `Variable.index_domains` (index to Domain, applied by `expand`); `Variable.search_domain` and the `searchable` property (the domain a `search` binding narrows within; `domain` stays the fixed binding's); `bind_variables` and `bind_one` name the reason on a fixed or runtime value outside the domain |
| `declaration.py` | the `outside` problem of `check_declaration` names the reason |
| `instance.py` | `space_hash` covers `index_domains` and `search_domain` where a template carries them, so an instance without either keeps its hash |
| `docs/design.md` | the three fields and the classification, under section 3.5 |

Member-level `when` followed in a second ADIR change (`Variable.member_when`,
`docs/adir_member_when_plan.md`): a member admissible while a sibling
variable holds one of a set of values, read at `bind_variables` and
`bind_one`, `Bindings.default_of`, `check_declaration`, the composer and
the numeric backends, with the sibling ordered before the member in
`_topological` and a cycle rejected at load. The registry lowers a
sibling predicate into it, and a `nested` rule into a choice's `when` on
a sibling choice.

## The classification of the families

195 families stand in the spaces `chialu/papers._all_spaces` walks. Each
`Family(...)` declaration carries its `behavior`; the table groups them by
the space that opens them.

| space | neutral | conditional | selector |
| --- | --- | --- | --- |
| logic | `lane_replicated_gates`, `wide_gate_row`, `alu_pg_fused` | | |
| rounder, unpacker | `dedicated_per_op`, `shared_per_lane`, `shared_across_formats` (both kinds), `per_unit_unpack` | | |
| adder (`cpa_space`, incrementer, comparator) | `ripple_carry`, `manchester_carry_chain`, `carry_lookahead`, `carry_skip`, `parallel_prefix`, `conditional_sum`, `carry_select`, `carry_increment`, `sparse_prefix_hybrid`, `ling_prefix`, `compound_flagged_prefix`, `end_around_carry`, `prefix_synthesis_nonuniform_arrival`, `fpga_carry_chain`, `prefix_and_incrementer`, `prefix_comparator`, `subtractor_comparator` | | `approximate_truncated` |
| lzc, bitcount, shifter, subword | `lzd_cell_tree`, `prefix_lzc`, `popcount_counter_tree`, `priority_encoder`, `trailing_zero`, `barrel_mux_tree`, `funnel`, `masked_merged`, `butterfly_network`, `partitioned_carry_chain`, `replicated_lanes` | | |
| multiplier | `behavioral_star`, `booth_recoded_parallel`, `csa_reduction_tree`, `uniform`, `hybrid_arrival_driven`, `compressor_4_2_tree`, `tiled_cpa_reduction_tree`, `direct_pp_parallel`, `carry_save_array`, `recursive_karatsuba`, `squarer`, `twin_precision_subword`, `segmented_grid`, `redundant_binary_multiplier` | | `truncated_fixed_width`, `logarithmic_mitchell`, `approximate_compressor` |
| divider, seed tables, final rounding | `restoring_nonrestoring`, `srt_radix2`, `srt_high_radix`, `qds_table`, `comparator_digit_selection`, `prescaled_very_high_radix`, `svoboda_tung`, `newton_raphson`, `goldschmidt`, `direct_polynomial`, `digit_recurrence_sqrt_combined`, `online_msdf`, `monolithic_rom`, `bipartite_rom`, `symmetric_bipartite`, `multipartite`, `operand_modification_multiply`, `poly_seed`, `magic_constant_bit_seed`, `back_multiply_remainder`, `exclusion_zone_proof`, `extra_precision_quotient` | | |
| fp_adder and its slots | `single_path`, `two_path`, `delay_optimized_unified`, `low_power_gated`, `exponent_path`, `full_align`, `coarse_fine`, `single_barrel`, `lza`, `lzc_after_add` | | |
| fp_multiplier, fp_divider, fp_comparator, converter | `sig_mul_then_round`, `round_fused_in_reduction` (a member rule narrows it), `sig_div_then_round`, `sig_sqrt_then_round`, `integer_compare_on_bits`, `dedicated_magnitude_comparator`, `shift_round_convert` | | |
| rounding (`round` slot) | `increment_adder`, `compound_adder_select`, `injection`, `flagged_prefix` | | |
| fp_fma | | `separate_multiplier_and_adder` (`fma_contract_sequential_or_no_fused_op_in_mode`); `classic_fma`, `reduced_latency_fma`, `multipath_fma`, `bridge_fma` (`fma_contract_fused_or_no_fused_op_in_mode`) | |
| dot | `pairwise_tree`, `fused_csa`, `integer_mac`, `classic_fma`, `reduced_latency_fma`, `multipath_fma`, `bridge_fma`, `mixed_precision_cascade_fma`, `multi_precision_simd_fma`, `fused_two_term_dot`, `multi_term_fused_dot`, `kulisch_long_accumulator`, `bf16_fma_datapath`, `fp8_training_datapath`, `bounded_align`, `linear_chain`, `binary_tree`, `csa_tree` | `streaming_accurate_accumulator`, `tensor_core_mixed_precision_mac` (`dot_contract_architecture`) | `block_fp_accumulation`, `mx_microscaling_dot` |
| checker, two-rail | `residue`, `inverse_residue`, `multi_residue`, `rns_redundant`, `an_code`, `berger`, `parity_prediction_adder`, `parity_prediction_multiplier`, `reduced_precision`, `duplication`, `direct_compare`, `two_rail_tree`, `m_out_of_n_checker`, `majority_voter` (the checker never touches `y`; its gate is the fault campaign) | | |
| decimal | `bcd_direct_addition`, `speculative_decimal_addition`, `redundant_decimal_addition`, `decimal_multioperand_addition`, `parallel_decimal_multiplication`, `decimal_digit_recurrence`, `decimal_newton` | | |
| redundant | `generalized_signed_digit`, `hybrid_signed_digit`, `carry_save_datapath`, `rns_channel_arithmetic`, `rns_reverse_converter`, `rns_forward_converter`, `rns_scaling_comparison` | | |
| approx | | | `segmented_carry_speculative`, `lower_part_approximate`, `accuracy_configurable`, `dynamic_segment`, `operand_rounding`, `logarithmic`, `pp_perforation`, `approximate_compressor_tree`, `approximate_booth`, `approximate_recurrence`, `approximate_functional` |
| posit_unit | `posit_adder_multiplier` (member rules narrow `approximation` and `operator_set`), `posit_ieee_interop` | | |
| sfu | | | every family of `sfu_approx_space`, `poly_datapath_space`, `segment_space` and `range_reduction_space` (35): the SFU's behavior is its error budget |

Counts over the 195 families of the spaces: 136 neutral, 7 conditional,
52 selector (a name shared by two slots, the dot's and the fp_fma slot's
`bridge_fma`, counts once, under the classification of the slot the lint
walks first). The three core partitionings of `chialu.ALU`
(`unit_per_class`, `redundant_internal`, `rns_internal`) are neutral
too, so the lint reports 198 families: 139 neutral, 7 conditional,
52 selector, 59 rules (8 retired, 5 on a sibling, 4 deferred) and 1
option rule.

## The migration

1. ADIR: the five files above, on the submodule branch `behav-checker`;
   every ADIR test passes.
2. `chialu/behavior_rules.py`: the predicate table, the rule table, the
   option rules, the evaluation (`check_options`, `prune_slot`, the report),
   the lint and the CLI.
3. Every `Family(...)` declaration gains `behavior=...` (a scripted pass
   over `chialu/spaces/*.py` inserts `behavior="neutral"`, then the
   conditional and selector ones are edited by hand); the lint reports
   `0 unregistered, 0 stale`.
4. `x_form` promotion, the two run files, the cards, the documents.
5. The prune in `chialu.ALU.elaborate` and `chialu.VecDotAcc.elaborate`
   replaces `exact_only`; the report reaches `info`; `plan_vars` and the
   render-time checks carry the reason.
6. `fma_dot_spaces.UNSUPPORTED_DOT_CHOICES` becomes a view of the retired
   rules; the render-time raises that now duplicate a registered rule are
   marked as the last defense.
7. The selftest, the target loads, the selftests that exist, `archdocs`,
   and the conformance of the three `fp_alu_cmp` run files.

The exclusion of unregistered families is on from the first commit, since
every family is classified in the same change; the lint gate keeps it
honest for a family added later.

## The test plan

`chialu/verify/behavior_rules_selftest.py` runs in the fast set and
covers:

* the lint: 0 unregistered families, 0 stale rules, every predicate a
  rule names exists, every conditional family and rule carries evidence;
* `x_form: guard_round_sticky` with a float mode that has `cvt(int8)`:
  `elaborate` raises with the mode named; the same spec forced through
  `tight_x` raises (the last defense); without the cvt op the fp16 seed
  at `guard_round_sticky` conforms on 64 vectors (`check_seed`);
* `round_fused_in_reduction` under `guard_round_sticky`: excluded from
  `core.fp_multiplier.*.family` with the reason; forced through
  `mul_sv` it raises; under `exact` the fp16 seed with it conforms;
* `subnormal_representation: as_stored` under `rounding: [RNE, SR]`:
  excluded with the reason and the default drift reported; forced through
  `fma_sv` it raises; under `[RNE]` the fp16 `classic_fma` seed conforms;
* a two-mode unit whose first float mode has `fmadd` and whose second
  has `fadd` and `fsub` alone, under `fma_contract: fused`:
  `separate_multiplier_and_adder` leaves `core.fp_fma.m0.family` and
  stays in `core.fp_fma.m1.family` (the per-index domain, visible through
  `Variable.expand`, with the default change reported); forced,
  `declare_library` raises ("fma_contract fused"); `classic_fma` on both
  modes conforms, so the fused ops and the mode with `fadd` and `fsub`
  alone are served;
* the same ops under `fma_contract: sequential`: the fused families leave
  the slot with the reason; forced, `declare_library` raises
  ("fma_contract sequential"); `separate_multiplier_and_adder` conforms
  on `fmadd`; a unit without a fused op keeps both organizations under
  either contract;
* `bridge_fma`: `cascade_mul_then_add` leaves `composition_style` with
  the reason and its forced seed raises; `cascade_product_rounding`
  carries the `when` on the cascade; `bridge_reuse` leaves under
  `guard_round_sticky` and its forced seed raises; at the exact X
  `bridge_reuse` conforms, and `monolithic_fused` with `as_stored`
  conforms (the choice is classic_fma's there); the deferred rule on the
  bridge's `subnormal_representation` is in the report;
* `reduced_latency_fma`'s `fused_with_cpa_dual_sum`: leaves under
  `guard_round_sticky` and its forced seed raises; on a two-format unit
  the member carries the condition on `core.fp_fma.*.sharing`, the VAR
  line under `shared_across_formats` is rejected with the sibling named,
  the forced seed raises ("dedicated_per_mode"), and the member conforms
  under `dedicated_per_mode`;
* the PLAM member under `accuracy: exact`: excluded; forced, the posit8
  `fmul` seed fails conformance;
* the dot: `core.window_bits` searches one member and takes a fixed 76
  (`vec_dot_acc_cmp_fp16_tdw.yaml` loads); `streaming_accurate_accumulator`
  is excluded under `dot_contract: fused` with the reason and forced it
  raises; a retired member still raises in `dot_sv`;
* a declaration naming an excluded member is rejected by
  `check_declaration` with the reason in the detail.

The run-level checks:

* every run file under `targets/` and `targets/eval/` loads and its seed
  renders (`adir.instance.load`, `adir.seeds.seed_programs`,
  `chialu.eda.rtl_of`);
* `python3 -m chialu.verify.<name>` for family_space, check_rules,
  float_seed, fp_cpa, alu_fidelity, module_collector, mode_ops,
  exponent_rounder, dot_structural, formats and behavior_rules;
* `python3 -m chialu.archdocs` exits 0; `python3 -m chialu.behavior_rules
  lint` exits 0;
* conformance of `fp_alu_cmp_fpnew`, `fp_alu_cmp_hardfloat` and
  `fp_alu_cmp` through `adir.registry.underlying(chialu.eda.conformance)`.

## Results (2026-09-18, on the development machine)

* `python3 -m chialu.behavior_rules lint`: 198 families (141 neutral,
  5 conditional, 52 selector), 51 rules (8 retired), 0 unregistered,
  0 stale; exit 0.
* `python3 -m chialu.archdocs`: 195 docs for 195 families, 0 undescribed
  members, 0 unmet claims; exit 0.
* Every run file under `targets/` and `targets/eval/` loads and its seed
  renders: 26 of 26.
* `fp_alu_cmp_fpnew.yaml` loads in 45.7 s, of which `elaborate` takes
  1.7 s and the verify bundle's reference vectors the rest; the prune's
  own cost is inside the 1.7 s.
* Removals per run file: 97 on `fp_alu_cmp` (the selectors in every
  nested adder slot, `partitioned_carry_chain` on a unit without an
  integer mode), 98 on the FPnew and HardFloat bindings (plus
  `round_fused_in_reduction` under `guard_round_sticky`), 137 on
  `mixed_cvt_alu`, 91 on `vec_dot_acc`, 309 on `posit_alu`, 0 on
  `approx_alu`.
* Default changes: `core.subword.family` to `replicated_lanes` on the
  float-only units, `core.exact_product_preserved` to true on the fused
  dot units, `core.multi_word_composition` to true on the fp16 dot unit.
* `python3 -m chialu.verify.<name>_selftest`: family_space 28 s,
  check_rules 3 s, float_seed 3 s, fp_cpa 6 s, alu_fidelity 47 s,
  module_collector 7 s, mode_ops under 1 s, exponent_rounder 54 s,
  dot_structural 7 s, formats 2 s, behavior_rules 19 s; every one passes.
* The behavior_rules selftest's forced PLAM multiplier mismatches on 33
  of 64 vectors, so the selector rule is necessary; the forced
  `round_fused_in_reduction` at the exact X and the forced `as_stored`
  under RNE conform, so the two conditional rules are not over-strict.
* Conformance through `adir.registry.underlying(chialu.eda.conformance)`:
  `fp_alu_cmp_fpnew` bit-exact in 65 s, `fp_alu_cmp_hardfloat` bit-exact
  in 65 s, `fp_alu_cmp` bit-exact in 31 s.
* ADIR's own tests: 34 pass before and after the change.

## Results (2026-09-19, the merge with the fma-space line)

The fma-space line (the fused ops `fmadd`, `fmsub`, `fnmsub`, `fnmadd`
under `fma_contract`, `bridge_fma` and `reduced_latency_fma`'s fused
rounding on the ALU's fp_fma slot) merges into this line, and its rules
enter the registry: the fp_fma families' classification against
`fma_contract`, two behavior rules and a nested rule on `bridge_fma`, the
three-predicate rule on `fused_with_cpa_dual_sum`, and the deferred rule
on the bridge's `subnormal_representation`.

* `python3 -m chialu.behavior_rules lint`: 198 families (139 neutral,
  7 conditional, 52 selector), 59 rules (8 retired, 5 on a sibling,
  4 deferred), 0 unregistered, 0 stale; exit 0.
* `python3 -m chialu.archdocs`: 195 docs for 195 families, 0 undescribed
  members, 0 unmet claims; the two `SHARED NAME` lines; exit 0.
* Every run file under `targets/` and `targets/eval/` loads and its seed
  renders: 27 of 27 (`fp_fma_alu.yaml` in 56.9 s; its report holds 99
  removals, 3 member conditions, 5 deferred rules, 0 not lowered,
  0 disagreements). The float run files carry the condition on
  `core.fp_fma.*.rounding_position` beside the two on the adder's
  `string_form`.
* `behavior_rules_selftest`: every case passes, the new ones included:
  the forced `separate_multiplier_and_adder` under `fused` and the forced
  `classic_fma` under `sequential` raise, `classic_fma` conforms on
  `fmadd` and in a mode with `fadd` and `fsub` alone, the separate
  organization conforms on `fmadd` under `sequential`, `bridge_reuse` and
  `monolithic_fused` with `as_stored` conform at the exact X, and the
  fused rounding conforms under `dedicated_per_mode`.
* The other selftests pass: family_space 37 s, check_rules 5 s,
  float_seed 7 s, fp_cpa 11 s, alu_fidelity 107 s, module_collector
  15 s, mode_ops under 1 s, exponent_rounder 94 s, dot_structural 7 s,
  formats 2 s; `variant_selftest --kinds fp_fma --widths 16 --limit 40
  --vectors 256`: 40 of 40 pass (the bounded sweep is incomplete by
  construction).
* `fptest --formats fp16,bf16,fp8e5m2,fp8e4m3`: 321 of 322 pass; the
  failure is the fp16 `direct_polynomial` sqrt bench, a Verilator
  internal fault on macOS that passes on the host. With `--tight`: 260 of
  266 pass; the six failures are the fp8e4m3 `fam_fp_round_*` benches
  that predate both lines.
* Conformance through `adir.registry.underlying(chialu.eda.conformance)`:
  `fp_alu_cmp` bit-exact in 29 s, `fp_alu_cmp_fpnew` in 26 s,
  `fp_alu_cmp_hardfloat` in 26 s, `fp_fma_alu` in 66 s.
* ADIR's own tests: 49 pass.
* On the EDA host: `domain_selftest` exits 0; the target suite
  (`pytest tests/test_targets.py -n 2 -q`: 108 cases, 85 pass, 22 skip, 1 xfail (`approx_alu`), 0 fail, exit 0, 22 min 35 s).

## Deferred

* The cross-index pin equality of `shared_across_formats` (the rounder,
  the unpacker, and `sharing` on the fp_fma families), registered as
  three `deferred` rules naming `pins_equal_across_sharing_modes`: an
  alias of the sharing modes' variables, in chiALU's
  `normalize_declaration` or in ADIR, would express it
  (`docs/adir_member_when_plan.md`). The former two deferred rules are
  member conditions now.
* A tight separate multiplier that normalizes its own product, which
  would admit `denormal_handling: in_datapath` under a separate
  multiplier.
* `indicator_restriction: positive_result_only` under the unswapped
  datapath with a single string (`add_sv` raises): a disjunction over
  two siblings, which one member condition does not state.
* A per-mode `x_form` (`modes[i].x_form`) for a unit that mixes a float
  mode with conversion ops and one without; the unit option covers the
  run files that exist.
* The rule-defect classification by `candidate.touched` (no region
  edited), which needs the conformance node to take a second input in
  every run file.
* The dot's geometry checks (a product count below a family's minimum, a
  window below the exact minimum) stay at render time; a predicate over
  the mode geometry would express them.
* `UNSUPPORTED_SFU_CHOICES` and the SFU's own render-time checks keep
  their table; the SFU is not pruned by this registry.
* The sequential dot contract: the fused families' behavior under
  `dot_contract: sequential` is not classified; the run files use `fused`.
* The inactivity of `subnormal_representation` under `bridge_fma` with
  `composition_style: bridge_reuse`, registered as a `deferred` rule
  naming `subnormal_representation_read_by_bridge`: it holds under two
  siblings' values on a variable four families share, which one `when`
  does not state (a per-family `when` on a union variable would). The
  `no_sr` rule narrows the shared variable under SR, which loses no
  design of the bridge, and the variant sweep rejects an explicit value
  through `alu_contracts`.
* The cascade of `bridge_fma` under `fma_contract: sequential` with
  `rounding: [RNE]` and `cascade_product_rounding: rne`, where the fixed
  product rounding coincides with the mode's: the rule excludes the
  member under every contract, as the fma-space line decided, and the
  separate multiplier then adder realize that contract.
