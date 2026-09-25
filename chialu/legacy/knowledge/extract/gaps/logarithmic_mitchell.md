# logarithmic_mitchell: proposed changes to the space

* `correction_scheme` value `iterative_residual` for Mitchell's own recursive correction, which adds a scaled logarithmic approximation of x1 x2 (or x1' x2' after a mantissa carry) in a second pass [mitchell1962]
* choice `secondary_correction: {none, divided_approximation, table_of_correction_values, mitchell_error_correction}` so operand decomposition can be combined with a second correction, which the space models as one value only [mahalingam2006]
* choice `decomposed_product_schedule: {parallel, sequential}` for the area/delay trade of computing the two decomposed products on separate or shared hardware [mahalingam2006]
* choice `log_approximation: straight_line_characteristic_plus_fraction` naming how the operand logarithm is obtained without a table [mitchell1962]
