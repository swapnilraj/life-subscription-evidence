# Data Gathering Plan

## What We Need to Prove

The essay isn't just vibes — we need hard numbers showing:

1. **The "subscription stack" is real and growing** — people pay more of their income to recurring extractions than ever before
2. **The framing hides the extraction** — language ("loan", "ownership", "access") obscures what's actually happening
3. **The comparison to fiction is quantifiable** — we can show the gap between fictional dystopia and mundane reality

---

## Dataset 1: UK Student Loans as Extraction

**Source:** Student Loans Company (SLC) annual reports, IFS
**Data needed:**
- Total outstanding student debt (UK)
- Average debt at graduation (Plan 2 vs Plan 5)
- Actual repayment rates (% who repay in full vs written off)
- Effective tax rate: 9% over threshold for 30-40 years
- Comparison: frame as "graduate tax" vs "loan" — what's the actual lifetime cost?
- Monthly deduction amounts at various salary levels

**Code:** Scrape/download SLC data, calculate lifetime extraction by salary band

## Dataset 2: Leasehold Ground Rent Extraction

**Source:** DLUHC, Land Registry, Leasehold Knowledge Partnership
**Data needed:**
- Number of leasehold properties in England & Wales
- Average ground rent and escalation clauses
- Freeholder concentration (how few companies own how many freeholds)
- Service charge inflation vs general inflation
- Marriage value / lease extension costs

**Code:** Analyze ground rent escalation patterns, model 25-year cost

## Dataset 3: Rent vs Own Wealth Gap

**Source:** ONS, Resolution Foundation, IFS
**Data needed:**
- Median renter vs owner wealth over time (UK)
- Rent-to-income ratio historical trend
- Home ownership rate by age cohort over decades
- "Dead money" calculation: lifetime rent paid vs mortgage equity built

**Code:** Visualize the divergence, calculate cumulative extraction

## Dataset 4: The Subscription Economy

**Source:** Zuora Subscription Economy Index, ONS household expenditure, bank data reports
**Data needed:**
- Average number of subscriptions per UK household (2015 vs 2020 vs 2025)
- Monthly subscription spend as % of income
- Categories: streaming, software, gym, insurance, utilities, phones
- What people "owned" 20 years ago vs rent/subscribe to now

**Code:** Build the "subscription stack" — visualize total monthly extraction

## Dataset 5: Historical Comparison

**Source:** ONS Family Expenditure Survey (historical), various
**Data needed:**
- Household expenditure breakdown: 1975 vs 1995 vs 2015 vs 2025
- Categories that shifted from "buy once" to "subscribe"
- Total % of income going to recurring payments

**Code:** Time series analysis, category mapping

---

## Visualizations We Want

1. **"The Subscription Stack"** — Stacked bar chart showing monthly extractions (rent/mortgage, student loan, council tax, streaming, insurance, phones, etc.)
2. **"The Divergence"** — Line chart: renter vs owner cumulative wealth over 30 years
3. **"What You Own vs What You Rent"** — 2005 vs 2025 comparison
4. **"The Graduate Tax"** — Lifetime repayment by salary band, showing most never clear the "loan"
5. **"Ground Rent Escalation"** — Exponential growth of doubling clauses over 99-year lease

---

## Tools

- Python (pandas, matplotlib, seaborn for analysis/viz)
- Public APIs where available (ONS, SLC)
- Web scraping where needed
- Jupyter notebooks for exploratory analysis
