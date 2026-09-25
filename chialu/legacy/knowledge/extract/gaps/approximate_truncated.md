# approximate_truncated: proposed changes to the space

* choice `truncation_constant_relation: {complementary_per_bit, equal, zero}` — the relation between the constants forced onto corresponding truncated operand bits sets the addition/subtraction error behaviour (complementary for addition, equal/zero for subtraction) and the current `lower_scheme` cannot express it [frustaci2019]
