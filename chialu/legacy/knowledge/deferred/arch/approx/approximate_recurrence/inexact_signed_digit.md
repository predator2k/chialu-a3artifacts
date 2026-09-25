---
family: approximate_recurrence
pin: {cell: inexact_signed_digit}
---
# inexact_signed_digit

A prescaled high-radix SRT array whose partial remainders are
carry-free binary signed digits: each row is built from exact
signed-digit adder cells, and approximation replaces selected cells
with an inexact signed-digit cell that errs on a quarter of its input
combinations and uses fewer transistors, or removes cells by
truncation. An error-compensation cluster of one exact cell,
one inexact cell and eight-transistor buffers preserves the paths into
the quotient-generating residual bits.

It is the pick when delay matters: radix 4 cuts nearly 60 percent of
the delay of the radix-2 array of approximate subtractor cells in a
45 nm predictive model, and radix 8 cuts further, at the price of a
higher normalized error distance, which larger widths reduce again.
The radix-2 array with axsc cells uses less power and area, so it
stays the choice when energy dominates. Within the variant, triangle
geometry gives the best error distance and horizontal the worst;
truncation saves the most power and area at the worst error, and
compensation restores much of the lost accuracy for at most 0.1
percent more power. Image division reports about 50 dB average PSNR
against 28 dB for the SEERAD and TruncApp designs.

## references

chen2018 -> L. Chen, J. Han, W. Liu, P. Montuschi, F. Lombardi, "Design, Evaluation and Application of Approximate High-Radix Dividers", IEEE Transactions on Multi-Scale Computing Systems, vol. 4, no. 3, pp. 299-312, 2018
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
