# Databases & SQL — Guide Integration and Verification — 2026-10-03

Scope: three SQL guides had been added to the repository root as untracked
files (`SQL_Interview_Guide.md`, `SQL_Advanced_Practice.md`,
`SQL_Oracle_Window_Functions.md`), written originally as personal prep for
one specific employer's interview. The user asked to verify the repository
and fix the README and the SQL-related files.

## What changed

- **Moved and renamed** into a new `Databases & SQL/` topic folder, using
  the repository's `*_Interview_Prep.md` naming:
  - `SQL_Interview_Guide.md` → `SQL_Data_Modeling_Interview_Prep.md`
  - `SQL_Advanced_Practice.md` → `SQL_Query_Practice_Interview_Prep.md`
  - `SQL_Oracle_Window_Functions.md` → `Oracle_Window_Functions_Interview_Prep.md`
- **Baseline header** (target level / technology baseline / last verified /
  prerequisites) added to each, matching the other guides.
- **Personal and employer-specific content removed** (per `CONTRIBUTING.md`
  rule 6): links to files that don't exist in this repository
  (`Interview Stories.md`, `Payments_Modernization.md`), references to the
  author's own project stories, an employer-specific "[confirm which
  business unit]" note, and `[fill in]`/`[confirm]` markers. Where a
  question genuinely calls for personal experience, the standard
  `> Personal example to add:` placeholder is used instead.
- **Cross-links** added to the existing Transactions, JPA & Hibernate, and
  Kafka guides where those cover the same topic in more depth.
- **Sources** section added to each guide (PostgreSQL 16, MySQL 8.0,
  SQL Server, and Oracle 19c/21c/23ai documentation; Kimball Group; the
  Berenson et al. isolation-levels paper).

## Corrections

- **Oracle guide §5** said Postgres requires an alias on a subquery in
  `FROM`. PostgreSQL 16 (this guide's execution baseline) made the alias
  optional — verified by running the alias-less query on 16.14. Corrected.
- **Data-modeling guide §7** said "in SQL Server and MySQL InnoDB, the
  primary key is the clustered index." True unconditionally for InnoDB;
  for SQL Server it's only the default. Corrected.
- **Data-modeling guide, month-over-month bonus problem** divided by the
  previous month's volume without guarding zero. Added `NULLIF`.
- **Data-modeling guide §10**: the `EXPLAIN ANALYZE` output was presented as
  if captured; it's representative. Now labelled as illustrative.
- **Query-practice guide B14**: the MySQL upsert used `VALUES()` in
  `ON DUPLICATE KEY UPDATE`, deprecated since MySQL 8.0.20. Rewritten with
  the row-alias form.

## Verification performed

- **Execution on PostgreSQL 16.14** (Docker `postgres:16`): every SQL block
  in `SQL_Query_Practice_Interview_Prep.md` run against its seed data, each
  in a rolled-back transaction so blocks don't affect each other; all 25
  blocks with a stated output matched. The Part C traps-table figures were
  re-run individually and all matched.
- `Oracle_Window_Functions_Interview_Prep.md` sections 1–7 run on the same
  instance with the seed's `NUMBER` types mapped to `NUMERIC`; all outputs
  matched. Section 8 (Oracle-only syntax) was **not** run on Oracle — its
  outputs remain expected values, as the guide states.
- `SQL_Data_Modeling_Interview_Prep.md` blocks run for syntax; the
  remaining errors are expected (fragments referencing tables defined
  elsewhere, `:param` placeholders, `CREATE INDEX CONCURRENTLY` inside a
  transaction). The SCD Type 2 load was tested end to end on sample data,
  including a NULL → value change.
- `markdownlint-cli2` (repository config): 0 issues after fixing 157
  missing blank lines around fences, 9 extra H1 headings, and 7 untagged
  code fences.
- `scripts/check_internal_links.py`, `check_duplicate_headings.py`,
  `check_code_fences.py`: clean for the three guides.

## Tooling bug found and fixed

`slugify()` in both `scripts/check_internal_links.py` and
`scripts/add_toc.py` stripped **every** underscore, treating it as an
emphasis marker. GitHub's slugger (`github-slugger`, checked directly with
`npm i github-slugger@2`) keeps underscores, so a heading containing
`` `REQUIRES_NEW` `` anchors at `requires_new`, not `requiresnew`. The
checker and the TOC generator agreed with each other, so CI passed while
links were broken on GitHub. Fixed both scripts to keep underscores inside
code spans and inside words. This exposed three existing broken links,
all fixed: two entries in the Transactions table of contents (Q6, Q7;
regenerated with `add_toc.py`) and one Glossary link to Transactions Q6.

## Not done

- The three SQL guides keep their own structure (20-second answer /
  details / example / likely follow-ups) with a consolidated Sources
  section per guide, not per-question `**Source:**` lines.
- No individual claim-by-claim fact audit of the data-modeling guide's
  prose beyond the corrections above.
