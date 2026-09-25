---
family: approximate_functional
pin: {method: divisor_round_pow2_lut}
---
# divisor_round_pow2_lut

SEERAD: the divisor's leading one fixes Bf = 2^K, the bits that follow
it classify B into one of a few groups, and a small table returns a
per-group pair (L, D) so that A/B is approximated by D*A/2^(K+L). D*A
is formed from shifted copies of |A| and one adder, a barrel shifter
divides by 2^(K+L), and sign detection and sign setting handle two's
complement inputs. No multiplier and no reciprocal table appear in the
datapath.

More divisor groups select more D values and reduce error while
adding hardware and delay: levels 1 to 4 use 1, 2, 4 and 8 groups and
bound the maximum error at 37.5%, 25%, 12.5% and 6.25%. The 8-bit
tuples are reused at wider operands for simpler hardware with slightly
larger inaccuracy. It is the pick for the highest error tolerance and
the shortest combinational path, and is faster than truncated
reciprocal and logarithmic methods at the same level, but it has lower
accuracy and higher area and power than array-style approximate
dividers, and TruncApp_AM reports lower mean error at less area and
energy than SEERAD level 3.

## references

zendegani2016 -> R. Zendegani, M. Kamal, A. Fayyazi, A. Afzali-Kusha, S. Safari, M. Pedram, "SEERAD: A High Speed yet Energy-Efficient Rounding-Based Approximate Divider", Design, Automation and Test in Europe (DATE), pp. 1481-1484, 2016
jiang2017 -> H. Jiang, C. Liu, L. Liu, F. Lombardi, J. Han, "A Review, Classification, and Comparative Evaluation of Approximate Arithmetic Circuits", ACM Journal on Emerging Technologies in Computing Systems, vol. 13, no. 4, 2017
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
vahdat2017b -> S. Vahdat, M. Kamal, A. Afzali-Kusha, M. Pedram, Z. Navabi, "TruncApp: A Truncation-Based Approximate Divider for Energy Efficient DSP Applications", Design, Automation and Test in Europe (DATE), pp. 1635-1638, 2017
