# tiled_cpa_reduction_tree

Partial-product reduction by levels of staggered K-bit carry-propagate adders instead of counters: each level tiles the matrix with short CPAs (adder_width 2, 4, 8, or full_width, which degenerates to a binary tree of full-width CPAs), and horizontal carry propagation inside a tile replaces vertical compression wherever the tile's carry-out is as fast as its sum. carry_assimilation says how tile carries re-enter the matrix and terminal_reduction which compressor closes the last rows; PPST-style trees reach 10 XOR delays against 14 for counters at 24x24.

The trade is cell speed against fan-in: a K-bit tile removes bits along its width in one short carry-chain delay, so the scheme pays when the tile_adder family (ripple or short lookahead) has a carry-out no slower than a counter's sum, and it loses when K grows past the point where the chain is slower than a compressor level. Row-wise 4-bit lookahead adders emitting four product bits per row are the array form of the same idea. staggered_tiling keeps carries local; an extra_counter_row or a terminal_compressor (3:2, 4:2 or 9:2) absorbs the leftover carry vector before the cpa slot, which still sees a nonuniform arrival profile and benefits from a hybrid final adder.

Pick it over csa_reduction_tree when the cell library's short carry chains are fast (dedicated adder cells, FPGA carry chains) and over compressor_4_2_tree when regularity matters less than the XOR count; a counter tree remains the safer choice where wiring rather than cell delay dominates.

## design choices

### terminal_reduction

| member | what it selects |
| --- | --- |
| `3_2_counter` | the rows left after the tiling are reduced by full adders. |
| `compressor_4_2` | they are reduced by 4:2 compressors. |
| `compressor_9_2` | they are reduced by 9:2 compressors. |

## references

oklobdzija1995 -> V. G. Oklobdzija, D. Villeger, "Improving Multiplier Design by Using Improved Column Compression Tree and Optimized Final Adder in CMOS Technology", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 3, 1995
samgupta1990 -> H. Sam, A. Gupta, "A Generalized Multibit Recoding of Two's Complement Binary Numbers and Its Proof with Application in Multiplier Implementations", IEEE Transactions on Computers, vol. 39, no. 8, pp. 1006-1015, 1990
wallace1964 -> Wallace, "A Suggestion for a Fast Multiplier", IEEE Transactions on Electronic Computers, 1964
stelling1998 -> P. F. Stelling, C. U. Martel, V. G. Oklobdzija, R. Ravi, "Optimal Circuits for Parallel Multipliers", IEEE Transactions on Computers, vol. 47, no. 3, 1998
