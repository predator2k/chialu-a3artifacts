# single_poly: proposed changes to the space

* choices `error_objective: {least_squares, minimax_absolute, minimax_relative}` and `orthogonal_basis: {legendre, chebyshev, jacobi, laguerre}` — the fitted norm and the orthogonal sequence are separate from the basis enumeration, and generic `minimax` and L2-fitted values appear in practice [muller_2016#s04, muller_2018#s10, brisebarre_2006, hussain_2021, kim_2021]
* `degree` range beyond 8 and below 2 — reported degrees include 1, 9, 10, 11, 12, 13, 21, 25, 44, 47 and 54 [muller_2016#s04, muller_2016#s13, muller_2018#s10, tang_1990, pasca_2011]
* choice `coefficient_constraints: {unconstrained_real, machine_number, multiple_of_2^-mi, fixed_values, forced_zero, multiword}` with `coefficient_optimization: lattice_constrained_minimax_polytope_search` — constraints are imposed during synthesis and a joint lattice search beats rounding [muller_2016#s04, muller_2018#s10, brisebarre_2006]
* choice `symmetry_form: {none, odd, even}` — odd/even forms xP(x^2) and Q(x^2) halve the coefficient count [muller_2016#s13, brisebarre_2006]
* choice `coefficient_generation: rounding_interval_linear_programming` — coefficients satisfy per-input reduced rounding intervals rather than a minimax bound [lim_2021]
* choices `argument_decomposition: radix_2k_blocks`, a postprocessing slot for function-specific table factors or additive reconstruction, and `rounding_contract: {faithful, correctly_rounded}` — the small-multiplier method decomposes the argument, reconstructs through a table factor and targets faithful rounding [ercegovac_2000]
* choices `coefficient_storage` and pipelined resource reuse — a shared multiplier/adder evaluates the polynomial over cycles from constant registers [hussain_2021]
* choice `reconstruction_split_bits` and `output_transform: sine_factor_and_cosine_residual` — accurate reconstruction splits the argument into high/low parts and known leading behaviour is removed before evaluation [tang_1990, detrey_2007]
* choice `execution: programmed` — the approximation may be evaluated through basic operations rather than a dedicated unit [richards_1955#s11]
