# `mixed_cvt_alu` — structures

target: `targets/mixed_cvt_alu.yaml`  ·  structures: 32  ·  slotted: 32  ·  plans: 64  ·  free micro-architecture variables: 11

Every plan below shares this one manifest: `register_op` derives the structure set from the
mode's format and its op list alone, with no reference to any family choice, so sharing is the
only thing a plan varies.

| id | kind | slot | mode | lane | width | format | ops | library |
|---|---|---|---|---|---|---|---|---|
| `m0.l0.fp_adder` | fp_adder | fp_adder | 0 | 0 | 16 | `fp16` | fadd | yes |
| `m0.l0.unpacker` | unpacker | unpacker | 0 | 0 | 16 | `fp16` | fadd,fmul,cvt(int8),cvt(fp16),cvt(fxs1i7f8) | yes |
| `m0.l0.rounder` | rounder | rounder | 0 | 0 | 16 | `fp16` | fadd,fmul,cvt(int8),cvt(fp16),cvt(fxs1i7f8) | yes |
| `m0.l0.fp_fma` | fp_fma | fp_fma | 0 | 0 | 16 | `fp16` | fadd,fmul | yes |
| `m0.l0.fp_multiplier` | fp_multiplier | fp_multiplier | 0 | 0 | 16 | `fp16` | fmul | yes |
| `m0.l0.converter.int8_twos_complement` | converter | converter | 0 | 0 | 16 | `fp16` | cvt(int8) | yes |
| `m0.l0.converter.fp16` | converter | converter | 0 | 0 | 16 | `fp16` | cvt(fp16) | yes |
| `m0.l0.converter.fxs1i7f8` | converter | converter | 0 | 0 | 16 | `fp16` | cvt(fxs1i7f8) | yes |
| `m1.l0.adder` | adder | adder | 1 | 0 | 16 | `int16_twos_complement` | add | yes |
| `m1.l0.multiplier` | multiplier | multiplier | 1 | 0 | 16 | `int16_twos_complement` | mul | yes |
| `m1.l0.comparator` | comparator | comparator | 1 | 0 | 16 | `int16_twos_complement` | min | yes |
| `m1.l0.converter.int8_twos_complement` | converter | converter | 1 | 0 | 16 | `int16_twos_complement` | cvt(int8) | yes |
| `m1.l0.converter.fp16` | converter | converter | 1 | 0 | 16 | `int16_twos_complement` | cvt(fp16) | yes |
| `m1.l0.converter.fxs1i7f8` | converter | converter | 1 | 0 | 16 | `int16_twos_complement` | cvt(fxs1i7f8) | yes |
| `m2.l0.adder` | adder | adder | 2 | 0 | 8 | `int8_twos_complement` | add | yes |
| `m2.l1.adder` | adder | adder | 2 | 1 | 8 | `int8_twos_complement` | add | yes |
| `m2.l0.multiplier` | multiplier | multiplier | 2 | 0 | 8 | `int8_twos_complement` | mul | yes |
| `m2.l1.multiplier` | multiplier | multiplier | 2 | 1 | 8 | `int8_twos_complement` | mul | yes |
| `m2.l0.comparator` | comparator | comparator | 2 | 0 | 8 | `int8_twos_complement` | min | yes |
| `m2.l1.comparator` | comparator | comparator | 2 | 1 | 8 | `int8_twos_complement` | min | yes |
| `m2.l0.converter.int8_twos_complement` | converter | converter | 2 | 0 | 8 | `int8_twos_complement` | cvt(int8) | yes |
| `m2.l1.converter.int8_twos_complement` | converter | converter | 2 | 1 | 8 | `int8_twos_complement` | cvt(int8) | yes |
| `m2.l0.converter.fp16` | converter | converter | 2 | 0 | 8 | `int8_twos_complement` | cvt(fp16) | yes |
| `m2.l1.converter.fp16` | converter | converter | 2 | 1 | 8 | `int8_twos_complement` | cvt(fp16) | yes |
| `m2.l0.converter.fxs1i7f8` | converter | converter | 2 | 0 | 8 | `int8_twos_complement` | cvt(fxs1i7f8) | yes |
| `m2.l1.converter.fxs1i7f8` | converter | converter | 2 | 1 | 8 | `int8_twos_complement` | cvt(fxs1i7f8) | yes |
| `m3.l0.adder` | adder | adder | 3 | 0 | 16 | `fxs1i7f8` | add | yes |
| `m3.l0.multiplier` | multiplier | multiplier | 3 | 0 | 16 | `fxs1i7f8` | mul | yes |
| `m3.l0.comparator` | comparator | comparator | 3 | 0 | 16 | `fxs1i7f8` | min | yes |
| `m3.l0.converter.int8_twos_complement` | converter | converter | 3 | 0 | 16 | `fxs1i7f8` | cvt(int8) | yes |
| `m3.l0.converter.fp16` | converter | converter | 3 | 0 | 16 | `fxs1i7f8` | cvt(fp16) | yes |
| `m3.l0.converter.fxs1i7f8` | converter | converter | 3 | 0 | 16 | `fxs1i7f8` | cvt(fxs1i7f8) | yes |

## Micro-architecture variables (free in every plan)

| variable | members |
|---|---|
| `core.adder.m1.family` | ripple_carry, manchester_carry_chain, carry_lookahead, carry_skip, carry_select, conditional_sum, carry_increment, parallel_prefix, sparse_prefix_hybrid, ling_prefix, compound_flagged_prefix, end_around_carry, prefix_synthesis_nonuniform_arrival, fpga_carry_chain |
| `core.adder.m2.family` | ripple_carry, manchester_carry_chain, carry_lookahead, carry_skip, carry_select, conditional_sum, carry_increment, parallel_prefix, sparse_prefix_hybrid, ling_prefix, compound_flagged_prefix, end_around_carry, prefix_synthesis_nonuniform_arrival, fpga_carry_chain |
| `core.adder.m3.family` | ripple_carry, manchester_carry_chain, carry_lookahead, carry_skip, carry_select, conditional_sum, carry_increment, parallel_prefix, sparse_prefix_hybrid, ling_prefix, compound_flagged_prefix, end_around_carry, prefix_synthesis_nonuniform_arrival, fpga_carry_chain |
| `core.comparator.m1.family` | prefix_comparator, subtractor_comparator |
| `core.comparator.m2.family` | prefix_comparator, subtractor_comparator |
| `core.comparator.m3.family` | prefix_comparator, subtractor_comparator |
| `core.fp_adder.m0.family` | single_path, two_path, delay_optimized_unified, low_power_gated |
| `core.fp_multiplier.m0.family` | sig_mul_then_round, round_fused_in_reduction |
| `core.multiplier.m1.family` | behavioral_star, booth_recoded_parallel, direct_pp_parallel, carry_save_array, recursive_karatsuba, squarer, segmented_grid, redundant_binary_multiplier |
| `core.multiplier.m2.family` | behavioral_star, booth_recoded_parallel, direct_pp_parallel, carry_save_array, recursive_karatsuba, squarer, segmented_grid, redundant_binary_multiplier |
| `core.multiplier.m3.family` | behavioral_star, booth_recoded_parallel, direct_pp_parallel, carry_save_array, recursive_karatsuba, squarer, segmented_grid, redundant_binary_multiplier |

## Plans (8 of 64, evenly spread through the enumeration)

### `add-none_mul-none_log-none_pair-none_fmt-none_intfp-none_sw-pcc`

units: 32  ·  shared groups: 0  ·  variables the plan pins: 0  ·  tied to a group representative: 0

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
  "why": "sharing scheme add-none_mul-none_log-none_pair-none_fmt-none_intfp-none_sw-pcc: adders none, multipliers none, gate rows none, adder partner none, float sharing none, float adders in the integer bank none, subword partitioned_carry_chain"
}
```

</details>

### `add-none_mul-all_log-none_pair-none_fmt-none_intfp-all_sw-pcc`

units: 28  ·  shared groups: 2  ·  variables the plan pins: 3  ·  tied to a group representative: 3

| unit | members | kind | family the sharing requires |
|---|---|---|---|
| `adders_0` | `m1.l0.adder`, `m0.l0.fp_adder` | adder, fp_adder | — (a micro-architecture: one draw per group) |
| `multipliers_0` | `m1.l0.multiplier`, `m2.l0.multiplier`, `m2.l1.multiplier`, `m3.l0.multiplier` | multiplier | twin_precision_subword |

<details><summary>variables the plan pins</summary>

```
core.multiplier.m1.family = twin_precision_subword
core.multiplier.m2.family = twin_precision_subword
core.multiplier.m3.family = twin_precision_subword
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
        "m1.l0.adder",
        "m0.l0.fp_adder"
      ],
      "why": "one lane-partitioned adder for these lanes, its width the float significand add's, which the float adder takes through ports"
    },
    "multipliers_0": {
      "family": "twin_precision_subword",
      "members": [
        "m1.l0.multiplier",
        "m2.l0.multiplier",
        "m2.l1.multiplier",
        "m3.l0.multiplier"
      ],
      "why": "one gated twin-precision matrix for these lanes"
    }
  },
  "structures": {},
  "why": "sharing scheme add-none_mul-all_log-none_pair-none_fmt-none_intfp-all_sw-pcc: adders none, multipliers all, gate rows none, adder partner none, float sharing none, float adders in the integer bank all, subword partitioned_carry_chain"
}
```

</details>

### `add-none_mul-per_mode_log-none_pair-comparator_fmt-none_intfp-none_sw-rep`

units: 27  ·  shared groups: 5  ·  variables the plan pins: 2  ·  tied to a group representative: 4

| unit | members | kind | family the sharing requires |
|---|---|---|---|
| `multipliers_0` | `m2.l0.multiplier`, `m2.l1.multiplier` | multiplier | twin_precision_subword |
| `pair_m1_l0` | `m1.l0.adder`, `m1.l0.comparator` | adder, comparator | — (a micro-architecture: one draw per group) |
| `pair_m2_l0` | `m2.l0.adder`, `m2.l0.comparator` | adder, comparator | — (a micro-architecture: one draw per group) |
| `pair_m2_l1` | `m2.l1.adder`, `m2.l1.comparator` | adder, comparator | — (a micro-architecture: one draw per group) |
| `pair_m3_l0` | `m3.l0.adder`, `m3.l0.comparator` | adder, comparator | — (a micro-architecture: one draw per group) |

<details><summary>variables the plan pins</summary>

```
core.multiplier.m2.family = twin_precision_subword
core.subword.family = replicated_lanes
```

</details>

<details><summary>plan JSON</summary>

```json
{
  "components": {
    "subword": {
      "family": "replicated_lanes"
    }
  },
  "shared": {
    "multipliers_0": {
      "family": "twin_precision_subword",
      "members": [
        "m2.l0.multiplier",
        "m2.l1.multiplier"
      ],
      "why": "one gated twin-precision matrix for these lanes"
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
    },
    "pair_m3_l0": {
      "members": [
        "m3.l0.adder",
        "m3.l0.comparator"
      ],
      "why": "the comparator rides the adder's subtractor"
    }
  },
  "structures": {},
  "why": "sharing scheme add-none_mul-per_mode_log-none_pair-comparator_fmt-none_intfp-none_sw-rep: adders none, multipliers per_mode, gate rows none, adder partner comparator, float sharing none, float adders in the integer bank none, subword replicated_lanes"
}
```

</details>

### `add-all_mul-none_log-none_pair-none_fmt-none_intfp-none_sw-pcc`

units: 29  ·  shared groups: 1  ·  variables the plan pins: 0  ·  tied to a group representative: 2

| unit | members | kind | family the sharing requires |
|---|---|---|---|
| `adders_0` | `m1.l0.adder`, `m2.l0.adder`, `m2.l1.adder`, `m3.l0.adder` | adder | — (a micro-architecture: one draw per group) |

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
        "m1.l0.adder",
        "m2.l0.adder",
        "m2.l1.adder",
        "m3.l0.adder"
      ],
      "why": "one lane-partitioned adder for these lanes"
    }
  },
  "structures": {},
  "why": "sharing scheme add-all_mul-none_log-none_pair-none_fmt-none_intfp-none_sw-pcc: adders all, multipliers none, gate rows none, adder partner none, float sharing none, float adders in the integer bank none, subword partitioned_carry_chain"
}
```

</details>

### `add-per_mode_mul-none_log-none_pair-none_fmt-none_intfp-none_sw-pcc`

units: 31  ·  shared groups: 1  ·  variables the plan pins: 0  ·  tied to a group representative: 1

| unit | members | kind | family the sharing requires |
|---|---|---|---|
| `adders_0` | `m2.l0.adder`, `m2.l1.adder` | adder | — (a micro-architecture: one draw per group) |

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
    }
  },
  "structures": {},
  "why": "sharing scheme add-per_mode_mul-none_log-none_pair-none_fmt-none_intfp-none_sw-pcc: adders per_mode, multipliers none, gate rows none, adder partner none, float sharing none, float adders in the integer bank none, subword partitioned_carry_chain"
}
```

</details>

### `add-per_mode_mul-per_mode_log-none_pair-none_fmt-none_intfp-none_sw-pcc`

units: 30  ·  shared groups: 2  ·  variables the plan pins: 1  ·  tied to a group representative: 2

| unit | members | kind | family the sharing requires |
|---|---|---|---|
| `adders_0` | `m2.l0.adder`, `m2.l1.adder` | adder | — (a micro-architecture: one draw per group) |
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
  "why": "sharing scheme add-per_mode_mul-per_mode_log-none_pair-none_fmt-none_intfp-none_sw-pcc: adders per_mode, multipliers per_mode, gate rows none, adder partner none, float sharing none, float adders in the integer bank none, subword partitioned_carry_chain"
}
```

</details>

### `add-per_lane_mul-none_log-none_pair-none_fmt-none_intfp-none_sw-pcc`

units: 30  ·  shared groups: 1  ·  variables the plan pins: 0  ·  tied to a group representative: 2

| unit | members | kind | family the sharing requires |
|---|---|---|---|
| `adders_0` | `m1.l0.adder`, `m2.l0.adder`, `m3.l0.adder` | adder | — (a micro-architecture: one draw per group) |

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
        "m1.l0.adder",
        "m2.l0.adder",
        "m3.l0.adder"
      ],
      "why": "one lane-partitioned adder for these lanes"
    }
  },
  "structures": {},
  "why": "sharing scheme add-per_lane_mul-none_log-none_pair-none_fmt-none_intfp-none_sw-pcc: adders per_lane, multipliers none, gate rows none, adder partner none, float sharing none, float adders in the integer bank none, subword partitioned_carry_chain"
}
```

</details>

### `add-per_lane_mul-per_lane_log-none_pair-comparator_fmt-none_intfp-all_sw-pcc`

units: 26  ·  shared groups: 3  ·  variables the plan pins: 3  ·  tied to a group representative: 6

| unit | members | kind | family the sharing requires |
|---|---|---|---|
| `adders_0` | `m1.l0.adder`, `m2.l0.adder`, `m3.l0.adder`, `m0.l0.fp_adder` | adder, fp_adder | — (a micro-architecture: one draw per group) |
| `multipliers_0` | `m1.l0.multiplier`, `m2.l0.multiplier`, `m3.l0.multiplier` | multiplier | twin_precision_subword |
| `pair_m2_l1` | `m2.l1.adder`, `m2.l1.comparator` | adder, comparator | — (a micro-architecture: one draw per group) |

<details><summary>variables the plan pins</summary>

```
core.multiplier.m1.family = twin_precision_subword
core.multiplier.m2.family = twin_precision_subword
core.multiplier.m3.family = twin_precision_subword
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
        "m1.l0.adder",
        "m2.l0.adder",
        "m3.l0.adder",
        "m0.l0.fp_adder"
      ],
      "why": "one lane-partitioned adder for these lanes, its width the float significand add's, which the float adder takes through ports"
    },
    "multipliers_0": {
      "family": "twin_precision_subword",
      "members": [
        "m1.l0.multiplier",
        "m2.l0.multiplier",
        "m3.l0.multiplier"
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
  "why": "sharing scheme add-per_lane_mul-per_lane_log-none_pair-comparator_fmt-none_intfp-all_sw-pcc: adders per_lane, multipliers per_lane, gate rows none, adder partner comparator, float sharing none, float adders in the integer bank all, subword partitioned_carry_chain"
}
```

</details>

