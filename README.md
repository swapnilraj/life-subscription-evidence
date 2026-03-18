# Life Subscription Evidence Repo

This repository contains the public research and reproducibility layer for the Life Subscription project: source artifacts, model inputs, scripts, generated outputs, and integrity tests.

It is intentionally scoped to evidence and methodology. Draft article writing is kept outside this repository.

## What This Repo Includes

- UK-focused research modules:
  - housing tenure and rent-vs-own divergence
  - student loans lifetime repayment dynamics
  - leasehold costs and extension dynamics
  - historical household expenditure context
  - subscription/ownership shift synthesis
- Comparative context modules:
  - western extraction benchmarks
  - macro "building vs extracting" indicators
- Provenance system:
  - pinned source registry
  - cached source artifacts
  - extracted metric store
  - model-input generation with source traceability
- Reproducibility scripts and test suite.

## Repository Layout

```text
code/
  *.py                          # Data extraction, modeling, provenance builders, audits

research/
  data/
    *.md                        # Research writeups and summaries
    *.json / *.csv              # Generated model outputs
    charts/                     # Derived charts used in publication
    provenance/                 # Source registry, lockfiles, extracted metrics, manifests
      model_inputs/             # Script inputs generated from extracted metrics
      raw/                      # Cached source artifacts

  references/                   # Bibliography and theory notes
  notes/                        # Working research notes

tests/
  test_*.py                     # Integrity and provenance tests
```

## Research Methodology

### 1) Source and artifact control

- Canonical source list: `research/data/provenance/primary_sources.json`
- Artifact integrity lock: `research/data/provenance/source_artifacts.lock.json`
- Raw cached artifacts: `research/data/provenance/raw/`

Each source can be tied to a publisher, URL, tier, and expected hash.

### 2) Deterministic extraction

- Extraction and input builder: `code/build_provenance_inputs.py`
- Output:
  - `research/data/provenance/extracted_metrics.json`
  - `research/data/provenance/model_inputs/*.json`

The builder normalizes extracted values and embeds provenance metadata used by downstream models.

### 3) Modeling and output generation

Core scripts:
- `code/rent_vs_own.py`
- `code/student_loans.py`
- `code/leasehold.py`
- `code/historical.py`
- `code/subscriptions.py`

Outputs are written under `research/data/` as `.json` and `.csv`.

### 4) Traceability and policy checks

- Claim traceability builder: `code/build_claim_traceability.py`
- Markdown source-domain policy audit: `code/audit_markdown_sources.py`
- Comparative metrics builder: `code/build_comparative_primary_metrics.py`

### 5) Integrity tests

- `tests/test_provenance_invariants.py`
- `tests/test_provenance_builder.py`
- `tests/test_claim_traceability.py`
- `tests/test_markdown_source_audit.py`

CI workflow:
- `.github/workflows/provenance-integrity.yml`

## How To Run

From repository root:

```bash
# 1) Regenerate extracted metrics and model inputs
python3 code/build_provenance_inputs.py

# 2) Run model scripts
python3 code/rent_vs_own.py
python3 code/student_loans.py
python3 code/leasehold.py
python3 code/historical.py
python3 code/subscriptions.py

# 3) Rebuild traceability artifacts
python3 code/build_claim_traceability.py

# 4) Audit comparative markdown source policy
python3 code/audit_markdown_sources.py --check

# 5) Run tests
python3 -m pytest tests
```

## Output Conventions

- Observed statistics and model outputs are kept separate.
- Generated files are written to `research/data/`.
- Scenario outputs are labeled as model outputs and should not be interpreted as forecasts.

## Reproducibility and Claim Discipline

The project follows three claim classes:
- Observed: directly reported in official or primary sources
- Estimated: derived from reported values with explicit calculation
- Modeled: scenario outputs from script assumptions

When citing outputs publicly, include both:
- source citations for observed inputs, and
- model notes for scenario outputs.

## Notes

- This repository may contain large cached source artifacts under `research/data/provenance/raw/`.
- If a source page changes upstream, rerun builders and tests to surface drift.
- Canonical bibliography lives at `research/references/BIBLIOGRAPHY.md`.
