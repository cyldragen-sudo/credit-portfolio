# Synthetic generation and reproducibility

Version 1.0.0 uses Python's seeded `random.Random` and no external data or model services. The delivered seed is **20261104**. The fixture SHA-256 and row counts are in `data/generated/manifest.json`. Gzip headers omit filenames and timestamps; the same code, seed and loan count produce byte-identical fixtures on the validated Python runtime.

## Population and time

- 12,000 funded contracts; 7,200 additional declined, withdrawn, pending or approved-unfunded applications.
- 15,000 generated customers; each can appear in multiple applications or contracts.
- Originations are distributed across 36 months from November 2023 to October 2026, with a rising origination weight and December seasonality.
- Daily reporting states start October 31, 2024. The normal reporting window is November 1, 2024 through October 31, 2026.
- Contractual schedules may extend beyond the fixture cutoff. Future obligations are contractual knowledge, not future observed payments or loan outcomes.
- No observed application event, loan operation, snapshot, closure or monthly-age observation occurs after October 31, 2026.

Products have different generated principal ranges, contractual rates and terms. These parameters create variety for demonstration and are not claims about market pricing. Customer residence, origination branch and channels are simulated independently. Product/branch plans are generated from the simulated monthly actuals multiplied by a seeded 0.85–1.20 factor, with a minimum target. They illustrate plan comparisons; they are not ex-ante forecasts or independent performance benchmarks.

## Ledger conventions

Installments use a fixed monthly annuity, with monthly interest equal to outstanding principal × annual percentage rate / 1200, rounded half-up to kopecks. The final installment pays the remaining principal. This monthly convention is a simplification; no actual/365 day-count, business-day adjustment, penalty or daily interest accrual is modeled.

For a payment, process the oldest due installment first, interest then principal, and continue to later due installments. A partial payment leaves the oldest unpaid obligation aging. Early settlement pays due interest plus all remaining principal; future interest is cancelled, not received. Write-off extinguishes all remaining principal and due interest through a separate non-cash operation and allocations.

Write-offs and early settlement retain their contractual schedule for auditability. Future canceled schedule rows are labeled with the observed closure date. No reversals, refinancing, variable rates, revolving limits or restructuring events are generated in this release.

## Assigned scenarios

| Scenario | Loans | Generated behavior |
|---|---:|---|
| ON_TIME | 6,830 | Payments on contractual due dates |
| SHORT_DELAY | 1,461 | Regular payments delayed by 5–20 days |
| CURE | 1,239 | Three installments delayed by 75 days, with catch-up later |
| EARLY_SETTLEMENT | 1,443 | Full settlement at a selected 6th–18th monthly anniversary |
| PERSISTENT_ARREARS | 654 | Payments stop after an initial 2–7 performing installments |
| WRITE_OFF | 373 | Persistent arrears followed by write-off 210 days after the first missed due date |

Scenario assignment is a generator input, not the present status. A recently issued WRITE_OFF scenario may still be performing at the fixture cutoff; future intended behavior is not injected into observed ledger data. Use the scenario table only for demo provenance and inspection, not historical prediction features.

Persistent-arrears assignment probability depends on the synthetic risk group and increases for **Partner** originations from **July 1, 2025** onward. Compare cohorts at a common completed age to demonstrate the effect; do not compare recent cohorts' raw lifetime arrears to older loans.

## Rebuild

Run from the project root:

```bash
python3 src/generate.py --loans 12000 --seed 20261104 --output /absolute/path/to/new-empty-directory
```

The output contains a compressed SQL COPY fixture and a manifest. The generator refuses a nonempty directory. Use a fresh directory rather than deleting or overwriting delivered data. For a smaller demo, change `--loans`; plans and population size scale accordingly. Full-project `verify.py` checks the delivered manifest, so update its manifest path if validating an alternate output.

## Demonstration walkthrough

1. Open Portfolio Overview on October 31, 2026; compare size and quality by product.
2. In Sales and Funnel, distinguish funded-date volumes from submission-cohort conversions.
3. In Vintage Analysis, select Partner and compare mature MOB 6 observations across origination months.
4. Open Delinquency, select a 31+ or 91+ minimum DPD and inspect the monthly transition table.
5. Pass a selected loan ID to Loan Details; reconcile its schedule, operations, balance and DPD history.

`validation/database-checks.json` records example loan IDs for each assigned scenario and the measured six-month channel comparison. Those values are generated demo results, not evidence of actual banking performance.
