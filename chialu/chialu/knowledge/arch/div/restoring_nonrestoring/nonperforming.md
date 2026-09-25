---
family: restoring_nonrestoring
pin: {style: nonperforming}
---
# nonperforming

The subtraction is tried but its result is kept only when it is
nonnegative: a multiplexer selects either the difference, with
quotient bit 1, or the shifted old remainder, with quotient bit 0, so
no restoring addition or remainder correction is needed and one
quotient bit is produced per clock. The CDC 6600 generalizes the idea to
three parallel subtractors trying 1X, 2X and 3X, with end-around-borrow
signals selecting the largest successful one and emitting two quotient
bits per iteration.

Nonperforming is the pick when the restore cycle must go but a true
remainder must stay: the ILLIAC IV PE gets one quotient bit per clock
where true restoring would take twice as many iterative clocks under
lock-step scheduling, and the 6600 needs 25 subtractions and 24 shifts
for a 48-bit coefficient, 2900 ns for a floating division, with the
end-around borrow shortening quotient selection relative to waiting
for the residual sign. Chen's exact array cell is a subtractor plus a
quotient-controlled 2-to-1 MUX, two transistors fewer than the
nonrestoring cell and free of its remainder-correction circuit, which
gives the restoring arrangement slightly lower power. The cost is the
parallel trial hardware: the 6600 carries three subtract networks, and
a fully simultaneous divider needs so many adders and switches that it
is considered only in rare cases. In the ADIR grammar
it is `family: restoring_nonrestoring` with `pin: {style: nonperforming}`.

## references

richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
thornton_1970 -> J. E. Thornton, "Design of a Computer: The Control Data 6600", Scott, Foresman and Co., 1970
davis_1969 -> R. L. Davis, "The ILLIAC IV Processing Element", IEEE Transactions on Computers, vol. C-18, no. 9, pp. 800-816, 1969
chen2016 -> L. Chen, J. Han, W. Liu, F. Lombardi, "On the Design of Approximate Restoring Dividers for Error-Tolerant Applications", IEEE Transactions on Computers, vol. 65, no. 8, pp. 2522-2533, 2016
