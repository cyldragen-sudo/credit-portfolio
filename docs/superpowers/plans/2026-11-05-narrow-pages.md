# Narrow Pages Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task by task.

**Goal:** Make the four remaining native report pages readable in narrow desktop panes while preserving filters, navigation and evidence.

**Architecture:** Reflow existing native widgets after page construction, preserving IDs, dataset formulas, controller definitions and actions. Use native width fitting with scrolling. Keep data queries unchanged.

**Tech Stack:** Python, native FineVIS FVS, existing PostgreSQL data.

**Spec:** ../specs/2026-11-05-narrow-pages.md

## Global Constraints

- English product UI; Russian conversation.
- Five stories, 31 datasets, eleven state parameters, unchanged analytical scopes.
- All eight native rows per existing registry and detail table page remain reachable.
- Native WIDTH_FILL; 640 px minimum target.

## Review Focus

- Long currency values must fit narrow record cards.
- Empty selections must stay empty, including guarded loan drills.
- Navigation and pagers must keep the existing parameter bindings.
- Vintage matrix row indices must remain literal and its six-by-six coverage intact.
- Narrow view must scroll to every section without horizontal clipping.

### Task 1: Layout and regression checks

- [x] Add a failing native layout/record coverage test and observe its failure.
- [x] Implement focused native layout reflow, common controls and chart typography.
- [x] Build and pass native tests and the existing suite.

### Task 2: Runtime verification and delivery

- [x] Install with backup; inspect 640/722/1440 previews and save evidence.
- [x] Verify Apply, common navigation, loan drill/back, pagers and empty states.
- [x] Request one fresh read-only review, fix supported findings.
- [x] Update guides, screenshots, validation receipt and portable archive.

## Ledger

- Chosen vertical scrolling because AUTO scales the entire fixed canvas and cannot preserve readable typography for dense tables.
- Ruling: Reflow Vintage into the shared scrolling frame while retaining its matrix logic, rather than leaving a small panel at the top of a tall shared canvas. Canvas adaptation is report-wide.

- Native runtime found first-record labels covered by enlarged stripes; fixed background paint order and added a coverage regression guard.
- Native query button uses fontStyle rather than the ignored top-level fontSize; actual Apply text was rechecked.
- Native text supports pre-wrap/maxWidth in its style configuration; actual DOM inspection confirmed wrapped KPI explanations.
- Fresh source review found no actionable defects; 55 PostgreSQL-backed tests passed without skips.
- Final screenshot repetition encountered expired login; normal sign-in requested while preserving all earlier passing runtime evidence.

- Normal sign-in restored Preview. Final repetition passed all four pages at all three widths, including actual native text overflow checks. One Written Off header gained eight design pixels of height; its three-width recheck passed.
- Final Apply changed October to September (RUB 19.07 bn), navigation retained the date, and October/default filters were restored. All 34 runtime checks passed. Temporary viewport overrides were reset and the report was left open.
