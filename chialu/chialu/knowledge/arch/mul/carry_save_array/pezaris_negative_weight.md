---
family: carry_save_array
pin: {signed_scheme: pezaris_negative_weight}
---
# pezaris_negative_weight

The Pezaris array: the highest-order bit of each two's-complement
operand is treated as a bit of negative weight and every other bit as
positive, so the partial products fall into positive and negative kinds
that are added directly, without converting negative operands. The cells
are 2-bit gated adders with a 2-bit anticipated carry that accept
partial products of either sign; carries propagate diagonally, sums
vertically, and the final row runs its internal carries horizontally.

The negative-weight form is the pick when operand sign bits arrive last
or when a conversion of negative operands to magnitudes is unwanted,
since the array consumes the signed operands as they are. The 17 by 17
bit implementation delivers the full 34-bit product in 40 ns in
current-steering ECL, with the carry-heavy longest path at about 30 ns
and the sum-heavy path at about 35 ns, and a sum-skip after every four
adders shortens the vertical path. The price is cells of two kinds and a
mixed final row, against the single positive cell type that the
Baugh-Wooley transform buys with its five correction bits, and the paper
notes that a 3-bit anticipated carry and richer sum-propagation paths
are the next speed steps.

## references

pezaris1971 -> S. D. Pezaris, "A 40-ns 17-Bit by 17-Bit Array Multiplier", IEEE Transactions on Computers, vol. C-20, no. 4, pp. 442-447, 1971
