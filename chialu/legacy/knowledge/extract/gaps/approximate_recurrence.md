# approximate_recurrence: proposed changes to the space

* choice `replacement_region: {vertical, horizontal, square, triangle}` — every evaluated design locates its approximate or truncated cells by one of these array geometries, and the choice moves the error distribution more than the cell type does [chen2016, chen2018, jiang2017, jiang2020]
* choice `approximation_action: {cell_replacement, cell_truncation, error_compensation}` with a `truncation_depth` parameter and an `error_compensation_cluster: {none, EXSDAC_AXSDAC_ECPLC}` choice — truncation removes cells rather than replacing them, and the high-radix design adds a compensating cluster near the quotient-generating residual bits [chen2016, chen2018]
* `replaced_depth` should admit odd values and depths above the radix-2 range, since d = 1, 3, 5 and 7 and depths 11 to 14 are evaluated [chen2016, chen2018, jiang2019]
* a base-array choice or slot distinguishing restoring/non-performing arrays from non-restoring arrays, which determines the remainder-correction circuit and the comparative power [chen2016]
* choice `operation: {divide, sqrt}` — the restoring square-root array with AXSC3 replacement (AXSR3) is the same family applied to a root recurrence [jiang2019]
* confirm that `cell` values axsc1/axsc2/axsc3 are the review's AXCS1/AXCS2/AXCS3 so the review's cell pins land inside the domain [jiang2017]
