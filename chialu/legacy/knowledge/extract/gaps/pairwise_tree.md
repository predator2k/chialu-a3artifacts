# pairwise_tree: proposed changes to the space

* choice product_grouping (adjacent_pairs) — PMADDWD adds products zero/one and two/three into separate 32-bit results rather than reducing all products to one sum. [peleg1996]
* slot mul admits bit_serial_dnn_datapath — Pragmatic's PIPs feed shifted essential-bit terms into per-filter adder trees, which is a pairwise tree over serial product terms. [albericio_2017]
