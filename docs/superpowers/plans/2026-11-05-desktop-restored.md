# Desktop Restoration Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans for inline implementation.

**Goal:** Restore the user's compact five-page desktop dashboard while retaining useful readability and interaction fixes.

**Architecture:** Reuse the original page modules and replace the report-wide scrolling reflow with a small presentation-only desktop polish pass. No SQL or state-contract changes.

**Tech Stack:** Python, native FineVIS FVS, existing PostgreSQL datasets.

**Spec:** ../specs/2026-11-05-desktop-restored.md

## Global Constraints

English interface; Russian conversation. Five stories, 31 datasets, 11 retained parameters. Keep the Vintage six-by-six view. Restore 1920×1080 AUTO desktop canvas.

## Review Focus

- Six KPI cards remain on the same row.
- Charts remain side by side and dense records remain tabular.
- Wrapped explanations and Apply font configuration must survive rollback.
- All navigation, loan actions, and pagers retain their formulas.
- Historical and empty data must not leave stale values.

## Tasks

- [x] Replace the scrolling-layout assertion with a failing desktop/readability regression.
- [x] Replace reflow with focused desktop typography and wrapping fixes; build and install with backup.
- [x] Run native and PostgreSQL-backed checks; inspect all five pages and interactions in Preview.
- [x] Fresh source review, current guides/screenshots, validation receipt and portable archive.

## Ledger

- The user explicitly selected restoring the established desktop layout; no new design choice or approval is needed.

- Desktop output retains exactly the original 784 widget IDs. Dataset XML, parameters, computes, formula values and widget events are identical to the unpolished compact baseline.
- A fresh read-only reviewer found no actionable issue. All three native checks and the full 55-test PostgreSQL-backed suite passed.
- Runtime: default pages at1440x900 show no text overflow or page scrolling. Registry paging/drill/back, Vintage MOB7-12 and page3, combined historical filters, retained registry/schedule pages2 and historical Vintage clamping all passed.

- Empty Overview/Quality/Vintage cleared stale content. All five pages passed 1920x1080 text/bounds checks as well. All23 runtime checks passed; original default slice restored and viewport override reset. Current screenshots/docs and desktop archive replace the superseded scrolling presentation.
