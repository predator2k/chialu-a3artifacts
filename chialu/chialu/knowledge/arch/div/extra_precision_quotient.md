# extra_precision_quotient

A final-step discipline for functional-iteration division: the
quotient or root is computed with enough guard bits beyond the target
precision that the truncation errors of the intermediate multiplies
are provably bounded, so the last rounding can be carried out by
truncation without a per-result remainder test. The sizing tool is
Even, Seidel and Ferguson's parametric error analysis of Goldschmidt's
algorithm, which ties the precision of each intermediate multiplier
to the final error; applied to the AMD K7 divider it proved smaller
guard-bit budgets sufficient and cut 10.6 percent of the FP-DIV
datapath cost.

The family exists because functional iteration approximates the
quotient where digit recurrence keeps an exact remainder: a
recurrence divider rounds by a sign and zero test on the final
residual, while Newton-Raphson and Goldschmidt deliver an approximate
result and need extra precision plus either a back-multiply remainder
step or a proved exclusion-zone argument before the result is IEEE
correct. Goldschmidt is the harder case, since its two independent
multiplies pipeline but their truncation error accumulates rather
than self-correcting, so the guard bits carried through the iteration
are a design choice in their own right, sized against the seed
accuracy, the iteration count and whether the intermediate multiplies
are truncated.

The neighbours in the final-step family trade hardware for proof
effort. Back-multiply rounding computes the residual a minus q times b
on an FMA and selects among two or three quotient candidates, which
makes software or microcode iteration IEEE correct on any FMA machine
and is how the K7 rounds under an ACL2 proof. Exclusion-zone proofs
show that the approximate result can never fall close enough to a
rounding boundary to round the wrong way, so the IA-64 line ships
iterative division without per-result remainder hardware, with the
recommended sequences machine-checked in HOL Light. Extra precision
sits between them: it removes the residual hardware and the candidate
mux but moves the burden into the datapath width and into the error
analysis, so it is the pick where the multiplier width is the cost
being minimized and a parametric bound can be established for the
chosen seed, iteration count and rounding modes.

The seed instantiates the library's generated divider for this family
(`chialu/targets/rtl/families/div.py`: two more fraction bits than exclusion_zone_proof and the estimate's error bound added through `correction_adder`, so the estimate lies at or above the quotient by less than a quotient step and its truncation is the quotient without candidate selection; the remainder back-multiplied for the r output). `python3 -m chialu.targets.rtl.families.div --width 32 --family <family> --pins k=v,...` emits it for a rewrite (`--sqrt` for the square root).

## references

even_2003 -> Even, Seidel, Ferguson, "A Parametric Error Analysis of Goldschmidt's Division Algorithm", 16th IEEE Symposium on Computer Arithmetic, 2003
oberman_1999 -> Oberman, "Floating Point Division and Square Root Algorithms and Implementation in the AMD-K7 Microprocessor", 14th IEEE Symposium on Computer Arithmetic, 1999
markstein_1990 -> Markstein, "Computation of Elementary Functions on the IBM RISC System/6000 Processor", IBM Journal of Research and Development, 1990
cornea_1999 -> Cornea-Hasegan, Golliver, Markstein, "Correctness Proofs Outline for Newton-Raphson Based Floating-Point Divide and Square Root Algorithms", 14th IEEE Symposium on Computer Arithmetic, 1999
harrison_2000 -> Harrison, "Formal Verification of IA-64 Division Algorithms", TPHOLs, LNCS 1869, 2000
