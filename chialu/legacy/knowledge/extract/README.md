# Corpus extraction: methodology

The extraction turns the pdf corpus in `knowledge/pdf` into notes under
`knowledge/notes`, one per paper and one per chapter of a long
document, written against the family vocabulary of `chialu/spaces`.
The notes are build intermediates: a later reduce pass merges every
note that names a family into that family's `knowledge/arch` md, and a
human reviews every `new_families` and `space_gaps` entry before the
vocabulary changes. `chialu/extract.py` runs every pass; codex
(`codex exec -m gpt-5.6-sol`) is the extractor.

## Document kinds

`python3 -m chialu.extract inventory` classifies every pdf into
`knowledge/pdf/inventory.tsv` (and `papers.txt` / `books.txt`) by
citation keywords, page count and a hand-kept override table:

| kind | count | route |
| --- | --- | --- |
| paper, report | 623 | paper prompt, one call per document |
| book (full or excerpt) | 11 | segment, triage, chapter prompt per chapter |
| thesis | 3 | same as book |
| standard | 3 | segment, standard prompt per clause |
| slides | 2 | paper prompt as one segment, once a handle exists |

Documents of one page are stubs and are skipped. Documents without a
bibliography handle carry the provisional key `file_<stem>` until a
handle is added to a survey bibliography; the note is re-keyed then.

## Papers

`run` renders `paper_prompt.md` per handle: the vocabulary and the
rules first (identical across the corpus, so the prefix caches), then
handle, citation, domain hint and the `pdftotext -layout` text, capped
at 900k characters. One note per paper lands in
`knowledge/notes/<handle>.md`. The identity check compares the
document with its citation; on mismatch the note records the real
citation in `actual_citation` and extracts the document anyway, so a
wrongly matched file still yields a note and the mismatch list drives
the re-keying of `knowledge/pdf/handles.json`.

## Books, theses, slides

A long document is not organized around one claim and exceeds one
call, so it goes through three persisted passes. Each pass writes
`knowledge/extract/segments/<key>.json`, which is committed so the
plan is reviewable and the chapter runs are reproducible.

1. `segment <key>|all` fixes chapter boundaries as pdf page indices.
   A document of at most 60 pages is one segment. A pdf outline with a
   chapter level (8 to 60 numbered entries) gives the boundaries
   mechanically. Otherwise `toc_prompt.md` runs once: it receives the
   first 40 pages and the first two lines of every page, and returns
   the document identity plus the chapter list as pdf indices under
   `schemas/toc.schema.json`. The identity field is how the
   unidentified thesis (`adder_arch.pdf`) gets its citation.
2. `triage <key>|all` decides which segments to extract.
   `triage_prompt.md` receives the vocabulary and a 500-word excerpt
   of every segment and returns, per segment, `extract`, the families
   it would inform and a one-sentence reason
   (`schemas/triage.schema.json`). Standards and single-segment
   documents skip triage: every non-front/back segment is extracted.
3. `run-books [--parallel N] [--only key]` runs `chapter_prompt.md`
   per planned segment (`standard_prompt.md` for standards). The
   chapter text carries `<<PAGE i>>` labels so page references stay
   pdf indices. The note lands in `knowledge/notes/<key>__<seg>.md`
   with front-matter `handle: <key>#<seg>` and `parent: <key>`.

The chapter prompt keeps the paper prompt's family blocks and adds
what a textbook contributes and a paper does not: a `## taxonomy`
section that reproduces the chapter's own classification of variants
with each leaf mapped to a vocabulary family, a `## primary_sources`
section listing the papers the chapter credits (handle discovery for
the bibliography), and result rows in abstract cost units (full-adder
delays, gate counts, `log2 n` expressions) with technology `abstract`.
The `authority: textbook` value tells the reduce pass to prefer these
notes for mechanism wording and terminology.

Theses use the chapter prompt with `authority: thesis`; a thesis's
survey chapters are taxonomy sources and its contribution chapters
are read like papers. Slides use the paper prompt as a single segment
with `authority: slides`.

## Standards

IEEE 754 and the OCP Microscaling specification fix formats,
rounding, operation semantics and exceptions rather than
microarchitectures, so `standard_prompt.md` extracts a contract per
clause: parameter tables for every format, rounding definitions
quoted, operation and special-value rules, exception behaviour, each
row marked `shall` / `should` / informative. The prompt describes the
verification model of `chialu/verify/formats.py` in five lines and
asks for a `## model_gaps` section, which is the list of normative
requirements the model does not represent.

## Reduce: notes -> family and variant docs

`python3 -m chialu.extract reduce-index` gathers, per family, every
note block that names it (ordered textbook > thesis > landmark >
survey > incremental), the chapter taxonomies that map onto it, the
enum values the notes pin (the variant candidates), the raw space-gap
bullets that mention it, and the handle -> citation lines, into one
bundle under `run/extract/reduce/<family>.md`, plus `INDEX.tsv`,
`new_families.tsv` and `unknown_families.tsv`. Writer subagents (at
most three at a time, 14 or 15 families each) turn a bundle into the
family doc `knowledge/arch/<domain>/<family>.md`, one variant doc per
named variant under `knowledge/arch/<domain>/<family>/<variant>.md`,
and a review file `knowledge/extract/gaps/<family>.md`, following
`reduce_prompt.md`; `python3 -m chialu.archdocs` lints titles,
references and variant pins after every batch. The 289 new-family
proposals found in the notes are reviewed per domain from
`run/extract/reduce/newfam_<domain>.md` into
`knowledge/extract/new_families/<domain>.md`: absorbed / new value /
new family (with a paste-ready `Architecture(...)`) / rejected. The
spaces are never edited by a subagent; a human applies the plans.

The thirteen domain surveys that seeded the spaces now live under
`docs/surveys/` as background prose; their bibliographies are
`knowledge/bib/<domain>.md`, the citation record the loaders read.
`knowledge/notes/_rekey/` holds the notes of papers whose file on
disk turned out to be a different work; they wait for handle
re-keying and are not indexed.

## Validation and follow-up

* A note is accepted only when it starts with front matter and its
  `handle:` line matches the job; anything else is kept under
  `run/extract/` as `<key>.out.md` with the codex log beside it.
* `python3 -m chialu.extract books` reports segmentation, triage and
  note status per long document.
* Scanned pdfs without a text layer (`unreadable`) need OCR before a
  rerun; the driver skips a document whose note already exists, so a
  rerun after fixing inputs only touches what is missing. `segment`
  refuses a document whose text layer is empty, because a
  table-of-contents pass over empty pages returns a chapter list
  invented from the model's memory of the book (thornton_1970 did
  exactly that before the guard existed). Known scanned files:
  thornton_1970, karatsuba1962, muller_1999; `ocrmypdf` on those
  three, then `segment --force` / `run`, closes the gap.
* The mismatch list (`status: mismatch` across notes) and the
  identity fields of the table-of-contents pass feed the manual
  re-keying of `handles.json` and the bibliography.
