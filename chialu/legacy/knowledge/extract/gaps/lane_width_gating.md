# lane_width_gating: proposed changes to the space

* width_thresholds {16, 33} and signed_detection parallel_zero_and_ones_detect — the two independently useful cutoffs and leading-ones detection for negative operands [brooks_1999]
* load_detection {enabled, omitted} — tagging cache-sourced values decides how many opportunities are seen [brooks_1999]
* significance_granularity {byte, halfword}, extension_bit_count {2, 3} and pipeline_organization {byte_serial, halfword_serial, byte_semi_parallel, byte_parallel_skewed, byte_parallel_compressed, byte_parallel_skewed_with_bypasses} — storage overhead and CPI follow these [canal_2000]
* gating as a set rather than one value — operand isolation in the functional unit and byte-level latch clock gating occur together [canal_2000]
* voltage_scaling precision_dependent, frequency_scaling subword_parallel_constant_throughput and power-domain partitioning — DVAS/DVAFS convert slack into voltage and frequency [moons2017]
* detection value regime_bit_width and gating value partial_product_region_enable with region_granularity_bits {4, 8} — posit mantissa-width detection driving enabled PPG regions [zhang_2020]
