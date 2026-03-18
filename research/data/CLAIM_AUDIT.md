# Claim Audit (Summary Docs)
**Scope:** Executive/summary-facing documents in `research/data/`.
**Goal:** Every headline statistic is (a) linked to an official/primary source, or (b) explicitly labeled as a model assumption/output.
**Last updated:** 2026-02-13

## 1. Rent vs Ownership (Housing)
**Files audited:**
- `research/data/EXECUTIVE_SUMMARY.md`
- `research/data/QUICK_STATS.md`

**Status:** Updated and made citable.

**Key changes applied**
- Replaced uncited “homeowners vs renters” wealth medians with ONS tenure-specific medians (owned outright / mortgage / rented).
- Updated all simulation outputs after fixing the model cashflow sign and aligning baseline rent to an ONS bulletin.
- Removed/avoided London-specific deposit/rent figures that were not supported by a primary source in-repo.

**Primary sources used**
- ONS total wealth bulletin (tenure medians): see `research/data/EXECUTIVE_SUMMARY.md` footnotes.
- ONS young-adult homeownership shift (1996→2015): see `research/data/EXECUTIVE_SUMMARY.md` footnotes.
- English Housing Survey (rent vs mortgage income burden): see `research/data/EXECUTIVE_SUMMARY.md` footnotes.
- ONS private rent level baseline (GB, March 2024): see `research/data/EXECUTIVE_SUMMARY.md` footnotes.
- LHA 30th percentile mechanism (VOA/GOV.UK): see `research/data/EXECUTIVE_SUMMARY.md` footnotes.
- Halifax 2024 FTB age/deposit: see `research/data/EXECUTIVE_SUMMARY.md` footnotes.

**Model outputs**
- Produced by `code/rent_vs_own.py`, saved as `research/data/rent_vs_own_summary.json` and `research/data/rent_vs_own_simulation.csv`.
- Assumptions are defined in `code/rent_vs_own.py`.

## 2. Subscription Economy (Access vs Ownership)
**Files audited:**
- `research/data/RESEARCH_SUMMARY.md`
- `research/data/subscription-economy.md`
- `code/subscriptions.py`

**Current risk level:** Medium.

**Why**
- `research/data/RESEARCH_SUMMARY.md` contains many market-size and behavioral claims that are plausible but not currently traceable to specific, auditable sources (author/date/report title + URL + page/table).
- `research/data/subscription-economy.md` names many sources but frequently lists them without URLs, which prevents verification.

**Claim-by-claim notes for `research/data/RESEARCH_SUMMARY.md`**
- “2005: 0.5 subscriptions per household; 2025: 2.8 (460% increase)”:
  - Status: Needs source upgrade.
  - Action: Either cite a specific survey/report with methodology + URL, or reframe as an estimate from the project’s stack model and label it as such.
- “86% of UK residents now use subscription services”:
  - Status: Needs primary survey citation (or remove).
- “Average UK household: £58-65.50/month on discretionary subscriptions; Gen Z £305/month; top 10% £200+/month”:
  - Status: Needs specific survey/report citations with URLs and field definitions (what counts as ‘subscription’?).
- “Global subscription economy: $565-722bn (2025), 15.7% CAGR, $2.1T by 2034”:
  - Status: Likely market research estimates; acceptable only if cited to named report(s) with URLs and the range explained.
- “Cars: 80-90% financed; PCP dominates”:
  - Status: Should be cited to an official/trade-body series (e.g., FLA, FCA motor finance research) with URLs.
- “Stack impact: 2005 £1,282/mo (61.5% income) vs 2025 £1,977/mo (80.7% income)”:
  - Status: Model output, not official statistic.
  - Action: Keep but label explicitly as model output from `code/subscriptions.py` and/or `research/data/subscription-economy.md` methodology section.

**Recommended remediation**
- Add URLs (and publication dates) for each named source in `research/data/subscription-economy.md` “Key Citations & Sources”.
- Convert `research/data/RESEARCH_SUMMARY.md` headline numeric bullets into footnoted claims:
  - Prefer Ofcom/ONS/FLA/FCA where possible.
  - Where only market research exists, label as “estimate” and cite the exact report.

## 3. Student Loans (Lifetime Repayment / Graduate Tax)
**Files audited:**
- `research/data/student-loans.md`
- `research/data/RESEARCH_COMPLETE.md`
- `code/student_loans.py`

**Current risk level:** Medium (improvable).

**Why**
- `research/data/student-loans.md` includes a mix of authoritative sources (SLC, GOV.UK, IFS, OBR) and weaker/derivative sources (calculator sites, generic media).
- Summary docs claim strong percentage statements (“only X% repay in full”, “94% decline in full repayments”) that should be tied to specific SLC statistical releases or DfE forecasts, not secondary reporting.

**Concrete improvements already in place**
- `code/student_loans.py` now computes effective tax rate using simulated lifetime income rather than `starting_salary * years`, and writes outputs to the repo’s `research/data/` directory.

**Recommended remediation**
- In `research/data/student-loans.md`:
  - Keep GOV.UK/SLC/OBR/IFS/EES as primary citations.
  - Move calculator sites and general-media links into a “popular summaries” subsection, or delete if not necessary.
  - For “% repaying in full” claims, cite DfE/EES forecast tables directly.

## 4. Leasehold (Ground Rent / Service Charges / Reform)
**Files audited:**
- `research/data/README.md`
- `research/data/leasehold.md`
- `code/leasehold.py`

**Current risk level:** Medium.

**Why**
- `research/data/leasehold.md` includes a valuable citations section with many GOV.UK/Law Commission links, but also includes low-credibility sources (and some legal-marketing pages) mixed into the same numbered list.

**Recommended remediation**
- Split `research/data/leasehold.md` sources into tiers:
  - Tier A: GOV.UK, Law Commission, ONS, CMA.
  - Tier B: RICS, reputable legal explainers (used only for interpretation, not headline numbers).
  - Tier C: advocacy/media (used for case studies, not core quantification).
- Ensure every headline number in `research/data/README.md` maps to a Tier A source or is labeled as model output.

## 5. Historical Expenditure (1975–2025)
**Files audited:**
- `research/data/historical-comparison.md`
- `code/historical.py`
- `research/data/SUBAGENT_REPORT.md`

**Current risk level:** High.

**Why**
- The report itself flags that the category mapping can produce counterintuitive results depending on how “essential recurring” is handled; this needs methodological tightening before using the extracted percentage deltas as headline claims.

**Recommended remediation**
- Treat historical extraction trend numbers as provisional until:
  - category mapping rules are specified, and
  - the specific ONS/FES tables and the inflation-adjustment methodology are documented.
