---
family: dynamic_segment
pin: {segment_select: dynamic_leading_one}
---
# dynamic_leading_one

Two leading-one detectors locate each operand's most significant 1; the
k-bit segment is that 1, the next k-2 bits, and an inserted 1 in place
of the discarded low portion. A k x k accurate core multiplies the two
segments and a barrel shifter restores the product by the sum of the two
leading-one positions; an operand whose leading one lies within the
least-significant k bits passes those bits directly.

It is the pick when the error must stay unbiased over a wide dynamic
range: the 6-bit window at n = 16 saves 70% area and 71% power against
an accurate Wallace tree in an industrial 65-nm library with 6.31%
maximum and 1.47% average error and near-zero bias. It is more accurate
than static selection because the retained bits follow the leading one,
and its savings grow with operand width since the core stays k x k.
The cost is the detectors, multiplexers and barrel shifter, which can
dominate the reduced core at small widths; signed operation adds
pre- and post-processing that lowers the power saving from 71% to 59%
at n = 16. The window can also feed a logarithmic core.

## references

hashemi2015 -> S. Hashemi, R. I. Bahar, S. Reda, "DRUM: A Dynamic Range Unbiased Multiplier for Approximate Applications", IEEE/ACM International Conference on Computer-Aided Design (ICCAD), 2015
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
yin2021 -> P. Yin, C. Wang, H. Waris, W. Liu, Y. Han, F. Lombardi, "Design and Analysis of Energy-Efficient Dynamic Range Approximate Logarithmic Multipliers for Machine Learning", IEEE Transactions on Sustainable Computing, vol. 6, no. 4, pp. 612-625, 2021
