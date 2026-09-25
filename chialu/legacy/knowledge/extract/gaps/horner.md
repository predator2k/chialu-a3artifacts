# horner: proposed changes to the space

* choice `arithmetic_step: {separate_multiply_add, fused_multiply_add}` — whether each nested step rounds once or twice changes the error recurrence [muller_2016#s04]
* parameters `product_guard_bits` and `argument_guard_bits` per step — the FPGA evaluator truncates each product beyond the coefficient LSB and may truncate y before each multiplication [pasca_2011#s08]
* choice `per_degree_precision: {double, double_double, double_double_extended}` — the correctly rounded logarithm changes evaluation precision across the chain [dedinechin_2007, lynch_1995]
