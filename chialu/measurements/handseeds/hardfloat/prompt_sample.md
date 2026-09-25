<!-- prompt_config {"operator": "free", "ambition": "moderate", "show": "path", "context_programs": 1, "feedback_depth": "files", "member_focus": "none", "show_plan_table": true, "knowledge_depth": "path", "decisions": "kinds", "tactic_id": null, "instruction_id": null, "focus": null} -->

## Response

State the reasoning in one short paragraph, then the change as SEARCH/REPLACE blocks, each in exactly this form; every SEARCH block must match the current program verbatim, whitespace included:

<<<<<<< SEARCH
(lines copied from the current program)
=======
(the replacement lines)
>>>>>>> REPLACE

Then one note per mutable region you changed, which is what a later round reads instead of the diff: the replaced lines in full, the lines that replaced them in full, and why. Abbreviate neither side. Say in the reason what you expected to gain, so a round that finds it did not work knows what was already ruled out. The name after HISTORY is the region's -- this program has one, `*`.

<<<<<<< HISTORY *
replaced:
(the lines as they were)
with:
(the lines as they now are)
why: (what this changes and what you expect from it)
>>>>>>> HISTORY

## Operator: free

Improve the candidate in any way that raises the score under the constraints.

## Ambition: moderate

Rework one part of the design: re-express a stage of its datapath, merge or split a stage, replace the algorithm of one block, or move logic across the boundary between two stages. The rest of the design stays.

## Current program

* score 1.0000; goal [5420.548, 2800.75]; feasible

The program is the file `program.sv` (2629 lines; mutable regions: `*` (lines 1-2628)). Read it with your file tools, the region in focus as a slice by its lines; a SEARCH block must match its text verbatim.

This call's directory is `$CHIALU_HOME/tmp/handseeds/verified/hardfloat/agent/20260924-111124-ad06b5-seed:hardfloat_hand_seed`; the paths below and those in the system text are relative to it. This round's files:

* `context/parent.md` (389 chars, 8 lines): the parent: its metrics per node and its unsatisfied constraints
* feedback `conformance.detail`: bit-exact against the reference
* `feedback/synth_ppa.summary.txt` (1.0 KB, 9 lines): the parent's feedback `synth_ppa.summary`
* feedback `synth_ppa.critical_path`: 1. y[0]                     2986.4 ps  from a[7]                  54 cells   top(54, 2986 ps)
* `feedback/synth_ppa.paths.txt` (24.3 KB, 214 lines): the parent's feedback `synth_ppa.paths`
* `feedback/synth_ppa.area_by_hierarchy.txt` (909 chars, 10 lines): the parent's feedback `synth_ppa.area_by_hierarchy`

## Notes from the search


Decide for yourself whether to keep optimizing along one of these histories -- a region whose entries show steady gains, or one whose last attempt failed for a reason you can now avoid -- or to leave them and change a region nothing has touched yet. Say which you chose in one clause.
