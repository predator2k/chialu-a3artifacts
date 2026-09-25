# fpga_mapped: proposed changes to the space

* `mapping` value `dedicated_4_to_1_mux_parallel_to_lut` — an architectural modification that places a 4:1 multiplexer beside each 4-LUT, sharing data and select inputs [beauchamp_2008]
* choice `execution_schedule: {single_cycle_parallel, four_cycle_time_multiplexed}` — parallel use of four multiplier shifters versus reuse of one across bytes [gigliotti_2004]
* choice `shift_function: {shift, rotate}` — the multiplier form is a rotate, with bits from the MSB end returning at the LSB end [gigliotti_2004]
