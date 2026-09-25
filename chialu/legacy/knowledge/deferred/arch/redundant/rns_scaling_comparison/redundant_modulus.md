---
family: rns_scaling_comparison
pin: {method: redundant_modulus}
---
# redundant_modulus

Base extension that carries the residue of x modulo one extra
relatively prime modulus p_{m+1} through every operation: the CRT
expansion bounds the unknown integer r_x by n - 1, so with p_{m+1} >= n
that integer is recovered modulo p_{m+1}, and parallel constant
multiplications with tree-structured modular additions compute r_x and
the residues for all extension moduli at once, after which r_x P is
subtracted modulo each extension modulus.

The redundant modulus is the pick when base extension sits in a
feedback path, as in an IIR filter, where the Szabo-Tanaka mixed-radix
extension costs n table-lookup cycles and n(n + 1)/2 - 1 tables:
combining modular addition and constant multiplication in one lookup
gives ceil(log2(n + 1)) + 1 cycles with 2n + 2 tables, 16 tables and 5
cycles at n = 8 against 35 and 8, and 40 tables and 6 cycles at n = 20
against 209 and 20. In fully pipelined use the gain is hardware and
fewer interstage latches rather than throughput. The redundant residue
must accompany the data throughout and the moduli must stay small
enough for practical tables; no fault coverage is reported.
Base extension underlies scaling, dynamic-range extension, comparison,
overflow detection, sign determination and redundant-RNS error
correction, so Jullien's scaler consumes it, while the diagonal
function compares without any redundant modulus.

The library does not generate this method; a comparator that pins it falls back to the mixed-radix compare and its header says so (`chialu/targets/rtl/families/redundant.py`).

## references

shenoy_kumaresan_1989 -> Shenoy, Kumaresan, "Fast Base Extension Using a Redundant Modulus in RNS", IEEE Transactions on Computers, 1989
jullien_1978 -> Jullien, "Residue Number Scaling and Other Operations Using ROM Arrays", IEEE Transactions on Computers, 1978
dimauro_1993 -> Dimauro, Impedovo, Pirlo, "A New Technique for Fast Number Comparison in the Residue Number System", IEEE Transactions on Computers, 1993
