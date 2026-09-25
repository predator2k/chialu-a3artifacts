# Families, spaces, cards, generators and the corpus pipeline

This document names the objects the knowledge base, the family spaces
and the family library are made of, how one family name ties them
together, and which of them a run reads. Three layers exist: the
definition layer (the spaces), the realization layer (the generators
and their modules), and the knowledge layer (the corpus, its notes and
the cards). Counts are as of 2026-09-12, after the deferrals of
`docs/deferred-families.md` (21 families, nine choice values and the
three groups no unit template opens).

## 1. The definition layer: the spaces

| Object | What it is | Example (adder domain) |
| --- | --- | --- |
| family | one microarchitecture, a `Family(...)` in `chialu/spaces/*.py` | `parallel_prefix` |
| design choice (pin) | a design axis inside a family, a member of `design_choices` (an enum, a boolean or a range) | `parallel_prefix.topology` |
| slot (component) | a member of `components`, which names another space; the compiler turns it into the nested variables `core.<kind>.<index>.<slot>.family` and `...<slot>.<choice>` | `carry_skip.block_adder` names `block_adder_space()` |
| space | the family list of one domain or one component kind; 13 files hold 35 space factories; `adir.spaces.Space.variables()` compiles a space into ADIR's conditional variables, a run file binds them, and a candidate declares its values in `VAR` lines | `adder_spaces.py` holds `cpa_space()`, `block_adder_space()`, `incrementer_space()`, `comparator_space()` |
| variant | not an object of the spaces: the name of one enum value of one choice that the literature calls a structure of its own | `kogge_stone` is `parallel_prefix` with `topology: kogge_stone` |

The spaces were transcribed from 13 domain surveys (the files
`docs/surveys/<domain>.md`, deleted in the commit of 2026-09-09; their
bibliographies survive under `legacy/knowledge/bib/`) and revised by
hand from the plans the corpus pipeline wrote (section 4). Across the
spaces and their sub-slot spaces there are 198 family names.

## 2. The realization layer: the generators

Two things are called generators.

* The template generators in `chialu/modules/generators.py` write the
  seed, the checker and the verification files of a unit from the run
  file's bindings.
* The family library under `chialu/targets/rtl/families/` realizes one
  family as one module: parametric SystemVerilog (`adder.sv`,
  `shifter.sv`, `comparator.sv`, `logic.sv`) where a parameter set
  expresses the family's combinations, and Python generators otherwise
  (`prefix.py`, `mul.py`, `mul_ext.py`, `adder_ext.py`, `approx.py`,
  `subword.py`, `fp.py`, `div.py`, `posit.py`, `decimal.py`,
  `redundant.py`, `sfu.py`, `dot.py`, `count.py`, `comparator.py`). `has_module(kind, family)` in
  `families/__init__.py` says which families have a realization; the
  seed instantiates the module of a declared family, the family menu
  marks such families `[library]`, and `chialu.characterize` synthesizes
  every module into the database `chialu/synth/<pdk>.jsonl`.

155 of the 155 declarable families have a realization. Inside a module,
a component of a library kind is realized in one of three ways
(`docs/slot-audit.md`): an instance chosen through a slot pin, an
instance with a hard-coded family, or behavioral text.

## 3. The knowledge layer: `chialu/knowledge`

`chialu/knowledge` is the directory a run hands the agent (the run
file's `knowledge:` key). It holds the cards, the move library and the
papers.

| Path | Content | Count |
| --- | --- | --- |
| `arch/<domain>/<family>.md` | the family card: mechanism, trade-offs, a `## references` list of paper handles; the plain `.md` files under `arch/adder/` are these | 198 |
| `arch/<domain>/<family>/<variant>.md` | a variant card with the front matter `family:` and `pin:`; the sub-folders under `arch/adder/` are these (`parallel_prefix/` holds brent_kung, han_carlson, knowles_mixed, kogge_stone, ladner_fischer and sklansky) | 341 |
| `moves/<id>.md` | a micro-optimization pattern (`abs_by_sign_mask`, ...); a declaration's `MOVE` line names one, `priors.MOVES` offers them as tactics | 33 |
| `pdf/` | the collected papers and `handles.json` (handle to file name) | 666 |

`chialu.archdocs` lints the cards against the spaces: every family of
every space has a card, every variant card's `family:` and `pin:` match
an enum member, every enum member is described, and every structural
claim a card states is met by its realization's module header. Of the
817 enum members (deduplicated by family, choice and value), 60 are
numbers, 288 have a variant card and 469 are named by their family
card's `## design choices` table or its prose; none stands in the
knowledge path as its identifier alone. The lint exits nonzero on an
undescribed member no allowlist row covers.

## 4. The corpus pipeline: `legacy/knowledge`

`chialu/extract.py` drives an offline map-reduce over the papers. Its
inputs, prompts and outputs live under `legacy/knowledge`, outside the
knowledge path a run hands the agent.

| Path | Content | Place in the pipeline |
| --- | --- | --- |
| `extract/README.md` | the methodology | |
| `extract/register_prompt.md`, `toc_prompt.md`, `triage_prompt.md` | registering a paper and its handle; finding the chapter boundaries of a long document; deciding which segments are worth extracting | preparation |
| `extract/schemas/toc.schema.json`, `triage.schema.json` | the JSON shapes the toc and triage steps must return | preparation |
| `extract/segments/<key>.json` | the segment plan of a book, thesis or standard: page ranges, segment kind, whether to extract, the families a segment informs | preparation output, 18 files |
| `extract/paper_prompt.md`, `chapter_prompt.md`, `standard_prompt.md` | the map step: one paper, one chapter or one standard becomes one note | map |
| `notes/<key>.md`, `notes/<key>__<seg>.md`, `notes/_rekey/` | the note of one document: mechanism, the enum values it pins, parameters, result rows, `## new_families`, `## space gaps`; chapter notes carry the segment id; `_rekey` holds notes whose file turned out to be another work | map output, 681 notes (67 chapter notes) |
| `extract/reduce_prompt.md` | the reduce step: one bundle per family (every note block naming it, the values the notes pin, the gap bullets) becomes the family card, one variant card per named variant and one gap review | reduce |
| `extract/gaps/<family>.md` | the review a card writer leaves for the space: proposed choices, values and ranges (the kulisch width below 512 bits, the intrinsic-line realignment of the multi-term dot) | reduce output, 228 files, applied by hand; `docs/knowledge-gaps.md` records the triage |
| `extract/new_families/<domain>.md`, `<domain>.applied.md` | the review of the 289 new-family proposals of the notes (absorbed, new value, new family, rejected) and the record of what was applied to the space file | after reduce, applied by hand |
| `bib/<domain>.md` | handle to citation, one file per domain; `chialu/papers.py` reads it for the presets and `archdocs` checks card references against it | throughout, 13 files |
| `run/extract/reduce/` | the reduce bundles and `INDEX.tsv`; not in the repository | intermediate |
| `deferred/` | the cards and the `Family(...)` blocks of the deferred families (`docs/deferred-families.md`) | record |

The variant rule of the reduce prompt is the reason the cards cover a
minority of the enum members: a variant card is written only for an
enum value that at least one note pins with a citation and that the
literature names as a distinct structure rather than a parameter
setting.

## 5. How the layers correspond

* A paper enters as a PDF and a handle, is segmented and triaged, and
  becomes a note; the notes of one family become its family card, its
  variant cards and a gap review; the gap reviews and the new-family
  reviews are applied to the space file by hand, and the applied record
  says which lines were taken.
* A space compiles to variables; a run file binds them; a candidate
  declares values; the seed instantiates the module of each declared
  family; the database holds the module's area and delay; the menu
  marks the family `[library]`.
* One family name is the key everywhere: `Family(name)` in the space,
  `arch/<domain>/<name>.md` in the knowledge path, the entry in the
  generator's family table, the value of a `*.family` variable, the
  `family` field of a database row.
* A variant name is a key in the knowledge layer only: the variant
  card's `pin:` names the choice and the value; the spaces know the
  value as an enum member, the generators read it as a pin, and no code
  reads the variant card by its pin.

Three consistency checks exist today. `chialu.archdocs` checks the cards
against the spaces (family coverage, pin membership, the enum members'
description, and a card's structural claims against its realization's
module header).
`chialu.targets.rtl.families.coverage` checks the generators against
the spaces (every family renders, every slot is read and every member
renders, every pin read is declared, every choice member changes the
text, the components are slot-chosen library instances, module names are
unique per text, the `[library]` mark agrees with the realizer). The review node
(`chialu.review.<agent>`) reads a module with its family card and says
whether the text realizes the family, at the family level. The claim
check is of the module header's own words, so it catches a card whose
claim the header contradicts (a card that says "the internal adder never
spans the exponent range" against a module header that says "the window
is raised to the exact width") and it does not prove the netlist below
the header.

## 6. What a run reads and what it does not

| Status | Objects |
| --- | --- |
| read by every run | the spaces (the variables); both kinds of generators; the family cards (`prompts.card_of` puts a card path in the family menu, `review._card` hands the card to the review model, ADIR's composer ranks every `.md` under the knowledge root by file stem against the variables' values under `knowledge_depth: index` or `cards`); the move library; `legacy/knowledge/bib` (through `chialu/papers.py`); `pdf/handles.json` |
| read only as files | the variant cards: they enter the composer's ranking and the agent's directory, and no code consumes their `pin:`; `archdocs.variant_table()` is used by the lint alone |
| development time | `chialu.archdocs` |
| offline, never in a run | `chialu/extract.py` with its prompts, schemas, segments and notes (only when the corpus is re-extracted); the gap and new-family reviews (input and record of manual space edits); `legacy/knowledge/deferred` |
| deleted | `docs/surveys/` |

## 7. The synthesis database

`chialu/synth/<pdk>.jsonl` is a list of rows, one per synthesized
module: `kind`, `family`, `variant`, `pins`, `module`, `width`,
`clock_ps`, `effort`, `pdk`, `area_um2`, `delay_ps`, `cells`, `seconds`,
`ok`, `detail`. The nangate45 file holds 4648 rows over 24 kinds at the
widths 8, 16, 32 and 64 (the RNS kinds stop at 32; the dot kind runs
at int8x4, fp16x4 and fp32x1; the SFU kind at fp8, fp16 and fp32).
`chialu.timing` (the `chialu_timing` PromptSource) shows the fastest
variant per family at the run's clock, and `chialu.prune` narrows a run
file's family domains from it. The database's limits and its redesign
are in the work plan (`docs/work-plan.md`).
