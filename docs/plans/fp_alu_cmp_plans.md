# `fp_alu_cmp_plans` — structures

target: `targets/eval/fp_alu_cmp_plans.yaml`  ·  structures: 24  ·  slotted: 24  ·  plans: 4  ·  free micro-architecture variables: 9

Every plan below shares this one manifest: `register_op` derives the structure set from the
mode's format and its op list alone, with no reference to any family choice, so sharing is the
only thing a plan varies.

| id | kind | slot | mode | lane | width | format | ops | library |
|---|---|---|---|---|---|---|---|---|
| `m0.l0.fp_adder` | fp_adder | fp_adder | 0 | 0 | 16 | `fp16` | fadd,fsub | yes |
| `m0.l0.unpacker` | unpacker | unpacker | 0 | 0 | 16 | `fp16` | fadd,fsub,fmul,fmin,fmax,fcmp | yes |
| `m0.l0.rounder` | rounder | rounder | 0 | 0 | 16 | `fp16` | fadd,fsub,fmul | yes |
| `m0.l0.fp_fma` | fp_fma | fp_fma | 0 | 0 | 16 | `fp16` | fadd,fsub,fmul | yes |
| `m0.l0.fp_multiplier` | fp_multiplier | fp_multiplier | 0 | 0 | 16 | `fp16` | fmul | yes |
| `m0.l0.fp_comparator` | fp_comparator | fp_comparator | 0 | 0 | 16 | `fp16` | fmin,fmax,fcmp | yes |
| `m1.l0.fp_adder` | fp_adder | fp_adder | 1 | 0 | 16 | `bf16` | fadd,fsub | yes |
| `m1.l0.unpacker` | unpacker | unpacker | 1 | 0 | 16 | `bf16` | fadd,fsub,fmul,fmin,fmax,fcmp | yes |
| `m1.l0.rounder` | rounder | rounder | 1 | 0 | 16 | `bf16` | fadd,fsub,fmul | yes |
| `m1.l0.fp_fma` | fp_fma | fp_fma | 1 | 0 | 16 | `bf16` | fadd,fsub,fmul | yes |
| `m1.l0.fp_multiplier` | fp_multiplier | fp_multiplier | 1 | 0 | 16 | `bf16` | fmul | yes |
| `m1.l0.fp_comparator` | fp_comparator | fp_comparator | 1 | 0 | 16 | `bf16` | fmin,fmax,fcmp | yes |
| `m2.l0.fp_adder` | fp_adder | fp_adder | 2 | 0 | 8 | `fp8e5m2` | fadd,fsub | yes |
| `m2.l1.fp_adder` | fp_adder | fp_adder | 2 | 1 | 8 | `fp8e5m2` | fadd,fsub | yes |
| `m2.l0.unpacker` | unpacker | unpacker | 2 | 0 | 8 | `fp8e5m2` | fadd,fsub,fmul,fmin,fmax,fcmp | yes |
| `m2.l0.rounder` | rounder | rounder | 2 | 0 | 8 | `fp8e5m2` | fadd,fsub,fmul | yes |
| `m2.l0.fp_fma` | fp_fma | fp_fma | 2 | 0 | 8 | `fp8e5m2` | fadd,fsub,fmul | yes |
| `m2.l1.unpacker` | unpacker | unpacker | 2 | 1 | 8 | `fp8e5m2` | fadd,fsub,fmul,fmin,fmax,fcmp | yes |
| `m2.l1.rounder` | rounder | rounder | 2 | 1 | 8 | `fp8e5m2` | fadd,fsub,fmul | yes |
| `m2.l1.fp_fma` | fp_fma | fp_fma | 2 | 1 | 8 | `fp8e5m2` | fadd,fsub,fmul | yes |
| `m2.l0.fp_multiplier` | fp_multiplier | fp_multiplier | 2 | 0 | 8 | `fp8e5m2` | fmul | yes |
| `m2.l1.fp_multiplier` | fp_multiplier | fp_multiplier | 2 | 1 | 8 | `fp8e5m2` | fmul | yes |
| `m2.l0.fp_comparator` | fp_comparator | fp_comparator | 2 | 0 | 8 | `fp8e5m2` | fmin,fmax,fcmp | yes |
| `m2.l1.fp_comparator` | fp_comparator | fp_comparator | 2 | 1 | 8 | `fp8e5m2` | fmin,fmax,fcmp | yes |

## Micro-architecture variables (free in every plan)

| variable | members |
|---|---|
| `core.fp_adder.m0.family` | single_path, two_path, delay_optimized_unified, low_power_gated |
| `core.fp_adder.m1.family` | single_path, two_path, delay_optimized_unified, low_power_gated |
| `core.fp_adder.m2.family` | single_path, two_path, delay_optimized_unified, low_power_gated |
| `core.fp_comparator.m0.family` | integer_compare_on_bits, dedicated_magnitude_comparator |
| `core.fp_comparator.m1.family` | integer_compare_on_bits, dedicated_magnitude_comparator |
| `core.fp_comparator.m2.family` | integer_compare_on_bits, dedicated_magnitude_comparator |
| `core.fp_multiplier.m0.family` | sig_mul_then_round, round_fused_in_reduction |
| `core.fp_multiplier.m1.family` | sig_mul_then_round, round_fused_in_reduction |
| `core.fp_multiplier.m2.family` | sig_mul_then_round, round_fused_in_reduction |

## Plans (4 of 4, evenly spread through the enumeration)

### `add-none_mul-none_log-none_pair-none_fmt-none`

units: 24  ·  shared groups: 0  ·  variables the plan pins: 0  ·  tied to a group representative: 0

No shared group: every structure is its own unit.

<details><summary>plan JSON</summary>

```json
{
  "shared": {},
  "structures": {},
  "why": "sharing scheme add-none_mul-none_log-none_pair-none_fmt-none: adders none, multipliers none, gate rows none, adder partner none, float sharing none"
}
```

</details>

### `add-none_mul-none_log-none_pair-none_fmt-stage`

units: 18  ·  shared groups: 2  ·  variables the plan pins: 6  ·  tied to a group representative: 0

| unit | members | kind | family the sharing requires |
|---|---|---|---|
| `rounders_across_formats` | `m0.l0.rounder`, `m1.l0.rounder`, `m2.l0.rounder`, `m2.l1.rounder` | rounder | shared_across_formats |
| `unpackers_across_formats` | `m0.l0.unpacker`, `m1.l0.unpacker`, `m2.l0.unpacker`, `m2.l1.unpacker` | unpacker | shared_across_formats |

<details><summary>variables the plan pins</summary>

```
core.rounder.m0.family = shared_across_formats
core.rounder.m1.family = shared_across_formats
core.rounder.m2.family = shared_across_formats
core.unpacker.m0.family = shared_across_formats
core.unpacker.m1.family = shared_across_formats
core.unpacker.m2.family = shared_across_formats
```

</details>

<details><summary>plan JSON</summary>

```json
{
  "shared": {
    "rounders_across_formats": {
      "family": "shared_across_formats",
      "members": [
        "m0.l0.rounder",
        "m1.l0.rounder",
        "m2.l0.rounder",
        "m2.l1.rounder"
      ],
      "why": "one rounder for every float format"
    },
    "unpackers_across_formats": {
      "family": "shared_across_formats",
      "members": [
        "m0.l0.unpacker",
        "m1.l0.unpacker",
        "m2.l0.unpacker",
        "m2.l1.unpacker"
      ],
      "why": "one unpacker for every float format"
    }
  },
  "structures": {},
  "why": "sharing scheme add-none_mul-none_log-none_pair-none_fmt-stage: adders none, multipliers none, gate rows none, adder partner none, float sharing stage"
}
```

</details>

### `add-none_mul-none_log-none_pair-none_fmt-arith`

units: 15  ·  shared groups: 3  ·  variables the plan pins: 0  ·  tied to a group representative: 6

| unit | members | kind | family the sharing requires |
|---|---|---|---|
| `fp_adders_across_formats` | `m0.l0.fp_adder`, `m1.l0.fp_adder`, `m2.l0.fp_adder`, `m2.l1.fp_adder` | fp_adder | — (a micro-architecture: one draw per group) |
| `fp_multipliers_across_formats` | `m0.l0.fp_multiplier`, `m1.l0.fp_multiplier`, `m2.l0.fp_multiplier`, `m2.l1.fp_multiplier` | fp_multiplier | — (a micro-architecture: one draw per group) |
| `fp_comparators_across_formats` | `m0.l0.fp_comparator`, `m1.l0.fp_comparator`, `m2.l0.fp_comparator`, `m2.l1.fp_comparator` | fp_comparator | — (a micro-architecture: one draw per group) |

<details><summary>plan JSON</summary>

```json
{
  "shared": {
    "fp_adders_across_formats": {
      "members": [
        "m0.l0.fp_adder",
        "m1.l0.fp_adder",
        "m2.l0.fp_adder",
        "m2.l1.fp_adder"
      ],
      "why": "one fp_adder for every float format, at the union geometry of their modes"
    },
    "fp_comparators_across_formats": {
      "members": [
        "m0.l0.fp_comparator",
        "m1.l0.fp_comparator",
        "m2.l0.fp_comparator",
        "m2.l1.fp_comparator"
      ],
      "why": "one fp_comparator for every float format, at the union geometry of their modes"
    },
    "fp_multipliers_across_formats": {
      "members": [
        "m0.l0.fp_multiplier",
        "m1.l0.fp_multiplier",
        "m2.l0.fp_multiplier",
        "m2.l1.fp_multiplier"
      ],
      "why": "one fp_multiplier for every float format, at the union geometry of their modes"
    }
  },
  "structures": {},
  "why": "sharing scheme add-none_mul-none_log-none_pair-none_fmt-arith: adders none, multipliers none, gate rows none, adder partner none, float sharing arith"
}
```

</details>

### `add-none_mul-none_log-none_pair-none_fmt-all`

units: 9  ·  shared groups: 5  ·  variables the plan pins: 6  ·  tied to a group representative: 6

| unit | members | kind | family the sharing requires |
|---|---|---|---|
| `rounders_across_formats` | `m0.l0.rounder`, `m1.l0.rounder`, `m2.l0.rounder`, `m2.l1.rounder` | rounder | shared_across_formats |
| `unpackers_across_formats` | `m0.l0.unpacker`, `m1.l0.unpacker`, `m2.l0.unpacker`, `m2.l1.unpacker` | unpacker | shared_across_formats |
| `fp_adders_across_formats` | `m0.l0.fp_adder`, `m1.l0.fp_adder`, `m2.l0.fp_adder`, `m2.l1.fp_adder` | fp_adder | — (a micro-architecture: one draw per group) |
| `fp_multipliers_across_formats` | `m0.l0.fp_multiplier`, `m1.l0.fp_multiplier`, `m2.l0.fp_multiplier`, `m2.l1.fp_multiplier` | fp_multiplier | — (a micro-architecture: one draw per group) |
| `fp_comparators_across_formats` | `m0.l0.fp_comparator`, `m1.l0.fp_comparator`, `m2.l0.fp_comparator`, `m2.l1.fp_comparator` | fp_comparator | — (a micro-architecture: one draw per group) |

<details><summary>variables the plan pins</summary>

```
core.rounder.m0.family = shared_across_formats
core.rounder.m1.family = shared_across_formats
core.rounder.m2.family = shared_across_formats
core.unpacker.m0.family = shared_across_formats
core.unpacker.m1.family = shared_across_formats
core.unpacker.m2.family = shared_across_formats
```

</details>

<details><summary>plan JSON</summary>

```json
{
  "shared": {
    "fp_adders_across_formats": {
      "members": [
        "m0.l0.fp_adder",
        "m1.l0.fp_adder",
        "m2.l0.fp_adder",
        "m2.l1.fp_adder"
      ],
      "why": "one fp_adder for every float format, at the union geometry of their modes"
    },
    "fp_comparators_across_formats": {
      "members": [
        "m0.l0.fp_comparator",
        "m1.l0.fp_comparator",
        "m2.l0.fp_comparator",
        "m2.l1.fp_comparator"
      ],
      "why": "one fp_comparator for every float format, at the union geometry of their modes"
    },
    "fp_multipliers_across_formats": {
      "members": [
        "m0.l0.fp_multiplier",
        "m1.l0.fp_multiplier",
        "m2.l0.fp_multiplier",
        "m2.l1.fp_multiplier"
      ],
      "why": "one fp_multiplier for every float format, at the union geometry of their modes"
    },
    "rounders_across_formats": {
      "family": "shared_across_formats",
      "members": [
        "m0.l0.rounder",
        "m1.l0.rounder",
        "m2.l0.rounder",
        "m2.l1.rounder"
      ],
      "why": "one rounder for every float format"
    },
    "unpackers_across_formats": {
      "family": "shared_across_formats",
      "members": [
        "m0.l0.unpacker",
        "m1.l0.unpacker",
        "m2.l0.unpacker",
        "m2.l1.unpacker"
      ],
      "why": "one unpacker for every float format"
    }
  },
  "structures": {},
  "why": "sharing scheme add-none_mul-none_log-none_pair-none_fmt-all: adders none, multipliers none, gate rows none, adder partner none, float sharing all"
}
```

</details>

