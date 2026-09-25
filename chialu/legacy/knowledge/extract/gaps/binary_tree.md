# binary_tree: proposed changes to the space

* product_grouping choice {adjacent_pairs, full_n_way} — PMADDWD reduces adjacent product pairs and a separate PADDD completes the reduction [peleg1996]
* inter_level_storage / inter_tile_chaining choice — an NPU tile reduces locally and daisy-chains int32 partials to the next tile through BRAM [boutros_2020]
