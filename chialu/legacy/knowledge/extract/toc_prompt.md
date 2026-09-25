# Table-of-contents pass: chapter boundaries as pdf page indices

You receive the front pages of a long document (book, thesis, or
standard) and a one-line sample of every page. Return the document's
identity and its chapter segmentation as pdf page indices, so that a
later pass can extract one chapter at a time.

## Rules

1. Page indices are the `<<PAGE i>>` / `pi:` numbers in this prompt
   (0-based pdf indices), never the printed page numbers. Use the
   table of contents to learn the chapter titles and printed page
   numbers, then locate each chapter's first pdf page in the per-page
   sample, where chapter headings appear as the first line of a page.
   When the sample does not show a heading, derive the offset between
   printed and pdf page numbers from pages where both are visible and
   apply it.
2. A segment is a chapter (or a standard's top-level clause / a
   thesis's chapter). Do not split below chapter level. Front matter
   (preface, contents, lists of figures) is one segment of kind
   `front`; bibliography and index are one segment of kind `back`;
   appendices are segments of kind `appendix`.
3. Segments tile the document: the first starts at page 0, each `end`
   is the page before the next `start`, and the last ends at page
   {{N_PAGES_MINUS_1}}.
4. Copy chapter titles as printed, without the chapter number.
5. Output JSON only, matching the schema you were given.

## Document

key: {{KEY}}
citation on file: {{CITATION}}
total pdf pages: {{N_PAGES}}

### Front pages (text)

{{FRONT}}

### Per-page sample (first two non-empty lines of every page)

{{HEADS}}
