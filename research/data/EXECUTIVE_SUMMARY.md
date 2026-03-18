# Executive Summary: UK Rent vs Ownership Wealth Divergence

**Research completed:** 2026-02-13  
**For:** Essay on "Life Subscription" / Mundane Dystopia

---

## The Numbers That Tell the Story

### Tenure Wealth Gap (Observed)

ONS data on household total wealth (Great Britain, April 2020 to March 2022) shows large median wealth differences by tenure:
- **Owned outright:** £647,400
- **Buying with a mortgage:** £404,700
- **Rented:** £40,800[^ons_total_wealth]

### 30-Year Divergence (Illustrative Simulation)

**Two 25-year-olds in 2024 with the same starting cash (£58,000), consuming equivalent housing but via different tenure pathways.** This is a deterministic model (not a forecast); results depend on assumptions.[^model]

| Metric | Buyer | Renter | Gap |
|--------|-------|--------|-----|
| **At Age 55 (2054)** | | | |
| Net Worth | £1,918,166 | £102,650 | £1,815,516 |
| Total Paid | £828,841 | £845,782 | Renter pays ~£16.9k MORE |
| Monthly Housing Cost (final) | £0 (owns outright) | £3,886/month | Still paying |
| Wealth Built | £1.9M equity | £103k savings | **18.7:1 ratio** |

**Interpretation:** Even under conservative assumptions, the renter pays similarly large totals over decades while ending with far less accumulated wealth, and with ongoing monthly rent at age 55.[^model]

---

## Grounded Supporting Data Points (Citable)

### 1. Young Adult Homeownership Decline (Long-Run)
ONS reporting using survey data shows homeownership fell sharply for young adults between 1996 and 2015:
- **Age 25-29:** 55% (1996) → 30% (2015)
- **Age 30-34:** 68% (1996) → 46% (2015)[^ons_young_adults]

### 2. First-Time Buyers: Age and Deposit (2024)
Halifax reports for 2024:
- Average first-time buyer age: **33**
- Average deposit: **£61,090** (about **20%** of typical first-home price)[^halifax_ftb]

### 3. Housing Cost Burden (Rent vs Mortgage)
English Housing Survey reporting shows (England, 2023-24):
- Private renters spent **34%** of household income on rent on average
- Mortgage holders spent **19%** of household income on mortgage payments on average[^ehs_housing_crisis]

### 4. Private Rent Level Baseline (2024)
ONS reports the average private rent in **Great Britain was £1,246** in March 2024 (and rising).[^ons_rent_level]

### 5. Local Housing Allowance (Mechanism)
LHA rates are determined using a local “list of rents” at the **30th percentile** of market rents.[^lha_30th]

## The Life Subscription Formula

```
Renter's Fate = (High rent × No equity) × Perpetuity
             = Permanent wealth extraction
             = Inability to save deposit
             = Locked into renting forever
             = "Life subscription" to housing
```

## Files Generated

1. **rent-wealth-gap.md** — Full research report with all citations (18,525 bytes)
2. **rent_vs_own.py** — Python simulation model (15,050 bytes)  
3. **rent_vs_own_simulation.csv** — Year-by-year data (31 rows, 17 columns)
4. **rent_vs_own_summary.json** — Summary statistics
5. **EXECUTIVE_SUMMARY.md** — This file

**All data fully cited to:**
- ONS (Wealth and Assets Survey, housing statistics)
- IFS (inequality, housing costs)  
- Resolution Foundation (intergenerational wealth, living standards)
- Halifax, Zoopla, Nationwide (market data)
- Gov.uk (English Housing Survey, LHA rates)
- Trading Economics, Statista (time series)

---

## The Bottom Line

**The UK housing system has bifurcated society into two permanent classes:**

1. **Asset owners** — accumulate wealth passively through property appreciation
2. **Renters** — pay perpetually, build nothing, locked out structurally

**This is not a temporary affordability crisis. It is a designed system of wealth extraction that:**
- Transfers ~£846k in rent payments over 30 years (illustrative model output)[^model]
- Creates a ~£1.82m net worth gap between otherwise-equivalent renter and buyer (illustrative model output)[^model]
- Uses a benefits benchmark (LHA) based on the 30th percentile of local rents, meaning 70% of rents are above that benchmark by definition[^lha_30th]

**The "life subscription" is real. The dystopia is mundane. The mechanism is measurable.**

---

*This is your quantitative foundation. Use it to make readers viscerally understand the numbers behind the everyday horror.*

[^ons_total_wealth]: ONS, “Household total wealth in Great Britain: April 2020 to March 2022” (24 Jan 2025). https://www.ons.gov.uk/peoplepopulationandcommunity/personalandhouseholdfinances/incomeandwealth/bulletins/totalwealthingreatbritain/april2020tomarch2022 (accessed 2026-02-13).
[^ons_young_adults]: ONS, “Why are more young people living with their parents?” (22 Feb 2016). https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/families/articles/whyaremoreyoungpeoplelivingwiththeirparents/2016-02-22 (accessed 2026-02-13).
[^halifax_ftb]: Halifax (Lloyds Banking Group), “First-time buyer market rebounds as a fifth more stepped on the ladder last year” (14 Feb 2025; reporting 2024 outcomes). https://www.lloydsbankinggroup.com/media/press-releases/2025/halifax-2025/first-time-buyer-market-rebounds.html (accessed 2026-02-13).
[^ehs_housing_crisis]: DLUHC, “English Housing Survey 2023 to 2024: experiences of the 'housing crisis'.” https://www.gov.uk/government/statistics/english-housing-survey-2023-to-2024-experiences-of-the-housing-crisis/english-housing-survey-2023-to-2024-experiences-of-the-housing-crisis (accessed 2026-02-13).
[^ons_rent_level]: ONS, “Private rent and house prices, UK: April 2024.” https://www.ons.gov.uk/economy/inflationandpriceindices/bulletins/privaterentandhousepricesuk/april2024 (accessed 2026-02-13).
[^lha_30th]: UK Government / VOA, “Local Housing Allowance: List of rents” (LHA based on 30th percentile). https://www.gov.uk/government/collections/local-housing-allowance-list-of-rents (accessed 2026-02-13).
[^model]: Deterministic model outputs generated by `code/rent_vs_own.py` and saved to `research/data/rent_vs_own_summary.json` and `research/data/rent_vs_own_simulation.csv`. Assumptions are defined in `code/rent_vs_own.py`.
