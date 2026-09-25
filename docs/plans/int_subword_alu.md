# `int_subword_alu` — structures

target: `targets/int_subword_alu.yaml`  ·  structures: 24  ·  slotted: 24  ·  plans: 144  ·  free micro-architecture variables: 18

Every plan below shares this one manifest: `register_op` derives the structure set from the
mode's format and its op list alone, with no reference to any family choice, so sharing is the
only thing a plan varies.

| id | kind | slot | mode | lane | width | format | ops | library |
|---|---|---|---|---|---|---|---|---|
| `m0.l0.adder` | adder | adder | 0 | 0 | 16 | `int16_twos_complement` | add,sub,adc,neg,abs,add_sat | yes |
| `m0.l0.multiplier` | multiplier | multiplier | 0 | 0 | 16 | `int16_twos_complement` | mul,mul_high | yes |
| `m0.l0.comparator` | comparator | comparator | 0 | 0 | 16 | `int16_twos_complement` | min,max,cmp | yes |
| `m0.l0.shifter` | shifter | shifter | 0 | 0 | 16 | `int16_twos_complement` | shl,shr_arith,rol | yes |
| `m0.l0.logic` | logic | logic | 0 | 0 | 16 | `int16_twos_complement` | and,or,xor,not | yes |
| `m0.l0.bitcount` | bitcount | bitcount | 0 | 0 | 16 | `int16_twos_complement` | popcount,clz,ctz | yes |
| `m1.l0.adder` | adder | adder | 1 | 0 | 16 | `int16_unsigned` | add,sub,adc,neg,abs,add_sat | yes |
| `m1.l0.multiplier` | multiplier | multiplier | 1 | 0 | 16 | `int16_unsigned` | mul,mul_high | yes |
| `m1.l0.comparator` | comparator | comparator | 1 | 0 | 16 | `int16_unsigned` | min,max,cmp | yes |
| `m1.l0.shifter` | shifter | shifter | 1 | 0 | 16 | `int16_unsigned` | shl,shr_arith,rol | yes |
| `m1.l0.logic` | logic | logic | 1 | 0 | 16 | `int16_unsigned` | and,or,xor,not | yes |
| `m1.l0.bitcount` | bitcount | bitcount | 1 | 0 | 16 | `int16_unsigned` | popcount,clz,ctz | yes |
| `m2.l0.adder` | adder | adder | 2 | 0 | 8 | `int8_twos_complement` | add,sub,adc,neg,abs,add_sat | yes |
| `m2.l1.adder` | adder | adder | 2 | 1 | 8 | `int8_twos_complement` | add,sub,adc,neg,abs,add_sat | yes |
| `m2.l0.multiplier` | multiplier | multiplier | 2 | 0 | 8 | `int8_twos_complement` | mul,mul_high | yes |
| `m2.l1.multiplier` | multiplier | multiplier | 2 | 1 | 8 | `int8_twos_complement` | mul,mul_high | yes |
| `m2.l0.comparator` | comparator | comparator | 2 | 0 | 8 | `int8_twos_complement` | min,max,cmp | yes |
| `m2.l1.comparator` | comparator | comparator | 2 | 1 | 8 | `int8_twos_complement` | min,max,cmp | yes |
| `m2.l0.shifter` | shifter | shifter | 2 | 0 | 8 | `int8_twos_complement` | shl,shr_arith,rol | yes |
| `m2.l1.shifter` | shifter | shifter | 2 | 1 | 8 | `int8_twos_complement` | shl,shr_arith,rol | yes |
| `m2.l0.logic` | logic | logic | 2 | 0 | 8 | `int8_twos_complement` | and,or,xor,not | yes |
| `m2.l1.logic` | logic | logic | 2 | 1 | 8 | `int8_twos_complement` | and,or,xor,not | yes |
| `m2.l0.bitcount` | bitcount | bitcount | 2 | 0 | 8 | `int8_twos_complement` | popcount,clz,ctz | yes |
| `m2.l1.bitcount` | bitcount | bitcount | 2 | 1 | 8 | `int8_twos_complement` | popcount,clz,ctz | yes |

## Micro-architecture variables (free in every plan)

| variable | members |
|---|---|
| `core.adder.m0.family` | ripple_carry, manchester_carry_chain, carry_lookahead, carry_skip, carry_select, conditional_sum, carry_increment, parallel_prefix, sparse_prefix_hybrid, ling_prefix, compound_flagged_prefix, end_around_carry, prefix_synthesis_nonuniform_arrival, fpga_carry_chain |
| `core.adder.m1.family` | ripple_carry, manchester_carry_chain, carry_lookahead, carry_skip, carry_select, conditional_sum, carry_increment, parallel_prefix, sparse_prefix_hybrid, ling_prefix, compound_flagged_prefix, end_around_carry, prefix_synthesis_nonuniform_arrival, fpga_carry_chain |
| `core.adder.m2.family` | ripple_carry, manchester_carry_chain, carry_lookahead, carry_skip, carry_select, conditional_sum, carry_increment, parallel_prefix, sparse_prefix_hybrid, ling_prefix, compound_flagged_prefix, end_around_carry, prefix_synthesis_nonuniform_arrival, fpga_carry_chain |
| `core.bitcount.m0.family` | popcount_counter_tree, lzd_cell_tree, trailing_zero, priority_encoder |
| `core.bitcount.m1.family` | popcount_counter_tree, lzd_cell_tree, trailing_zero, priority_encoder |
| `core.bitcount.m2.family` | popcount_counter_tree, lzd_cell_tree, trailing_zero, priority_encoder |
| `core.comparator.m0.family` | prefix_comparator, subtractor_comparator |
| `core.comparator.m1.family` | prefix_comparator, subtractor_comparator |
| `core.comparator.m2.family` | prefix_comparator, subtractor_comparator |
| `core.logic.m0.family` | lane_replicated_gates, alu_pg_fused |
| `core.logic.m1.family` | lane_replicated_gates, alu_pg_fused |
| `core.logic.m2.family` | lane_replicated_gates, alu_pg_fused |
| `core.multiplier.m0.family` | behavioral_star, booth_recoded_parallel, direct_pp_parallel, carry_save_array, recursive_karatsuba, squarer, segmented_grid, redundant_binary_multiplier |
| `core.multiplier.m1.family` | behavioral_star, booth_recoded_parallel, direct_pp_parallel, carry_save_array, recursive_karatsuba, squarer, segmented_grid, redundant_binary_multiplier |
| `core.multiplier.m2.family` | behavioral_star, booth_recoded_parallel, direct_pp_parallel, carry_save_array, recursive_karatsuba, squarer, segmented_grid, redundant_binary_multiplier |
| `core.shifter.m0.family` | barrel_mux_tree, funnel, masked_merged, butterfly_network |
| `core.shifter.m1.family` | barrel_mux_tree, funnel, masked_merged, butterfly_network |
| `core.shifter.m2.family` | barrel_mux_tree, funnel, masked_merged, butterfly_network |

## Plans (8 of 144, evenly spread through the enumeration)

### `add-none_mul-none_log-none_pair-none_fmt-none_sw-pcc`

units: 24  ·  shared groups: 0  ·  variables the plan pins: 0  ·  tied to a group representative: 0

No shared group: every structure is its own unit.

<details><summary>plan JSON</summary>

```json
{
  "components": {
    "subword": {
      "family": "partitioned_carry_chain"
    }
  },
  "shared": {},
  "structures": {},
  "why": "sharing scheme add-none_mul-none_log-none_pair-none_fmt-none_sw-pcc: adders none, multipliers none, gate rows none, adder partner none, float sharing none, subword partitioned_carry_chain"
}
```

</details>

### `add-none_mul-all_log-none_pair-comparator_fmt-none_sw-pcc`

units: 17  ·  shared groups: 5  ·  variables the plan pins: 3  ·  tied to a group representative: 5

| unit | members | kind | family the sharing requires |
|---|---|---|---|
| `multipliers_0` | `m0.l0.multiplier`, `m1.l0.multiplier`, `m2.l0.multiplier`, `m2.l1.multiplier` | multiplier | twin_precision_subword |
| `pair_m0_l0` | `m0.l0.adder`, `m0.l0.comparator` | adder, comparator | — (a micro-architecture: one draw per group) |
| `pair_m1_l0` | `m1.l0.adder`, `m1.l0.comparator` | adder, comparator | — (a micro-architecture: one draw per group) |
| `pair_m2_l0` | `m2.l0.adder`, `m2.l0.comparator` | adder, comparator | — (a micro-architecture: one draw per group) |
| `pair_m2_l1` | `m2.l1.adder`, `m2.l1.comparator` | adder, comparator | — (a micro-architecture: one draw per group) |

<details><summary>variables the plan pins</summary>

```
core.multiplier.m0.family = twin_precision_subword
core.multiplier.m1.family = twin_precision_subword
core.multiplier.m2.family = twin_precision_subword
```

</details>

<details><summary>plan JSON</summary>

```json
{
  "components": {
    "subword": {
      "family": "partitioned_carry_chain"
    }
  },
  "shared": {
    "multipliers_0": {
      "family": "twin_precision_subword",
      "members": [
        "m0.l0.multiplier",
        "m1.l0.multiplier",
        "m2.l0.multiplier",
        "m2.l1.multiplier"
      ],
      "why": "one gated twin-precision matrix for these lanes"
    },
    "pair_m0_l0": {
      "members": [
        "m0.l0.adder",
        "m0.l0.comparator"
      ],
      "why": "the comparator rides the adder's subtractor"
    },
    "pair_m1_l0": {
      "members": [
        "m1.l0.adder",
        "m1.l0.comparator"
      ],
      "why": "the comparator rides the adder's subtractor"
    },
    "pair_m2_l0": {
      "members": [
        "m2.l0.adder",
        "m2.l0.comparator"
      ],
      "why": "the comparator rides the adder's subtractor"
    },
    "pair_m2_l1": {
      "members": [
        "m2.l1.adder",
        "m2.l1.comparator"
      ],
      "why": "the comparator rides the adder's subtractor"
    }
  },
  "structures": {},
  "why": "sharing scheme add-none_mul-all_log-none_pair-comparator_fmt-none_sw-pcc: adders none, multipliers all, gate rows none, adder partner comparator, float sharing none, subword partitioned_carry_chain"
}
```

</details>

### `add-none_mul-per_mode_log-all_pair-none_fmt-none_sw-pcc`

units: 20  ·  shared groups: 2  ·  variables the plan pins: 4  ·  tied to a group representative: 3

| unit | members | kind | family the sharing requires |
|---|---|---|---|
| `multipliers_0` | `m2.l0.multiplier`, `m2.l1.multiplier` | multiplier | twin_precision_subword |
| `gate_rows_0` | `m0.l0.logic`, `m1.l0.logic`, `m2.l0.logic`, `m2.l1.logic` | logic | wide_gate_row |

<details><summary>variables the plan pins</summary>

```
core.logic.m0.family = wide_gate_row
core.logic.m1.family = wide_gate_row
core.logic.m2.family = wide_gate_row
core.multiplier.m2.family = twin_precision_subword
```

</details>

<details><summary>plan JSON</summary>

```json
{
  "components": {
    "subword": {
      "family": "partitioned_carry_chain"
    }
  },
  "shared": {
    "gate_rows_0": {
      "family": "wide_gate_row",
      "members": [
        "m0.l0.logic",
        "m1.l0.logic",
        "m2.l0.logic",
        "m2.l1.logic"
      ],
      "why": "one gate row for these lanes"
    },
    "multipliers_0": {
      "family": "twin_precision_subword",
      "members": [
        "m2.l0.multiplier",
        "m2.l1.multiplier"
      ],
      "why": "one gated twin-precision matrix for these lanes"
    }
  },
  "structures": {},
  "why": "sharing scheme add-none_mul-per_mode_log-all_pair-none_fmt-none_sw-pcc: adders none, multipliers per_mode, gate rows all, adder partner none, float sharing none, subword partitioned_carry_chain"
}
```

</details>

### `add-none_mul-per_lane_log-all_pair-comparator_fmt-none_sw-pcc`

units: 15  ·  shared groups: 6  ·  variables the plan pins: 6  ·  tied to a group representative: 7

| unit | members | kind | family the sharing requires |
|---|---|---|---|
| `multipliers_0` | `m0.l0.multiplier`, `m1.l0.multiplier`, `m2.l0.multiplier` | multiplier | twin_precision_subword |
| `gate_rows_0` | `m0.l0.logic`, `m1.l0.logic`, `m2.l0.logic`, `m2.l1.logic` | logic | wide_gate_row |
| `pair_m0_l0` | `m0.l0.adder`, `m0.l0.comparator` | adder, comparator | — (a micro-architecture: one draw per group) |
| `pair_m1_l0` | `m1.l0.adder`, `m1.l0.comparator` | adder, comparator | — (a micro-architecture: one draw per group) |
| `pair_m2_l0` | `m2.l0.adder`, `m2.l0.comparator` | adder, comparator | — (a micro-architecture: one draw per group) |
| `pair_m2_l1` | `m2.l1.adder`, `m2.l1.comparator` | adder, comparator | — (a micro-architecture: one draw per group) |

<details><summary>variables the plan pins</summary>

```
core.logic.m0.family = wide_gate_row
core.logic.m1.family = wide_gate_row
core.logic.m2.family = wide_gate_row
core.multiplier.m0.family = twin_precision_subword
core.multiplier.m1.family = twin_precision_subword
core.multiplier.m2.family = twin_precision_subword
```

</details>

<details><summary>plan JSON</summary>

```json
{
  "components": {
    "subword": {
      "family": "partitioned_carry_chain"
    }
  },
  "shared": {
    "gate_rows_0": {
      "family": "wide_gate_row",
      "members": [
        "m0.l0.logic",
        "m1.l0.logic",
        "m2.l0.logic",
        "m2.l1.logic"
      ],
      "why": "one gate row for these lanes"
    },
    "multipliers_0": {
      "family": "twin_precision_subword",
      "members": [
        "m0.l0.multiplier",
        "m1.l0.multiplier",
        "m2.l0.multiplier"
      ],
      "why": "one gated twin-precision matrix for these lanes"
    },
    "pair_m0_l0": {
      "members": [
        "m0.l0.adder",
        "m0.l0.comparator"
      ],
      "why": "the comparator rides the adder's subtractor"
    },
    "pair_m1_l0": {
      "members": [
        "m1.l0.adder",
        "m1.l0.comparator"
      ],
      "why": "the comparator rides the adder's subtractor"
    },
    "pair_m2_l0": {
      "members": [
        "m2.l0.adder",
        "m2.l0.comparator"
      ],
      "why": "the comparator rides the adder's subtractor"
    },
    "pair_m2_l1": {
      "members": [
        "m2.l1.adder",
        "m2.l1.comparator"
      ],
      "why": "the comparator rides the adder's subtractor"
    }
  },
  "structures": {},
  "why": "sharing scheme add-none_mul-per_lane_log-all_pair-comparator_fmt-none_sw-pcc: adders none, multipliers per_lane, gate rows all, adder partner comparator, float sharing none, subword partitioned_carry_chain"
}
```

</details>

### `add-all_mul-per_mode_log-none_pair-none_fmt-none_sw-pcc`

units: 20  ·  shared groups: 2  ·  variables the plan pins: 1  ·  tied to a group representative: 3

| unit | members | kind | family the sharing requires |
|---|---|---|---|
| `adders_0` | `m0.l0.adder`, `m1.l0.adder`, `m2.l0.adder`, `m2.l1.adder` | adder | — (a micro-architecture: one draw per group) |
| `multipliers_0` | `m2.l0.multiplier`, `m2.l1.multiplier` | multiplier | twin_precision_subword |

<details><summary>variables the plan pins</summary>

```
core.multiplier.m2.family = twin_precision_subword
```

</details>

<details><summary>plan JSON</summary>

```json
{
  "components": {
    "subword": {
      "family": "partitioned_carry_chain"
    }
  },
  "shared": {
    "adders_0": {
      "members": [
        "m0.l0.adder",
        "m1.l0.adder",
        "m2.l0.adder",
        "m2.l1.adder"
      ],
      "why": "one lane-partitioned adder for these lanes"
    },
    "multipliers_0": {
      "family": "twin_precision_subword",
      "members": [
        "m2.l0.multiplier",
        "m2.l1.multiplier"
      ],
      "why": "one gated twin-precision matrix for these lanes"
    }
  },
  "structures": {},
  "why": "sharing scheme add-all_mul-per_mode_log-none_pair-none_fmt-none_sw-pcc: adders all, multipliers per_mode, gate rows none, adder partner none, float sharing none, subword partitioned_carry_chain"
}
```

</details>

### `add-per_mode_mul-all_log-all_pair-none_fmt-none_sw-pcc`

units: 17  ·  shared groups: 3  ·  variables the plan pins: 6  ·  tied to a group representative: 5

| unit | members | kind | family the sharing requires |
|---|---|---|---|
| `adders_0` | `m2.l0.adder`, `m2.l1.adder` | adder | — (a micro-architecture: one draw per group) |
| `multipliers_0` | `m0.l0.multiplier`, `m1.l0.multiplier`, `m2.l0.multiplier`, `m2.l1.multiplier` | multiplier | twin_precision_subword |
| `gate_rows_0` | `m0.l0.logic`, `m1.l0.logic`, `m2.l0.logic`, `m2.l1.logic` | logic | wide_gate_row |

<details><summary>variables the plan pins</summary>

```
core.logic.m0.family = wide_gate_row
core.logic.m1.family = wide_gate_row
core.logic.m2.family = wide_gate_row
core.multiplier.m0.family = twin_precision_subword
core.multiplier.m1.family = twin_precision_subword
core.multiplier.m2.family = twin_precision_subword
```

</details>

<details><summary>plan JSON</summary>

```json
{
  "components": {
    "subword": {
      "family": "partitioned_carry_chain"
    }
  },
  "shared": {
    "adders_0": {
      "members": [
        "m2.l0.adder",
        "m2.l1.adder"
      ],
      "why": "one lane-partitioned adder for these lanes"
    },
    "gate_rows_0": {
      "family": "wide_gate_row",
      "members": [
        "m0.l0.logic",
        "m1.l0.logic",
        "m2.l0.logic",
        "m2.l1.logic"
      ],
      "why": "one gate row for these lanes"
    },
    "multipliers_0": {
      "family": "twin_precision_subword",
      "members": [
        "m0.l0.multiplier",
        "m1.l0.multiplier",
        "m2.l0.multiplier",
        "m2.l1.multiplier"
      ],
      "why": "one gated twin-precision matrix for these lanes"
    }
  },
  "structures": {},
  "why": "sharing scheme add-per_mode_mul-all_log-all_pair-none_fmt-none_sw-pcc: adders per_mode, multipliers all, gate rows all, adder partner none, float sharing none, subword partitioned_carry_chain"
}
```

</details>

### `add-per_mode_mul-per_lane_log-per_mode_pair-none_fmt-none_sw-pcc`

units: 20  ·  shared groups: 3  ·  variables the plan pins: 4  ·  tied to a group representative: 4

| unit | members | kind | family the sharing requires |
|---|---|---|---|
| `adders_0` | `m2.l0.adder`, `m2.l1.adder` | adder | — (a micro-architecture: one draw per group) |
| `multipliers_0` | `m0.l0.multiplier`, `m1.l0.multiplier`, `m2.l0.multiplier` | multiplier | twin_precision_subword |
| `gate_rows_0` | `m2.l0.logic`, `m2.l1.logic` | logic | wide_gate_row |

<details><summary>variables the plan pins</summary>

```
core.logic.m2.family = wide_gate_row
core.multiplier.m0.family = twin_precision_subword
core.multiplier.m1.family = twin_precision_subword
core.multiplier.m2.family = twin_precision_subword
```

</details>

<details><summary>plan JSON</summary>

```json
{
  "components": {
    "subword": {
      "family": "partitioned_carry_chain"
    }
  },
  "shared": {
    "adders_0": {
      "members": [
        "m2.l0.adder",
        "m2.l1.adder"
      ],
      "why": "one lane-partitioned adder for these lanes"
    },
    "gate_rows_0": {
      "family": "wide_gate_row",
      "members": [
        "m2.l0.logic",
        "m2.l1.logic"
      ],
      "why": "one gate row for these lanes"
    },
    "multipliers_0": {
      "family": "twin_precision_subword",
      "members": [
        "m0.l0.multiplier",
        "m1.l0.multiplier",
        "m2.l0.multiplier"
      ],
      "why": "one gated twin-precision matrix for these lanes"
    }
  },
  "structures": {},
  "why": "sharing scheme add-per_mode_mul-per_lane_log-per_mode_pair-none_fmt-none_sw-pcc: adders per_mode, multipliers per_lane, gate rows per_mode, adder partner none, float sharing none, subword partitioned_carry_chain"
}
```

</details>

### `add-per_lane_mul-per_lane_log-per_lane_pair-comparator_fmt-none_sw-pcc`

units: 17  ·  shared groups: 4  ·  variables the plan pins: 6  ·  tied to a group representative: 7

| unit | members | kind | family the sharing requires |
|---|---|---|---|
| `adders_0` | `m0.l0.adder`, `m1.l0.adder`, `m2.l0.adder` | adder | — (a micro-architecture: one draw per group) |
| `multipliers_0` | `m0.l0.multiplier`, `m1.l0.multiplier`, `m2.l0.multiplier` | multiplier | twin_precision_subword |
| `gate_rows_0` | `m0.l0.logic`, `m1.l0.logic`, `m2.l0.logic` | logic | wide_gate_row |
| `pair_m2_l1` | `m2.l1.adder`, `m2.l1.comparator` | adder, comparator | — (a micro-architecture: one draw per group) |

<details><summary>variables the plan pins</summary>

```
core.logic.m0.family = wide_gate_row
core.logic.m1.family = wide_gate_row
core.logic.m2.family = wide_gate_row
core.multiplier.m0.family = twin_precision_subword
core.multiplier.m1.family = twin_precision_subword
core.multiplier.m2.family = twin_precision_subword
```

</details>

<details><summary>plan JSON</summary>

```json
{
  "components": {
    "subword": {
      "family": "partitioned_carry_chain"
    }
  },
  "shared": {
    "adders_0": {
      "members": [
        "m0.l0.adder",
        "m1.l0.adder",
        "m2.l0.adder"
      ],
      "why": "one lane-partitioned adder for these lanes"
    },
    "gate_rows_0": {
      "family": "wide_gate_row",
      "members": [
        "m0.l0.logic",
        "m1.l0.logic",
        "m2.l0.logic"
      ],
      "why": "one gate row for these lanes"
    },
    "multipliers_0": {
      "family": "twin_precision_subword",
      "members": [
        "m0.l0.multiplier",
        "m1.l0.multiplier",
        "m2.l0.multiplier"
      ],
      "why": "one gated twin-precision matrix for these lanes"
    },
    "pair_m2_l1": {
      "members": [
        "m2.l1.adder",
        "m2.l1.comparator"
      ],
      "why": "the comparator rides the adder's subtractor"
    }
  },
  "structures": {},
  "why": "sharing scheme add-per_lane_mul-per_lane_log-per_lane_pair-comparator_fmt-none_sw-pcc: adders per_lane, multipliers per_lane, gate rows per_lane, adder partner comparator, float sharing none, subword partitioned_carry_chain"
}
```

</details>

