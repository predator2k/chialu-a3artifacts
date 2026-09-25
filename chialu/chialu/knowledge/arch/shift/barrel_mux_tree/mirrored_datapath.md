---
family: barrel_mux_tree
pin: {direction_handling: mirrored_datapath}
---
# mirrored_datapath

Left and right shifts are served by separate mux arrays, each wired
for one direction: a parameterized left shifter of log2(N) stages of
N-bit 2:1 multiplexers, each controlled by one shift-amount bit and
displacing by 2^i, and a right shifter generated as its mirror image.
The CDC 6600 shift unit holds both a left circular and a right end-off
shift with sign extension in one network of six columns, one per count
bit, two columns per module set.

The mirrored form keeps each array at ceil(log2 n) stages with no
amount transform or reversal mux on the path, so the 6600 network
executes any shift in one minor cycle with fan-in and fan-out of three
per column and 60 modules excluding controls (thornton_1970). Posit
generators use it because regime extraction, mantissa alignment and
normalization each need a fixed direction, with the shifter widths
following the available mantissa width and the right shifter also
collecting sticky bits (jaiswal_2018, jaiswal_2019). It is the pick
when the directions belong to different pipeline points or when a
generator must stay parameterizable; a single bidirectional unit
through data_reversal or amount_negation wins on area when one shifter
can serve both directions.

## references

thornton_1970 -> J. E. Thornton, "Design of a Computer: The Control Data 6600", Scott, Foresman and Co., 1970
jaiswal_2018 -> M. K. Jaiswal, H. K.-H. So, "Universal Number Posit Arithmetic Generator on FPGA", Design, Automation and Test in Europe (DATE), 2018
jaiswal_2019 -> M. K. Jaiswal, H. K.-H. So, "PACoGen: A Hardware Posit Arithmetic Core Generator", IEEE Access, 2019
