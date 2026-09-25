---
family: parallel_decimal_multiplication
pin: {multiplier_recoding: radix4_radix5_split}
---
# radix4_radix5_split

Each BCD multiplier digit is decomposed as Yi = 5 YU + YL with YU in
{0, 1, 2} and YL in {-2, -1, 0, 1, 2}, so the partial products need
only the multiples plus or minus X and 2X, with fixed shifts for the
factor five or 5X and 10X precomputed, and a d-digit multiplier yields
2d partial products. Lang and Nannarelli's form uses yH in {0, 5, 10}
and yL in [-2, 2] with x, 2x, 5x and 10x precomputed and radix-10
complements for the negative terms.

It is the pick when partial-product generation must be as fast as
binary Booth radix-4, which the simple multiple set achieves because
no 3X addition is needed; the price is twice the rows of
sd_radix10_m5_p5 and a 32:2 worst-case column, so at the minimum-delay
point the SD radix-5 multiplier is faster than SD radix-10 but larger,
1.20 against 1.15 times the baseline speed at 0.70 against 0.65 its
area in 90 nm. A mixed 4221/5211 tree keeps the reduction binary; the
8421 form with radix-10 carry-save adders and carry counters takes six
levels for 16 digits and makes every partial product positive, so no
sign extension is needed.

## references

vazquez_2010 -> Vazquez, Antelo, Montuschi, "Improved Design of High-Performance Parallel Decimal Multipliers", IEEE Transactions on Computers, 2010
lang_2006 -> Lang, Nannarelli, "A Radix-10 Combinational Multiplier", 40th Asilomar Conference on Signals, Systems and Computers, 2006
