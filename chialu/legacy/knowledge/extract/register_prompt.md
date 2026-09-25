# Registration review: new-family proposals -> paste-ready space entries

The map pass asked every note to flag mechanisms the vocabulary
lacks, under `## new_families`. The reviewer turns one domain's
proposals (`run/extract/reduce/newfam_<domain>.md`: the domain's
existing families, every proposal block with its handle and
authority, and the citations) into a decision file
`chialu/knowledge/extract/new_families/<domain>.md`. Nothing in
`chialu/spaces` changes in this pass; the decision file is the input
a human uses to change it.

## Verdicts

Each proposal gets exactly one verdict:

* `duplicate` — an existing family already covers the mechanism
  (name it). The proposer used another name for the same structure.
* `variant` — the mechanism is a value of an existing family's
  choice, present or missing. Name the family, the choice, and the
  value; say whether the value already exists in the declared domain.
* `choice` — the mechanism is a new design choice (a new axis) inside
  an existing family rather than a new family. Name the family and
  sketch the choice (`name: {values}` or `Int[lo..hi]`).
* `new` — a family the vocabulary lacks: a structure with its own
  mechanism, its own tunables, and at least one citable source.
* `discard` — not a microarchitecture (a metric, a methodology, a
  software technique, a full product, an evaluation), or too thin to
  register (one sentence of evidence, no structure).

Proposals from different notes that describe the same mechanism are
merged into one entry with all their handles; the merged name is the
literature's name in `snake_case`, never a paper-specific label.

## File shape

```
# new-family review: <domain>

## summary
<counts per verdict, one line>

## new
### <family_name>
domain: <vocabulary section>
doc: <one line, the spaces `doc=` string: what it is and when it wins>
execution_style: feed_forward | fixed_iteration | variable_iteration
choices:
  <choice_name>: {<value>, <value>} | Int[lo..hi:step] | Bool   # what it trades
slots:
  <slot_name>: {<families that can fill it>}   (or "none")
mechanism: <at most 100 words, from the proposal blocks>
sources: <handle>, <handle>   (from the bundle's citations section)
proposed_by: <handle> [<authority>], ...

## variant
* <proposed_name> -> <family>.<choice> = <value> (exists | missing)  [handles]

## choice
* <proposed_name> -> <family>: <choice_name>: <domain sketch>  [handles]

## duplicate
* <proposed_name> -> <existing family>  [handles]

## discard
* <proposed_name> — <reason in one clause>  [handles]
```

## Rules

* The existing-families list in the bundle is authoritative for what
  exists; when a proposal's mechanism matches one of those families'
  one-line docs, the verdict is `duplicate` or `variant`, never `new`.
  When in doubt between `new` and `variant`, prefer `variant` and say
  what the deciding question is.
* Family, choice and value names follow the vocabulary's style:
  lower snake_case, the literature's term, no author names unless the
  literature itself names the structure after them (`kogge_stone`).
* A `new` entry's choices are only the tunables the proposal blocks
  give evidence for; nothing invented.
* Every handle written is one that appears in the bundle.
