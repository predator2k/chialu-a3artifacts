# Complete variant coverage

The acceptance scope includes every legal complete pin binding, including every member of each `Range`. The database's baseline and single-choice enumeration does not establish this coverage.

The current acceptance requires faithful generation and simulation of the ALU, VecDotAcc and VecSFU seeds. Formal runs are deferred. A requested family must occur in the reachable circuit. A requested size must fit the component that uses it without clipping, and a sharing choice must construct a physical shared datapath. For example, an 8-bit circuit cannot cover a 16-bit block choice. A copied pin dictionary or identical RTL does not establish that a parameter takes effect.

`chialu.variant_contracts` rejects explicit inactive pins and validates declared domains. Its projection of an old Cartesian binding removes inactive axes; projected aliases cannot count as distinct exercised constructions. The geometry hooks in the ALU, dot and SFU family modules supply lower bounds for target selection. These bounds require checks at each nested component's actual geometry before a target can count as coverage.

`chialu.variants` indexes the declared products with arbitrary-size integer ordinals. A slot includes every family in its domain and every binding under the selected family. Rank and unrank preserve complete bindings. Shards partition ordinals without sampling. An unhandled domain, recursive schema or forbidden predicate raises an error. The index keeps distinct schemas even when their family names match.

`chialu.active_variants` indexes each conditional active product before semantic and geometry legality. `variant_selftest` uses this index by default. `--index raw` selects the older Cartesian ordinals. Active and raw products have different fingerprints, so their coverage records cannot share ordinal meanings. Carry select has 185,472 active bindings and 1,775,520 raw bindings in the current schema. The difference consists of inactive aliases.

```sh
python3 -m chialu.variants --kinds adder --families carry_skip --ordinal 0
python3 -m chialu.active_variants --kinds adder --families carry_select --ordinal 0
```

`chialu.verify.variant_selftest` generates native RTL and compares it with Python golden files. An available ALU or dot fixture also checks the generated seed through its pattern ports. Dot fixtures bind a geometry compatible with the family, including single-product FMA, two-product dot and block formats. The result records that geometry. The `--formal` option additionally requires a native formal proof. A missing contract, rejected generator, unavailable geometry or solver timeout leaves the point unproved. An unsupported floating width cannot inherit the characterizer's fp16 fallback and count as verified.

```sh
python3 -m chialu.verify.variant_selftest \
  --kinds adder --families ripple_carry --widths 8,16 \
  --out /tmp/chialu-variants
```

`--start`, `--stop`, `--shard` and `--shards` select work within a complete product. `--limit` bounds new work. These options do not reduce the acceptance denominator. An incomplete report returns a failing exit status. `--retry-unproved` revisits failures and missing proofs. `--report-only` reads the accumulated results.

`coverage.sqlite3` stores ordinals as decimal strings and preserves separate generation and golden results. Source and tool changes invalidate old scope records. Native evidence can be shared when the complete emitted source, parameters, compiled reference and verification settings agree. The seed has a separate check and cache. The synthesis database and its row schema remain unchanged.

The legacy ledger's `complete` field reports functional coverage. Its separate `fidelity_complete` field also requires an explicit parameter-effect result for every legal point. Existing functional records do not acquire that result automatically. The simulation report retains the RTL, stimulus and expected-file hashes, plus the generator's parameter and sharing records. `chialu.verify.elaboration` additionally reads actual module parameters and port widths from Verilator's compiled hierarchy.

The ripple-carry regression exercises all 128 complete bindings at width 32, including every chunk size from 1 through 32 and all four full-adder forms. Its Verilator hierarchy check verifies every chunk's width, input width and selected form. Width 32 is the minimum target width for this family's entire declared chunk range. This result concerns that family and geometry, not the complete library.

SFU precision targets govern implementation search and unresolved parameter search. An omitted target uses 1 ULP. A fixed implementation whose parameters determine its error range reports that range without applying the user's budget. Complete-domain simulation currently supplies this range for small input products. Sampling supplies measured maxima only; it cannot complete this branch. Independent algorithm verification and structural fidelity remain separate requirements. Dot architecture contracts retain their exact algorithm check and any explicit mathematical budget.

```sh
python3 -m chialu.verify.ripple_fidelity_selftest --out /tmp/chialu-ripple --jobs 4
```

## Component substitution

`carry_skip`, `carry_select`, `carry_increment` and `sparse_prefix_hybrid` use explicit templates for their parent circuits. A template accepts only its own choices. Its component interfaces identify the slot, arithmetic kind and actual width. The ordinary RTL generator resolves those interfaces with the selected child families and pins. The proof generator resolves the same interfaces with their Python arithmetic contracts.

The composition check performs these obligations:

* Every legal combination of the parent's own choices gets a parent-circuit proof.
* Every child binding gets a proof at every width where the parent can instantiate it.
* Every parent binding requires the intersection of its child's width proofs. Proof at one width does not cover another width.
* Independent slots contribute a Cartesian product. An unused slot contributes all its bindings to the older functional-equivalence count. That count does not satisfy the current parameter-effect criterion. The active branch must omit that slot, and an explicit selection of the inactive slot must fail.
* A missing child proof contributes no coverage to combinations that require it.

```sh
python3 -m chialu.verify.composition_selftest \
  --widths 8,16 --jobs 4 --out /tmp/chialu-composition

python3 -m chialu.verify.composition_selftest \
  --out /tmp/chialu-composition \
  --check-report /tmp/chialu-composition/carry_skip/w8/report.json
```

The report checker reconstructs the declared bindings and proof obligations. It checks the circuit hashes, saved sources, solver results and coverage counts. The proof directories retain `miter.sv`, `miter.v`, `prove.ys`, `yosys.log` and Python-generated simulation files. A failed SAT proof also retains a counterexample. Existing reports remain evidence for their recorded functional contracts and source revisions; they do not certify the newer parameter-effect criterion.

`chialu.verify.symbolic` executes the integer Python reference with bounded symbolic inputs. Conditional paths become guarded expressions. Failed Python assertions leave a path undefined. The SAT check requires the reference to be defined and every output to agree on every admitted input. Intermediate bounds prevent truncation in the generated proof expressions. Unsupported Python operations remain unproved. Approximate error bounds and floating internal contracts currently need additional proof implementations.

`chialu.variant_legality` contains explicit restrictions from the existing space descriptions. Prefix valency restrictions and the modulus-width restriction have named reasons. A generator exception, numerical mismatch or timeout does not create an exclusion.

The current `VecDotAcc` contract also excludes the following unsupported operation choices, as requested. These choices previously selected the ordinary product implementation without implementing their declared operation.

| Family | Pin | Unsupported value |
| --- | --- | --- |
| `integer_mac` | `element_op` | `absolute_difference` |
| `multi_term_fused_dot` | `term_source` | `fp_operands` |
| `fused_two_term_dot` | `second_op` | `add_subtract_pair` |

The exclusion report lists removed operation and sequential domains. A domain removed from the public space has no current-product cardinality; its report preserves the removed values or range explicitly:

```sh
python3 -m chialu.variant_legality --out /tmp/chialu-unsupported-choices.json
```

## Seed selection

An explicit ALU family selection must generate a module reachable from the seed's top. The selection check preserves the requested structure owner and pins, so a module generated for another mode cannot satisfy the request. The two registered inline families have explicit owner checks. Dot and SFU selections raise an error when their requested implementation cannot be generated. Dot operation pins that the product contract does not express are rejected instead of being substituted with products. These checks also apply through `chialu.targets.derive`.

The float seed preserves the IEEE sign of an exact-zero arithmetic result after generic packing. The zero-sign regression checks both behavioral and selected-family seeds on fp8e4m3, fp16, bf16 and fp32.

The twin-precision matrix also has a binary component wrapper that selects its full-width packing. A multiplier component can use this wrapper without a mode-selector port.

The library dependency collector omits static modules already present in the supplied source. This permits a component template to carry its dependencies without duplicating their definitions during the yosys frontend conversion.

The dot window ignores zero terms when choosing its largest exponent. A zero product therefore cannot discard a small nonzero addend. Signed window words are emitted once and reused by subsequent accumulation stages, which prevents duplicate declarations in tensor-core configurations.

## Remaining acceptance work

The full-library acceptance criterion remains unmet. The component proof implementation currently covers the four blocked-adder families above. Native formal support currently covers integer references that the symbolic executor can compile. Other families still need compositional contracts, generation fixes or native reference adapters. Approximate component compositions, internal floating outputs, posit units, dot variants, SFU variants and checker variants are not certified by the blocked-adder reports.

A report certifies its named family schemas and geometries. A native component proof does not establish every ALU sharing configuration or every format geometry. The whole-library claim requires these remaining scopes to have coverage records with no unvisited or unproved legal combinations.

The regression checks for the coverage machinery are:

```sh
python3 -m chialu.verify.variants_selftest
python3 -m chialu.verify.variant_coverage_selftest
python3 -m chialu.verify.composition_coverage_selftest
python3 -m chialu.verify.formal_selftest
python3 -m chialu.verify.seed_selection_selftest
python3 -m chialu.verify.float_seed_selftest
```
