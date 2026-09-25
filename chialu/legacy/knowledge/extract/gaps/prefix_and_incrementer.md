# prefix_and_incrementer: proposed changes to the space

* choice `carry_arrangement: {digit_counter_ripple, simultaneous_all_lower_and, serial_and_chain, grouped_hybrid}` — direct unbounded-fan-in gating from all lower-order 1 states and the grouped direct/chained compromise are distinct arrangements that `structure` cannot express [richards_1955#s08]
* choice `storage_implementation: {bistable_digit_counters, half_adder_static_storage, half_adder_dynamic_storage, recirculating_n_digit_delay_line}` — the counter form's state-holding organisation (including dynamic per-bit storage) is a separate decision from the carry structure [richards_1955#s08]
* choice `hardware_organization: {one_stage_per_bit, bit_serial_reuse}` — one half adder reused with an n-digit delay line is a bit-serial incrementer the space cannot classify [richards_1955#s08]
* choice `direction_change_recovery: {none, shadow_register_swap}` — the constant-period up/down counter prestores the previous block value so a direction reversal swaps rather than waits on a reversed carry/borrow chain [stan1997]
* choice `prescaled_event_generation: {combinational_chain, up_down_ring_counter}` — constant-time CARRY-in/BORROW-in events from ring counters rather than a combinational chain make the clock period O(1) in width [stan1997]
* choice `partitioning_method: top_down` — the block sizes of the prescaled counter come from a reported top-down sizing procedure that minimises the ring-counter overhead [stan1997]
* family or value for shared-adder increment units — the chapter's Increment Units perform arbitrary 18-bit addition/subtraction through a shared parallel adder, which the family does not describe [thornton_1970#s06]
