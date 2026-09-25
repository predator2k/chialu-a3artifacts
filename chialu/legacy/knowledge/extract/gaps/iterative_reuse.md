# iterative_reuse: proposed changes to the space

* instantiated_fraction admits a numeric percentage (20%) or a retired_bits_per_iteration value (12) — the Model 91 subset is 20% of the full tree and retires 12 multiplier bits per pass, which none of half/quarter/eighth expresses. [anderson1967]
* choices partial_product_recoding (modified Booth), partial_products_per_cycle / partial-tree input count (8), and local_clocking (stoppable on-chip ring oscillator) — these set the instantiated tree width and the matched internal pipeline clock. [santoro1989]
* choice bits_per_iteration_per_half (6) for a split-multiplier organization — the CDC 6600 runs two 24-bit halves through three carry-save layers, two bits per layer, per step. [thornton_1970__s06]
