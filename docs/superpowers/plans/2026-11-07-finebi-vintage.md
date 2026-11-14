# FineBI Vintage Analysis Implementation Plan

**Goal:** Extend the authorized FineBI migration with a fourth native shared tab.
**Architecture:** Three prepared direct-query datasets, six headline metrics, age-specific eligible-population notes/tooltips, chronological cohort matrix and observed cohort curves. Reuse existing shared controls, English labels and desktop theme.
**Spec:** docs/vintage-analysis.md and the existing FineBI migration plan.

- [x] Install Vintage KPIs, Vintage Matrix and Vintage Curves with English Text parameters through native UI; verify SQL previews.
- [x] Build original loans, original funded amount, origination cohorts and pooled ever-31+ MOB 3/6/12 KPI cards. Preserve age-specific eligible populations.
- [x] Build a native matrix covering all monthly cohorts and ages 1–12; retain immature/unavailable dashes and measured zero. Build up to four source-selected cohort curves with no future observations.
- [x] Place the fourth Tab in the current dashboard and extend all four shared controls to the three Vintage sources. Preserve existing tabs and the Quality-only registry threshold.
- [x] Validate default, historical and early immature slices; inspect oldest/newest cohort rows and all MOB ages, numeric age sorting, absent versus zero observations, and bidirectional navigation involving the new tab. Restore defaults, save screenshots, release editor and reset temporary viewport.

Native scrolling may replace FineReport's six-by-six pagination if all cohorts and ages stay legible and accessible. Do not convert immature cells to numeric zero, sum subgroup percentages or average pooled age rates. Use original contract-count denominators, including closed/written-off loans. No database fixture or FineReport changes.

## Verification record

- All three public SQL sources installed with four English Text parameters via native UI; previews 1 / 288 / 40 default rows.
- 89 numeric/English dataset-scenario checks passed. Additional default/historical/early controls checked full matrix shape, nulls and mature denominators.
- Six directed Vintage navigation edges retain August 2025 / Personal Loan / Moscow / Online; Quality-local 91+ DPD persists across Vintage round trip. Defaults restored including 1+ DPD.
- Native matrix shows chronological Year Month cohorts and exact numeric MOB groups 1–12; no interval bins. Full-width desktop matrix uses native scrolling. KPI eligible cohorts/loans are in age-specific English tooltips; visible methodology explains populations, source window and dash semantics.
- Earliest November 2024 slice has 295 loans, RUB 649.27 m, one cohort; rates and all twelve matrix cells are dashes; curves have no observations.
- Final review: independent fresh-context reviewer found no Critical/Important issues and reconciled 420 matrix cells plus 52 curve points. No deferred findings.
- Final saved view verified outside editor after native Back; editing lock released and temporary viewport override reset. Screenshot evidence: outputs/finebi-vintage under the FineBI workspace; build IDs and control values in finebi/vintage-build-state.json.
