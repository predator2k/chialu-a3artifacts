# bounded_align: proposed changes to the space

* iterative_shift_cycles choice — Stretch aligned by bounded repeated shifting over several cycles, 80 per cent of numbers within six [bloch_1959]
* accumulator_window (LSBA, MSBA) bounds for fixed-point accumulation, which set the exactness contract [dedinechin_2008]
* retained_positions_beyond_product_lsb Int — an FMA aligner keeps two positions beyond the product LSB for the denormal subtraction case [schwarz_2005]
