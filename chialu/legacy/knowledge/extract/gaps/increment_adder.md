# increment_adder: proposed changes to the space

* shared negation/rounding incrementer and variable-precision incrementer with per-lane increment signals [kaul_2012]
* split carry propagation (wide adder plus incrementer selected by the lower carry) [lang_2004, quinnell_2007]
* early forwarding of the unrounded result with correction terms [trong_2007]
* increment_return_path {addend_pipeline, multiplicand_pipeline} [montoye_1990]
