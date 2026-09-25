# low_power_gated: proposed changes to the space

* path_specific_shifters choice or per-path align/norm slots — the near path pairs a bounded alignment with a full normalizer and the far path pairs a full alignment with a bounded normalizer, which one shared align/norm slot cannot express [pillai_1997]
* bypass_cases choice {exponent_difference_gt_p, zero_operand, infinity, NaN} — the conditions that inhibit both arithmetic paths are a design decision of the family [pillai_1997]
