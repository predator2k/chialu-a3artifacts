---
family: srt_radix2
pin: {residual_form: carry_save}
---
# carry_save

The partial remainder held as sum and carry words S and C: each stage
forms the next remainder by a carry-save subtraction of the selected
divisor multiple, the three upper positions of S and C are summed
locally to classify the remainder and pick the digit from {-1, 0,
1}, and the full sum is resolved only after the last stage. A
force-next-digit flag keeps the selection correct when the trimmed
sign bit aliases a negative remainder into a positive encoding.

Carry-save residuals are the pick for every divider whose stage
delay sets the cycle: the stage delay falls from O(log n) with full
carry resolution to O(1), which gives the combinatorial array O(n)
delay at O(n^2) area and lets the self-timed 54-bit divider reach an
estimated 160 ns with overlapped stages in 1.2 um. The costs are
double residual storage, a selection that consumes redundant inputs
or a short assimilated estimate whose bounds are biased relative to
borrow-save, and a final assimilation whenever the remainder itself
is needed. The two's-complement residual is the sibling when
register area and a plain remainder matter more than the recurrence
delay.

## references

zuras1986 -> D. Zuras, W. H. McAllister, "Balanced Delay Trees and Combinatorial Division in VLSI", IEEE Journal of Solid-State Circuits, vol. 21, 1986
williams_1991 -> Williams, Horowitz, "A Zero-Overhead Self-Timed 160-ns 54-b CMOS Divider", IEEE Journal of Solid-State Circuits, 1991
oberman_1997 -> Oberman, Flynn, "Division Algorithms and Implementations", IEEE Transactions on Computers, 1997
burgess_1995 -> Burgess, Williams, "Choices of Operand Truncation in the SRT Division Algorithm", IEEE Transactions on Computers, 1995
harris_1997 -> Harris, Oberman, Horowitz, "SRT Division Architectures and Implementations", 13th IEEE Symposium on Computer Arithmetic, 1997
