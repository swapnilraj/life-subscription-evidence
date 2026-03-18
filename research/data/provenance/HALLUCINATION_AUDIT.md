# Hallucination Audit (Original `HEAD` Scripts)

**Purpose:** identify values/claims in the original scripts that were hardcoded, weakly sourced, or computationally incorrect.

**Method:** line-by-line review of original files from `git show HEAD:<file>` and classification against provenance rules:
- **Extracted**: machine-extracted from cached primary source artifact
- **Assumption**: explicit model assumption (allowed, but must be labeled)
- **Hallucination risk**: numeric claim presented as empirical without extractable primary-source backing
- **Bug**: computational logic error

---

## 1) `code/rent_vs_own.py` (original `HEAD`)

- `code/rent_vs_own.py@HEAD:32` `property_price_2024 = 290_000` with narrative citation in comment only, not source-extracted at runtime (**hallucination risk**).
- `code/rent_vs_own.py@HEAD:40` `monthly_rent_2024 = 1_258` not reproducibly pulled from a primary dataset (**hallucination risk**).
- `code/rent_vs_own.py@HEAD:41` `rent_inflation = 0.04` presented as baseline without explicit assumption labeling (**assumption not labeled**).
- `code/rent_vs_own.py@HEAD:44` `house_price_growth = 0.065` presented as conservative baseline without extraction path (**assumption not labeled**).
- `code/rent_vs_own.py@HEAD:165-172` annual cashflow difference sign handling inverted (renter cash adjusted in wrong direction) (**bug**).

**Current status:** baseline property/rent now extracted by code from ONS artifacts; non-extracted scenario terms are explicitly labeled assumptions.

---

## 2) `code/student_loans.py` (original `HEAD`)

- `code/student_loans.py@HEAD:23-58` thresholds and plan parameters defined in-code constants, not generated from source artifacts (**hallucination risk** for thresholds).
- `code/student_loans.py@HEAD:116` effective tax denominator used `starting_salary * years`, ignoring salary growth (**bug**, systematic distortion).
- `code/student_loans.py@HEAD:193-194` hidden-tax path used fixed growth constants inline, not shared config/provenance path (**traceability gap**).

**Current status:** plan thresholds are source-extracted from GOV.UK; effective tax now uses simulated lifetime income trajectory.

---

## 3) `code/leasehold.py` (original `HEAD`)

- `code/leasehold.py@HEAD:348` `initial_service_charge = 2_150` hardcoded without machine-verifiable source path (**hallucination risk**).
- `code/leasehold.py@HEAD:349` `lease_length = 99` embedded as default without explicit assumption metadata (**assumption not labeled**).
- `code/leasehold.py@HEAD:360,377,394,419` `initial_ground_rent=250` scenario base hardcoded without extraction path (**assumption not labeled**).
- `code/leasehold.py@HEAD:367-428` scenario outputs numerically precise but fed by unlabeled assumptions, making empirical interpretation unsafe (**hallucination risk** if reported as factual).

**Current status:** property baseline is source-extracted; service charge, lease term, and ground-rent scenarios are now explicitly labeled assumptions.

---

## 4) `code/historical.py` (original `HEAD`)

- `code/historical.py@HEAD:174-177` snapshot fields explicitly marked “Estimated” but consumed as model inputs without assumption provenance metadata (**assumption not labeled**).
- `code/historical.py@HEAD:259,321-326,419-501` multiple decade snapshots use fixed synthetic values (income, expenditure, debt ratios) with no extraction path (**hallucination risk**).
- `code/historical.py@HEAD:419-420` 2024 uses mixed values (`income=650`, `expenditure=623.30`) without source-driven generation of both fields (**traceability gap**).

**Current status:** 2024 key fields are source-extracted/computed from extracted metrics; non-extracted legacy snapshots are explicitly marked assumptions.

---

## 5) `code/subscriptions.py` (original `HEAD`)

- `code/subscriptions.py@HEAD:178,228` monthly incomes `{2005: 2083, 2015: 2250, 2025: 2450}` hardcoded (**hallucination risk**).
- `code/subscriptions.py@HEAD:205` subscription count trend `[0.5, 1.2, 1.8, 2.3, 2.8]` hardcoded and easy to misread as measured data (**hallucination risk**).
- `code/subscriptions.py@HEAD:106-113,141-143` branded expense lines hardcoded at precise prices without extraction path (**assumption not labeled**).
- `code/subscriptions.py@HEAD:282-289` narrative claim blocks use these fixed values as if externally measured (**hallucination risk** in downstream prose).

**Current status:** income baseline now derived by code from extracted ONS income metric; stack/category numbers remain explicit scenario assumptions.

---

## Summary Judgment

- Original scripts mixed empirical statistics, scenario assumptions, and some logic bugs without a strict provenance boundary.
- Main hallucination vector was **hardcoded numerics presented as factual baselines**.
- Current pipeline reduces this by enforcing:
  - extractable primary-source metrics for core baselines,
  - generated model input JSON with run metadata,
  - explicit assumption labeling where extraction is not available.
