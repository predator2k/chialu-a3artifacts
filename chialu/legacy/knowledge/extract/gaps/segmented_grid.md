# segmented_grid: proposed changes to the space

* `seg_w` value `4` — the documented flexible block is 4x4 [haynes_1998]
* `num_seg` as independent horizontal and vertical counts `m` and `n` — the grid builds any 4m-bit by 4n-bit multiplier [haynes_1998]
* choices `signedness: {signed_twos_complement, unsigned}` with a `boundary_configuration` of six bits (Ma, Mb, Cl, Cr, Cb, Ct) and `interblock_connections: dedicated_left_right_top_bottom` — the block's configuration bits and neighbour routing are design decisions [haynes_1998]
* choice `final_adder_activation: final_column_only` — each block's output adder is used only in the last column [haynes_1998]
