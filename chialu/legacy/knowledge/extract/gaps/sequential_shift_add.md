# sequential_shift_add: proposed changes to the space

* choice `multiplier_recoding: {none, booth_adjacent_bit, modified_booth_radix4, minimal_signed_digit, overlapping_three_bit_signed, minimal_canonical}` — every source after the plain shift-add recodes the multiplier to cut additions or handle signs [booth1951, rubinfield1975, tocher_1958, goldschmidt_1964__s01, avizienis_1961]
* refine `string_skipping` into `shift_schedule: {variable_run_length, uniform_2_bit, uniform_3_bit}` — variable shifts skip runs while uniform groups give a predictable cycle count [macsorley1961]
* `step_adder` slot value `generalized_signed_digit` — the signed-digit recurrence uses a carry-free adder [avizienis_1961]
* choices `multiples_per_pass: Int` and a recirculating four-input/two-output accumulator — four bits per pass add two multiples into a two-register carry-save partial product [goldschmidt_1964__s01]
* choices for signed-operand handling (negate both operands, LSD-first complementation, partial-product sign insertion) [robertson1955]
* choices `shifted_quantity: {multiplicand, accumulated_sum}`, `control_timing: {synchronous, asynchronous_completion}`, and a storage slot for the shift registers (static, delay-line, drum, CRT) [richards_1955__s06]
* choice `clocking_source: {system_clock, multiplied_clock, self_clocked}` — the loop's maximum rate exceeds the system clock [bewick1994__s02]
* choice `conditional_add_control` (microcoded, shifted-out MSB) for the programmed form [mead_conway1980__s06]
