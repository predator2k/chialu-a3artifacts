# The passes a recipe may use

The recipe is a Yosys script. Yosys elaborates the RTL and hands the
combinational logic to ABC through the `abc` command; ABC's `-script`
takes the `+cmd,arg;cmd` form (commas stand for blanks, semicolons
separate commands). The node appends `opt_clean`, `stat -liberty` and
`write_verilog`, so the recipe ends at the `abc` command.

## Yosys side

* `synth -top {top} -flatten -noabc [-noshare]`: the standard coarse
  flow (proc, opt, fsm, memory, techmap, opt). `-noshare` skips the
  SAT-based SHARE pass, which merges same-type cells on mutually
  exclusive branches; it can run long on wide multipliers.
* `opt -full`: the optimization passes with the expensive options
  (opt_expr -full, opt_merge -share_all).
* `alumacc`, `wreduce`, `peepopt`, `share`: individual coarse passes;
  `synth` runs them, so a recipe repeats one only for a reason.
* `abc -liberty {liberty} -script ...`: the mapping; the script decides
  the area and the delay.

## ABC side

Optimization on the AIG, before mapping:

* `strash`: structural hashing into an AIG (first).
* `balance` (`b`): balances AND trees to reduce depth.
* `rewrite` (`rw`), `rewrite -z` (`rwz`): local rewriting with 4-input
  cuts; `-z` allows zero-cost replacements.
* `refactor` (`rf`), `refactor -z` (`rfz`): larger-cone refactoring.
* `resub -K <k> -N <n>` (`rs`): resubstitution with k-input cuts and up
  to n added nodes; the compress2rs script is resub-heavy.
* `dc2`: don't-care based rewriting (a resyn2 alternative, stronger and
  slower).
* `dch -f`: computes structural choices so the mapper sees several
  equivalent structures per node; pair with a choice-aware mapper.
* `fraig`, `&fraig -x`: SAT sweeping (functionally reduced AIG);
  `&fraig -x` can run long on arithmetic.
* `&get -n` / `&put`: move between the old and the new (`&`) AIG
  package; the `&`-passes (`&dc2`, `&dch`, `&syn2`, `&nf`, `&if`)
  need `&get` first and `&put` after.

Mapping:

* `&nf -D <ps>`: the delay-oriented standard-cell mapper (the default
  of yosys's liberty flow); `-C <cuts>`, `-F <flow rounds>`, `-p`
  (pin permutation) raise the effort; `-D` is the delay target.
* `amap`, `map`: the older library mappers (`map -a` area recovery).
* `topo; stime`: order the mapped netlist and print `Delay = ... ps`
  and `Area = ...`; keep them last so the log carries the numbers.

The names `resyn2` and `compress2rs` are aliases of ABC's `abc.rc`,
which yosys's ABC does not load: `compress2rs` alone is "unknown
command". Write the passes out. `resyn2` is `balance; rewrite;
refactor; balance; rewrite; rewrite -z; balance; refactor -z;
rewrite -z; balance`. `compress2rs` is `balance -l; resub -K 6 -l;
rewrite -l; resub -K 6 -N 2 -l; refactor -l; resub -K 8 -l;
balance -l; resub -K 8 -N 2 -l; rewrite -l; resub -K 10 -l;
rewrite -z -l; resub -K 10 -N 2 -l; balance -l; resub -K 12 -l;
refactor -z -l; resub -K 12 -N 2 -l; rewrite -z -l; balance -l`.
In the `+cmd,arg;cmd` form of `abc -script`, commas stand for blanks:
`resub,-K,6,-l`. The `&`-prefixed passes work on the `&get -n` copy
and need `&put` before old-style passes run again; `&balance` and
`&compress2rs` do not exist.

## What moves area

The multiplier and the adders dominate the block. Area falls when the
AIG is smaller before mapping (resub, dc2) and when the mapper can
choose among structures (dch before &nf). Delay falls with balance and
with a tighter `-D`. A recipe that repeats a pass with no effect only
costs seconds; the pass trace in the feedback shows the cell count
after each pass.
