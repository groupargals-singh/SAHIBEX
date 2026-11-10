# SAHIBEX Reading / Document Specialist Routing — 2026-11-11

## Scope
Connect explicit reading and document-summary requests to the existing `reading` and `document_file` specialist handlers.

## Implemented
- `Read this text: ...`, polite English requests and supported Hinglish and Hindi text requests route to `reading`.
- `Summarize this document: ...` / `Review this document: ...`, polite English and supported Hinglish and Hindi requests route to `document_file`.
- Payload extraction is limited to text after the explicit colon/newline delimiter and capped at 12,000 characters.
- Missing payload is represented as empty text; handlers return `SOURCE_TEXT_REQUIRED` / `DOCUMENT_TEXT_REQUIRED` rather than guessing.
- Document extraction reports source-grounded lines only. It does not generate a semantic summary or fact-check claims.
- Both handlers explicitly report that they do not read/write/delete files or execute supplied content.
- Existing Mother Brain authorization and verification gates still precede automatic specialist dispatch.

## Validation
- Focused router + InternalBrainTeam regression: **125 passed**.
- Full repository regression: Full repository regression: **2,351 passed in 145.57s**, exit 0. `compileall -q core app tools scripts tests`: PASS. All repository shell scripts passed `bash -n`. `git diff --check`: PASS. Hindi/Hinglish/English payload extraction covered.

## Limitations
- This is supplied-text processing only. File-path opening, PDF/DOCX parsing, library access, OCR, semantic summarization and factual verification are not added by this change.
- No P-series release gate is promoted.
