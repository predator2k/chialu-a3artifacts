# Reduce: one family bundle -> one family md

The writer turns `run/extract/reduce/<family>.md` (the bundle) into
`chialu/knowledge/arch/<domain>/<family>.md` (the registry doc). The
bundle carries the family's structural definition from
`chialu/spaces` (authoritative), every note block that names the
family ordered by authority (textbook > thesis > landmark > survey >
incremental), the chapter taxonomies that map onto it, the raw
space-gap bullets that mention it, and the `handle -> citation` lines
to copy. The doc is what `chia_loop/kb_prompt.py` inlines into the
agent's prompt, so it is written for a designer choosing a
microarchitecture, in the register of the five existing docs
(`arch/adder/parallel_prefix.md`, `arch/mul/booth_recoded_parallel.md`,
`arch/sfu/cordic.md`, `arch/sfu/gpu_multifunction_interpolator.md`,
`arch/checker/residue.md`).

## File shape (parsed by `chialu.archdocs`)

```
# <family>

<paragraph 1: the mechanism>

<paragraph 2..n: trade-offs, when it wins, what the tunables do>

## references

<handle> -> <citation copied verbatim from the bundle>
```

* Line 1 is `# <family>`, exactly the filename stem.
* Paragraph 1 is the mechanism, at most 700 characters, because the
  prompt renderer inlines only the first paragraph and truncates at
  700. It says what the structure computes and how (recurrence,
  encoding, pipeline shape) in the terms the textbook/thesis blocks
  use; a designer reads it and can sketch the datapath.
* Paragraphs 2 and on (two to four paragraphs, 150 to 350 words in
  total) cover: what each design choice trades (qualitatively, in
  the choice names the structure block lists, without restating the
  enumerations), where the family wins and loses against its
  neighbours, the accuracy/fault contract it implies where the family
  is approximate or a checker, and the execution style (iterative
  families say so).
* `## references` lists three to eight handles: the origin paper,
  the textbook/thesis chapter that defines it, and the results the
  paragraphs lean on. Citations are copied verbatim from the bundle's
  `## citations` section; never invented; a handle not in that
  section is not used.

## Evidence rules

* Every sentence is supportable by a block in the bundle or by the
  structure section. Nothing from outside the bundle, no general
  knowledge, no guessing at numbers. Where blocks disagree, the
  higher-authority block wins and the disagreement is not mentioned.
* Numbers stay qualitative except for at most three anchors that
  carry their context (technology node or "abstract" units) inline,
  e.g. "about 2x the area of ripple carry in FA units". No tables.
* A note block whose status is `mismatch` describes the document on
  file, not the cited paper: its content is usable, its handle is
  not cited unless the `actual_citation` is the same work. When in
  doubt, cite a different block.
* A family with no blocks is written from its structure section and
  the survey report of its domain (`docs/surveys/<domain>.md`, found
  by grepping the family name), in the same shape, with references
  taken from that domain's bibliography (`chialu/knowledge/bib/`).

## Variant docs: `chialu/knowledge/arch/<domain>/<family>/<variant>.md`

A VARIANT is a named microarchitecture inside a family: one enum
value of one design choice that the literature names as a structure
of its own (Kogge-Stone, Brent-Kung and Sklansky are `topology`
values of `parallel_prefix`; Wallace and Dadda are `geometry` values
of `csa_reduction_tree`). A yaml instance can select one (`variant:
kogge_stone`), a list (`variants: [kogge_stone, brent_kung]`), or the
whole family (`family: parallel_prefix`, every variant open to the
loop), so each variant needs its own doc.

The bundle's `## variant candidates` section lists every enum value
the notes pin, with counts and handles. Write a variant doc for each
candidate that (a) at least one block pins with a citation and (b)
the literature names as a distinct structure rather than a parameter
setting. Skip values that are parameters or circuit styles with no
structural identity of their own (a fanout cap, a cell style), and
skip values no block pins. A family with no such candidates gets no
variant folder.

```
---
family: <family>
pin: {<choice>: <value>}
---
# <variant>

<paragraph 1: what this variant's structure is and what makes it distinct, at most 500 characters>

<paragraph 2: trade-offs against the sibling variants, when it is the pick; 60 to 150 words>

## references

<handle> -> <citation copied verbatim from the bundle>
```

* The file name is the enum value verbatim (`kogge_stone.md`); the
  title line equals it; `pin` uses the choice name and value verbatim
  from the structure section (the lint checks both against spaces).
* Evidence rules are the family doc's: only blocks that pin or
  discuss this value, citations copied verbatim, one to five
  references (one is enough when only one block supports it).
* The family doc still names its variants in prose; the variant doc
  is where a designer who has already chosen the family reads on.

## Side file: `chialu/knowledge/extract/gaps/<family>.md`

One file per family, for human review, never read by the prompt:

```
# <family>: proposed changes to the space

* <choice/value/slot/family the evidence suggests adding or changing> — <one sentence why> [handles]
```

Sources are the bundle's `space_gaps` section and the `new_choices` /
`[outside domain]` values inside the blocks, deduplicated and merged
into one bullet per distinct proposal. Write `none` when the evidence
proposes nothing.

## Check

After writing a batch, `python3 -m chialu.archdocs` must report no
ORPHAN and no BAD REF lines. The parser requires the title line to
equal the filename stem and every `## references` line to match
`handle -> citation`.
