---
family: segmented_carry_speculative
pin: {carry_in_scheme: carry_cut_back}
---
# carry_cut_back

A conventional carry chain is cut by cut-back modules placed along it:
a PROP monitor detects a propagate sequence that could activate a long
path, and a multiplexer or monotonic OR straight-cut gate substitutes
a guessed carry from a lower-significance stage, optionally refined by
a short SPEC speculator. The apparent feedback uses operand-derived
local propagate/generate signals and is not recursive, and every
module guesses in the same direction so cut errors do not accumulate.

The tuple (number of cut-backs, ADD1, PROP, ADD3, SPEC) sets the trade:
at 3.3 GHz in industrial 65 nm, (7,1,1,2,0) reaches 22 fJ and 472 um2
against 47 fJ and 910 um2 for the exact adder at REMAX 35 per cent,
while (2,5,1,3,0) holds REMAX to 3 per cent at 38 fJ. A consistently
directed cut bounds the absolute error at 2^m, so mixed guess
directions are prohibited. Timing analysis needs manual constraints
that exclude the full chain as a false path, and high-speed targets
need more modules. Against the ISA, which pairs propagate_window with
an error_reduction_stage, CCB improves PDAP by up to 30 per cent and
gains as the required accuracy rises, while ISA wins at very low
precision under the 3.3 GHz constraint. It is the pick for a bounded
relative error on a single-pass chain with no correction hardware.

## references

camus2016 -> V. Camus, J. Schlachter, C. Enz, "A Low-Power Carry Cut-Back Approximate Adder with Fixed-Point Implementation and Floating-Point Precision", 53rd Design Automation Conference (DAC), 2016
jiang2017 -> H. Jiang, C. Liu, L. Liu, F. Lombardi, J. Han, "A Review, Classification, and Comparative Evaluation of Approximate Arithmetic Circuits", ACM Journal on Emerging Technologies in Computing Systems, vol. 13, no. 4, 2017
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
