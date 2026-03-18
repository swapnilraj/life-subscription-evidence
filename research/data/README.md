# UK Leasehold Research - Data & Analysis

**Created:** 2026-02-13  
**Topic:** UK Leasehold System as "Life Subscription" / Mundane Dystopia

## Provenance Note

- Source extraction, model-input provenance, and assumption register now live in
  `research/data/provenance/`.
- For current source/assumption status, see:
  - `research/data/provenance/README.md`
  - `research/data/provenance/ASSUMPTION_REGISTER.md`
  - `research/data/provenance/CLAIM_TRACEABILITY.md`
  - `research/data/provenance/HALLUCINATION_AUDIT.md`

---

## Files in This Directory

### 📊 `leasehold.md` (28 KB)
**Comprehensive research document** covering all aspects of the UK leasehold extraction system.

**Contents:**
1. Scale: 4.83M properties in England, 235K in Wales
2. Ground rent amounts and escalation clauses (flat, RPI, doubling)
3. Freeholder ownership concentration (30% investor-owned)
4. Service charge inflation (3× CPI)
5. Lease extension costs and the 80-year "marriage value" cliff
6. Leasehold Reform Act 2024 (what changed, what didn't)
7. Commonhold failure (20 schemes in 22 years)
8. Horror stories (Taylor Wimpey scandal, 20,000+ victims)
9. Ground rent doubling clauses making properties unmortgageable
10. Total annual extraction (~£3.8 billion/year estimated)

**Key findings:**
- **£600 million** in ground rent paid annually
- **£2,000-£2,300** average annual service charges
- Service charges inflate at **11% vs 3.8% CPI** (2023-24)
- **770,000-900,000** leaseholders pay £250+/year in ground rent
- Marriage value can add **20-50%** to lease extension costs below 80 years

**All data cited and sourced.**

---

### 💻 `../../code/leasehold.py` (20 KB)
**Python financial model** simulating leasehold costs over 99-year lease lifetime.

**Functions:**
- `calculate_ground_rent_flat()` - Fixed annual ground rent
- `calculate_ground_rent_rpi()` - RPI-linked escalation (3% default)
- `calculate_ground_rent_doubling()` - Doubling clauses (10/15/25 year periods)
- `calculate_service_charges()` - Service charge inflation (5% default)
- `calculate_lease_extension_premium()` - Statutory formula with marriage value
- `model_leasehold_lifecycle()` - Complete lifecycle cost calculation
- `compare_leasehold_vs_freehold()` - Extraction vs freehold equivalent

**To run:**
```bash
cd /home/node/.openclaw/workspace/life-subscription
python3 code/leasehold.py
```

**Output includes:**
- 4 scenarios (flat, RPI, doubling 10yr, doubling 25yr)
- Lease extension cost curve (99 to 40 years remaining)
- Marriage value impact analysis (80-year threshold)
- Total lifetime extraction calculations
- Comparison vs freehold equivalent

---

### 📈 `leasehold_model_output.json` (2 KB)
**Machine-readable output** from the Python model.

**Structure:**
```json
{
  "property_value": 280000,
  "lease_length": 99,
  "scenarios": [
    {
      "name": "Flat £250",
      "ground_rent_total": 6000,
      "service_charges_total": 5342290,
      "lease_extension_cost": 8476,
      "total_cost": 5356766,
      "extraction_amount": 5208266,
      "extraction_percentage": 1215.5
    },
    ...
  ],
  "extension_curve": [ ... ]
}
```

Use for further analysis, visualization, or integration with other data.

---

## Key Model Results

**For a £280,000 property with 99-year lease:**

| Scenario | Total Cost | vs Freehold | Extraction % |
|----------|-----------|-------------|--------------|
| Flat £250/year | £5.36M | +£5.21M | 1,215% |
| RPI-linked £250 | £5.36M | +£5.22M | 1,217% |
| Doubling 10yr | £5.38M | +£5.23M | 1,220% |
| Doubling 25yr | £5.36M | +£5.21M | 1,215% |

**Key insight:** Even with "modest" 5% annual service charge inflation, you pay **19× the purchase price** in fees over 99 years.

---

## The "Life Subscription" Framing

### What This Data Reveals

1. **Perpetual payments** for property you nominally "own"
2. **Compounding extraction** (5% inflation → £5.3M over 99 years)
3. **Multiple extractors** (freeholders, management companies, surveyors)
4. **Structural traps** (80-year cliff, doubling clauses, unmortgageability)
5. **Failed alternatives** (commonhold: 20 schemes in 22 years)
6. **Delayed reforms** (2024 Act takes effect 2028, doesn't fix existing problems)

### The Mundane Dystopia Element

- **Appears normal** until you model it over lifetime
- **Legalized extraction** baked into property law
- **Complexity as obscurantism** (marriage value, relativity curves, yield rates)
- **Trapped equity** (can't sell, can't escape escalating costs)
- **Professional capture** (solicitors, surveyors, managing agents all profit)
- **Feudal persistence** in modern economy

---

## Sources Summary

**Official:**
- UK Government Statistics (DLUHC, Land Registry, ONS)
- Law Commission reports (2020 leasehold reform recommendations)
- Leasehold and Freehold Reform Act 2024

**Advocacy:**
- Leasehold Knowledge Partnership (LKP)
- Home Owners Alliance (HOA)
- National Leasehold Campaign

**Legal/Professional:**
- RICS (Royal Institution of Chartered Surveyors)
- Multiple solicitor firms' guides

**Media:**
- CMA enforcement actions (Taylor Wimpey, etc.)
- Guardian, BBC, Sky News investigations
- Parliamentary committee reports

**All sources cited in leasehold.md.**

---

## Usage for Essay

This data supports arguments about:

1. **Financialization of everyday life** (housing as extraction platform)
2. **Subscription models replacing ownership** (perpetual payments)
3. **Legal complexity as control mechanism** (obfuscating extraction)
4. **Regulatory capture** (commonhold failure, delayed reforms)
5. **Compound exploitation** (multiple fees, all escalating)
6. **Temporal violence** (80-year cliff, decades to reform)
7. **Class extraction** (disproportionately affects first-time buyers, flat dwellers)

### Narrative Hooks

- "You pay 19× the purchase price over 99 years"
- "£600 million in ground rent annually for... nothing"
- "Marriage value: you pay 50% of increasing your own property's value"
- "Commonhold: 20 schemes in 22 years — designed to fail"
- "Doubling clauses: £250 → £128,000 over 90 years"
- "Service charge inflation: 3× general CPI"
- "Properties made unmortgageable by small print"

### The "Subscription" Angle

Like SaaS, streaming services, phone contracts:
- **Perpetual payments** (ground rent, service charges)
- **Price escalation** (doubling, RPI, "inflation")
- **Lock-in** (trapped equity, extension costs)
- **Bundled fees** (management, insurance commissions, "event fees")
- **Complexity** (obscures total cost)
- **Failed alternatives** (commonhold = open-source software that "never took off")

Unlike subscriptions:
- **You paid £280,000 upfront**
- **It's your home** (emotional, not just financial)
- **Can't cancel** (without losing massive equity)
- **Escalation you can't control** (service charges, no cap)

---

## Potential Extensions

**Further research could explore:**
1. Service charge breakdowns (what % is profit vs actual cost?)
2. Management company ownership (who owns the managing agents?)
3. Insurance commission structures (kickbacks to managing agents)
4. Freeholder financial returns (IRR on ground rent portfolios)
5. Comparison to other countries (Scotland banned leasehold in 1970s)
6. Impact of 2024 reforms (will £250 cap actually work?)
7. Commonhold adoption barriers (why developers still resist)

**Data sources to add:**
- First-tier Tribunal decisions (service charge disputes)
- Mortgage lender policies (what makes property unmortgageable?)
- Actual lease documents (show escalation clauses in practice)
- Property price discount data (leasehold vs freehold equivalent)

---

**Compiled by:** OpenClaw Research Subagent  
**For:** "Life Subscription" / Mundane Dystopia Essay  
**Cite as:** UK Leasehold Research Data (2026)
