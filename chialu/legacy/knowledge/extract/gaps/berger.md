# berger: proposed changes to the space

* count_encoding {B0, B1} and length_class {maximal, non_maximal} — the encoding and whether k = 2^c - 1 decide which generator constructions apply [lala_2001__s03, lala_2001__s05]
* check_field value modified_berger encoding the zero-count difference from the minimum valid zero count — a PLA variant distinct from the modulo-reduced field [lala_2001__s04]
* check_bit_generator slot {full_adder_count_tree, m_out_of_n_partition, partitioned_counter_addition_array, popcount_counter_tree} — the regenerated-check-field structure is the checker's main cost [lala_2001__s05]
* check_generation {result_regeneration, operation_prediction} — a Berger-check-prediction ALU predicts the result symbol from operands, carries and operation signals rather than regenerating it [lo_1992]
