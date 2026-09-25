# add_table_add

Add-Table lookup-Add (ATA): adders before and after the lookup. The
fixed-point argument X splits into chunks A and B; parallel adders form
the addresses A+B and A-B; table banks read f(A), f(A+B) and f(A-B) in
parallel; and a central-difference combination of the readouts, a
truncated Taylor series rewritten as differences, gives the value with
no coefficient multiplier. The first-order form looks up f(A) and
f(A+B), subtracts, shifts the difference and adds it to f(A); the
second-order form reads the three banks and applies centered-difference
formulas. Sign and exponent processing and a final renormalization
produce the floating-point result.

truncation_order sets how many readouts the difference formula
combines and how far the truncated series reaches: first order costs
two lookups, second order three lookups and seven additions.
table_bank_count and table_access trade storage against the read path:
six parallel banks per function hold about 868 Kbit at 24-bit
precision, while one table reused sequentially holds about 16 Kbit and
runs five times slower. input_chunk_bits sets the depth of each bank.
final_reduction picks the subtract-shift-add chain of the first-order
form or a Wallace multioperand tree over the fixed-point readouts, and
the final_adder slot's csa_tree is that tree; the address_adder slot
holds the parallel adders in front of the banks. offset_partitioning
and symmetry are the storage reductions of the multipartite framework
applied to the difference tables.

The family wins on the post-lookup path: with large fast memories whose
banks read in parallel, the mantissa datapath is 16 gate delays of
logic plus the lookup, 22 in total, or 1.57 single-precision
multiplication times under a fast-ECL assumption; reciprocal and square
root are the fastest of the seven functions and arc tangent the
slowest. It differs from bipartite, stam and multipartite, which
decompose into parallel offset tables added only after the lookup,
because ATA adds before the lookup and combines the readouts as
differences; it loses to them wherever memory is scarce, since the
speed is bought with table banks, and the figures are estimates rather
than measurements of fabricated hardware.

The accuracy contract is a maximum absolute error of at most 0.5 ulp
over the restricted operand ranges, checked exhaustively over the
24-bit mantissas and by random single-precision inputs, which is stated
not to guarantee correct rounding to nearest. Each function is applied
only after the range_reducer restricts or transforms the operand into
the table range, and full-range sine and cosine need pi stored to well
beyond the operand precision. The family is feed-forward.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/sfu.py`: one value table read at the address and its neighbours, `truncation_order` central differences times the low chunk, `table_access` as the bank count, `final_reduction` a chain or a tree, `offset_partitioning` splitting the low chunk, `symmetry` the central difference). `python3 -m chialu.targets.rtl.families.sfu --function <fn> --format <format> --family add_table_add --pins k=v,...` emits the module with its modeled error for a rewrite.

## design choices

### final_reduction

| member | what it selects |
| --- | --- |
| `adder_chain` | the central-difference terms are summed by a chain of adders. |
| `multioperand_tree` | they are summed by a tree. |

### offset_partitioning

| member | what it selects |
| --- | --- |
| `none` | one offset word addresses the tables. |
| `split_subwords` | the offset is split into subwords addressed separately. |

### table_access

| member | what it selects |
| --- | --- |
| `parallel_banks` | one bank per read, so every read runs at once. |
| `dual_port` | each bank serves two reads, which halves the banks and serializes nothing else. |

## references

wong_1995 -> W. F. Wong, E. Goto, "Fast Evaluation of the Elementary Functions in Single Precision", IEEE Transactions on Computers, vol. 44, no. 3, pp. 453-457, 1995
dedinechin_2005 -> de Dinechin, Tisserand, "Multipartite Table Methods", IEEE Transactions on Computers, 2005
