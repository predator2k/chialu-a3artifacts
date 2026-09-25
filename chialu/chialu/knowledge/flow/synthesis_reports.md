# Reading the synthesis reports of a candidate

Area and delay are now separate medians of five mappings. `synth_ppa.runs` retains all
five receipts and `cells_run_index` identifies the physical mapping supplying cells.
These diagnostic reports still describe the separate name-kept base mapping recorded
in `report_run.attribution_run`, not a physical netlist corresponding to both medians.
Replay receipts with `python -m chialu.synth_records`; keep the referenced artifact store.

The evaluation of every candidate synthesizes it (yosys, ABC mapping on
the run's liberty at the run's clock) and returns, beside the scored
numbers `synth_ppa.area_um2` and `synth_ppa.abc_delay_ps`, four texts
the prompt carries as feedback; the long ones arrive as files under
`feedback/` of the call's directory:

* `synth_ppa.summary`: the metric's numbers, the numbers of the netlist
  the reports describe, and one row per unit instance of the flattened
  design (`u_m0_l0_adder`, `u_m1_l0_multiplier`, ...): area, its share,
  cells, the cells ABC merged with another unit (`shared`), the latest
  arrival at the unit's input ports (`in arr`) and at its output ports
  (`out arr`), in ps. The `top glue` row is the logic outside every
  unit: operand decode, the op mux, the flags.
* `synth_ppa.critical_path`: one line, the latest endpoint with the
  path as a chain `owner(cells, ps)` per segment, a segment being the
  consecutive cells one instance owns; `shared(k)` is logic ABC merged
  between k instances, `top` the glue.
* `synth_ppa.paths` (`feedback/synth_ppa.paths.txt`): the 20 latest
  endpoints as such lines, then the first three cell by cell: arrival,
  incremental delay, the input and output edge (`r->f`), the cell type,
  the owner, the output net, its fanout, load (fF) and slew (ps).
* `synth_ppa.area_by_hierarchy` (`feedback/synth_ppa.area_by_hierarchy.txt`):
  area and cells per instance as a tree, then the table from structure
  member (the file under `members/`) to module to instances.

## What to look for

* The unit that owns the longest segment of the critical path is where
  delay goes; its `out arr` in the summary is near the total.
* A cell with fanout above 20 and slew above 300 ps (an op decode or a
  select net driving many loads) costs hundreds of ps; ABC does not
  buffer, so the RTL duplicates the decode or restructures it.
* A long run of cells with alternating edges inside one unit is a
  carry or increment chain; a faster family or a shorter chain fixes
  it, a rewrite of the surrounding logic does not.
* Two units in series on the path (an fp adder feeding the rounder,
  an unpacker feeding a multiplier) share the budget; a merged stage
  or a moved boundary shortens both.
* A large `shared` count means ABC merged logic between units; a
  change in one of them may unshare it and grow the area.

## How the numbers relate to the metric

The reports come from a second mapping of the same pre-mapping
netlist with `keep` on the unit instances' port nets, which is what
lets a mapped cell keep an owner; ABC's own mapping (the metric) drops
every hierarchical name. The reports' area and delay stand within a
few per cent of the metric (measured: +0.1 % and +1.9 % on an integer
ALU, +3.2 % and +0.8 % on a float one), and the header of every text
states both. The timing follows ABC's delay model (no wire load, the
fanout pins' capacitances as load, inputs at 0 ps, outputs unloaded);
names inside a unit are not kept, so a path shows its cells with the
unit as owner rather than the RTL signal names.
