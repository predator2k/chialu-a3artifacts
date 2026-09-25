---
family: srt_high_radix
pin: {quotient_conversion: serial_msd_borrow_scan}
---
# serial_msd_borrow_scan

Post-recurrence conversion of the redundant quotient by a serial scan
from the most significant digit: a negative digit is increased by the
radix and one unit is borrowed from the next more-significant digit,
and because zero is a permitted digit the sign of the next nonzero
digit is taken from the divisor and partial-remainder signs, or from a
sign attached to the zero, so the borrow propagates through runs of
zeros.

It is the pick where the converter may run after the recurrence and
cost nothing on the iteration path: the scan needs one digit position
of logic and a borrow, and the terminal overflow is settled either by
an addition in the quotient register or by decrementing the least
significant digit and adding the divisor to the remainder. The
separate positive and negative accumulation keeps two registers during
the recurrence and subtracts them at the end, and the on-the-fly
converter that digit_recurrence_sqrt_combined shares maintains both
forms of the quotient during the recurrence so no post-step remains;
both remove the serial scan's latency at the price of more registers
or update logic per step.

## references

robertson_1958 -> Robertson, "A New Class of Digital Division Methods", IRE Transactions on Electronic Computers, 1958
