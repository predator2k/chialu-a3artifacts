# correct_rounding_strategy: proposed changes to the space

* `strategy` values `ziv_multilevel_retry` and `interpolation_tables` — LIBULTIM and LIBMCR raise precision until rounding is proven rather than in two phases, and the posit paper proposes tables to avoid the dilemma [muller_2016#s11, muller_2016#s13, gustafson_2017]
* choices `phase_count: Int` and `intermediate_representation: {double_extended, double_double, triple_double, scslib}` — the phases and their arithmetic set the cost of each implementation [dedinechin_2007]
* choice `proof_status: {conjectured, exhaustive, proved}` — Gal's all-input claim rests on a uniformity assumption while CRLIBM publishes a proof per function [gal_1991, muller_2016#s13]
* choice `hardness_search: {exhaustive, L_algorithm, SLZ_polynomial, polynomial_filter_euclidean_grid, fpga_tabulated_differences}` with an independent cross-check value — the offline worst-case search method and agreement between unrelated methods are what `worst_case_knowledge` summarizes [muller_2018#s10, lefevre_2001, pasca_2011#s13]
* parameters `oracle_precision_bits` and `implementation_representation_H`, and choices `polynomial_generation: counterexample_guided_linear_programming` and `multi_function_interval_deduction: simultaneous_bound_expansion` — the RLIBM flow's knobs [lim_2021, lim_2021b]
* choices `discriminant_threshold` and `fallback_evaluation: {direct_function, inverse_function}` — the accurate-table retry triggers within 1/1024 ulp and may resolve the last bit through the inverse function [markstein_1990]
* choices `monotonicity_contract`, `breakpoint_type` and `special_input_handling: analytic_replacement` — monotonicity preservation, directed-versus-nearest breakpoints and analytic treatment near zero [muller_2016#s11]
* choice `coefficient_tuning: exhaustive_per_subinterval_ulp_adjustment` — hardware designs lower the required internal accuracy by adjusting stored coefficients [schulte_1994]
