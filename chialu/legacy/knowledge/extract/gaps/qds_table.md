# qds_table: proposed changes to the space

* comparison_constant_placement choice (within_overlap_region) — constants placed near the upper boundary of the overlap trade divisor inspection against residual inspection width [atkins_1968]
* unreachable_entry_value choice — unreachable P-D locations were initialized to 0 to save power and must not be treated as invalid merely because tests cannot reach them [pratt_1995, edelman_1997]
* implementation choice {pla, narrow_adder_plus_logic, synthesized} — the Pentium and R3010 used PLAs, the S-1 a narrow adder plus logic [coe_1995, rowen_1988, taylor_1985]
* sibling digit_select fillers (arithmetic-model, comparator/constant-comparison selection, prescaled MSD extraction) — many designs select without a table [atkins_1968, burgess_2007, nikmehr_2006, vazquez_2007b, robertson_1958, williams_1991, noll_1991, eisen_2007, schwarz_2009, chen2018, bruguera_2020, lang_1999]
* selection_replication / overlap choice — radix 16 built as two overlapped radix-4 selections with the second replicated per candidate digit, speculation confined to a narrow q-path [taylor_1985, lang_2007b, liu_2012, cortadella_1994]
* shared_div_sqrt_table Bool — a merged divide/square-root table, or division constants plus a square-root offset table [gerwig_2004, bruguera_2023]
* residual_representation {carry_save, borrow_save} and asymmetric positive/negative (p/n) inspection precision — both representations need identical truncation, and unequal precisions are allowed [burgess_1995]
* decimal repeated-subtraction / trial-digit selection values for decimal_digit_recurrence.digit_select [meggitt_1962]
