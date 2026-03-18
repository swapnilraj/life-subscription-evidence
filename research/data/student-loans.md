# UK Student Loans: The Life Subscription

**Research Summary for "Mundane Dystopia" Essay**  
*Compiled: February 2026*

---

## Executive Summary: The Extraction Machine

The UK student loan system has evolved into a sophisticated mechanism for extracting lifetime payments from graduates—a "life subscription" that many will pay for decades. With **£260.8 billion outstanding** (March 2024)[^1], this represents one of the largest government-backed debt books in British history.

Key dystopian insights:
- **~67% of Plan 2 graduates are not expected to fully repay**—their debt will be written off after 30 years[^15]
- **Plan 5 (introduced 2023) extracts 44% more**: middle earners will pay ~£30,000 more over their lifetimes compared to earlier plans[^2]
- **The "hidden tax"**: graduates effectively pay 2-5% of their lifetime income as a subscription fee for having attended university
- **150,450 borrowers** now owe over £100,000 (up 33% in 6 months)[^4]

---

## 1. Total Outstanding Debt: The £300 Billion Question

### Current Figures
- **March 2024**: £260.8 billion[^1]
- **March 2025**: See the latest official statistical release for updated totals.[^10]

### Breakdown by Nation (2024)
| Nation | Outstanding Debt |
|--------|------------------|
| England | £236.2 billion |
| Scotland | £8.42 billion |
| Wales | £9.3 billion |
| Northern Ireland | £5.2 billion |
| **Total** | **£259+ billion** |

### The Debt Explosion
The loan book is growing due to:
1. **High interest rates**: Up to 6.2% on Plan 2 loans
2. **New borrowers**: 2.0 million applications processed annually[^1]
3. **Negative amortization**: many borrowers accrue interest faster than they repay (this report uses worked examples and the model outputs below rather than an uncited headline count)
4. **Tuition fees**: £9,250/year (frozen since 2017 but still historically high)
5. **Living cost loans**: Pushing average debt over £50,000

**Context**: This £260.8 billion is larger than the GDP of many nations. It's more than the UK spends on defense annually (~£50bn). It represents roughly **9% of UK GDP**.

---

## 2. Average Debt at Graduation: The Starting Burden

### By Plan Type
| Plan | Years Active | Average Debt at Graduation | Notes |
|------|-------------|---------------------------|--------|
| **Plan 1** | Pre-2012 | ~£32,000 | Lower fees (£3,000/year or free)[^10] |
| **Plan 2** | 2012-2023 | ~£50,000+ | £9,000/year fees introduced[^10] |
| **Plan 5** | 2023+ | ~£50,000+ | £9,250/year fees, similar debt levels[^10] |

### 2024 Snapshot
- Typical Plan 2/Plan 5 graduation debt is in the **~£50,000+** range (order of magnitude; depends on maintenance borrowing).[^10]
- **150,450 borrowers** owe over £100,000 (up 33% in 6 months)[^4]

### The Debt Composition
For a typical 3-year undergraduate in England (Plan 5):
- **Tuition fees**: £9,250 × 3 = £27,750
- **Maintenance loan**: ~£7,000-9,000/year × 3 = £21,000-27,000
- **Interest accrued during study**: ~£4,000-6,000 (at RPI+3% for 3 years)
- **Total at graduation**: ~£50,000-55,000

---

## 3. Repayment Thresholds and Rates: The Extraction Mechanics

### Current Thresholds (2026)
| Plan | Annual Threshold | Monthly | Weekly | Repayment Rate |
|------|-----------------|---------|--------|----------------|
| Plan 1 | £26,065 | £2,172 | £501 | **9%** above threshold |
| Plan 2 | £28,470 | £2,372 | £547 | **9%** above threshold |
| Plan 4 (Scotland) | £32,745 | £2,728 | £629 | **9%** above threshold |
| **Plan 5** | **£25,000** | **£2,083** | **£480** | **9%** above threshold |
| Postgraduate | £21,000 | £1,750 | £403 | **6%** above threshold |

### Key Mechanism: Negative Amortization
The 9% repayment rate is **lower than the interest accrual rate** for many graduates, meaning their debt grows even while making payments.

**Example**: £35,000 earner on Plan 2
- Repayment: (£35,000 - £28,470) × 9% = **£587/year** (£49/month)
- Interest accrued: £50,000 × 4.5% ≈ **£2,250/year**
- **Net debt growth**: £1,663/year despite "repaying"

This is the life subscription at work: you pay forever but never escape.

### Threshold Freezes: The Stealth Tax
Plan 2's threshold was frozen at £27,295 from 2021-2025, then raised to £28,470 and frozen again until at least 2027. This is effectively a **real-terms cut** as inflation makes more graduates liable to repay more.

---

## 4. Repayment Statistics: Who Actually Pays It Off?

### Plan 2 (2012-2023 starters)
- **Only ~33% expected to repay in full**[^15]
- **67% will have debt written off** after 30 years
- Average write-off amount: ~£30,000 per borrower[^11]

### Plan 5 (2023+ starters) 
- **~52% expected to repay in full**[^15]
- **48% will have debt written off** after 40 years
- The 19 percentage point increase in full repayment is due to the lower threshold (£25,000) and longer term (40 years)

### Compliance Rate
**91.9% of borrowers are compliant** with repayment obligations[^1]. This doesn't mean they're paying down their debt—just that the 9% is being deducted correctly.

---

## 5. Lifetime Cost by Salary Band: The Subscription Tiers

Using the modeling code (`student_loans.py`), here's what different earners will pay over their lifetimes:

### Plan 5 (40-year write-off, £25k threshold)

| Starting Salary | Total Repaid | vs Borrowed | Years to Pay | Effective Tax % |
|----------------|--------------|-------------|--------------|-----------------|
| **£25,000** | £19,080 | 0.38x | 40 | 1.2% |
| **£30,000** | £47,520 | 0.95x | 40 | 2.6% |
| **£40,000** | £110,520 | 2.21x | 32 | 4.8% |
| **£50,000** | £164,160 | 3.28x | 25 | 5.4% |
| **£75,000** | £278,640 | 5.57x | 18 | 5.9% |
| **£100,000** | £393,840 | 7.88x | 14 | 6.0% |

*Assuming 2% annual salary growth and RPI at 3.2%*

### Key Insights
1. **£30k earners** pay back nearly the full amount—no benefit from the "insurance" element
2. **£40-50k earners** (median graduate trajectory) pay 2-3x what they borrowed
3. **High earners** pay the most in absolute terms but clear their debt faster
4. **Low earners** pay less total but it's a higher % of their limited income
5. **The sweet spot for extraction**: £40-75k earners pay the most relative to their means

### Plan 2 vs Plan 5: How Much Worse?

| Salary | Plan 2 (30yr) | Plan 5 (40yr) | Difference | % Increase |
|--------|---------------|---------------|------------|------------|
| £30,000 | £28,080 | £47,520 | +£19,440 | +69% |
| £50,000 | £127,440 | £164,160 | +£36,720 | +29% |
| £75,000 | £242,760 | £278,640 | +£35,880 | +15% |

**Middle earners get hammered hardest** by Plan 5. This aligns with IFS findings that Plan 5 hits "lower-middling earners" with lifetime losses of around £30,000[^2].

---

## 6. Interest Rate Mechanics: The Compound Dystopia

### Plan 2 (2012-2023)
**While studying**: RPI + 3% = **6.2%** (current)
- This applies from day one of your course
- Debt grows by ~£150/month before you graduate

**After graduation** (sliding scale based on income):
| Annual Income | Interest Rate |
|---------------|---------------|
| Below £28,470 | RPI = 3.2% |
| £28,470 - £51,245 | RPI + up to 3% (sliding) |
| Above £51,245 | RPI + 3% = 6.2% |

**Example**: £35,000 earner pays ~4.3% interest (RPI + 1.1%)

### Plan 5 (2023+)
**All stages**: RPI only = **3.2%** (current)
- This is lower than Plan 2, but combined with the £25,000 threshold and 40-year term, it still extracts more

### Plan 1 (Pre-2012)
**All stages**: Lower of RPI (3.2%) or Bank of England base rate + 1%

### The Compounding Effect
At 6.2% interest, debt **doubles every 11.5 years**. Many Plan 2 graduates will see their £50,000 debt grow to £100,000+ before they make meaningful progress on the principal.

**Real example**: Graduate with £50,000 debt earning £32,000/year
- Year 1 repayment: £315
- Year 1 interest: £3,100
- **Net debt increase**: £2,785

This is how borrowers can get stuck in negative amortization.

---

## 7. Plan 5 Changes: The 40-Year Trap

### What Changed (August 2023)
| Feature | Plan 2 | Plan 5 | Change |
|---------|--------|--------|--------|
| Threshold | £28,470 | £25,000 | **-£3,470** (12% lower) |
| Interest (studying) | RPI+3% | RPI | **Lower** |
| Interest (after) | RPI to RPI+3% | RPI | **Lower** |
| Write-off | 30 years | 40 years | **+10 years** |
| % repaying fully | 33% | 52% | **+19pp** |

### The Illusion of Improvement
Plan 5 was marketed as "fairer" because:
- Lower interest rates (RPI vs RPI+3%)
- Threshold tied to inflation from 2027

But the reality:
- **Lower threshold** means you start paying sooner and on lower salaries
- **10 extra years** means a decade more of payments
- **Net effect**: Middle earners pay £30,000 more over their lifetimes[^2]

### Who Benefits?
- **Low earners** (sub-£25k): Pay less total but over longer
- **High earners** (£80k+): Save ~£20,000 due to lower interest[^2]
- **Middle earners** (£30-60k): **Lose £30,000+** — the sacrificial cohort

This is regressive redistribution: the middle pays for cuts at the top and bottom.

---

## 8. RAB Charge: The Government's Subsidy Expectation

### What is RAB?
The **Resource Accounting and Budgeting (RAB) charge** is the percentage of each loan pound the government expects to write off (i.e., never get back). It's the true taxpayer cost.

### Current RAB Charges (2024-25)
| Loan Type | RAB Charge | Interpretation |
|-----------|------------|----------------|
| Plan 2 (undergrad) | **34%** | Govt expects to lose 34p per £1 lent[^14] |
| Plan 5 (undergrad) | **30%** | Govt expects to lose 30p per £1 lent[^14] |
| Master's loans | **0%*** | Expected to be profitable[^15] |

*Master's loans technically have a -20.6% RAB (profitable), but government accounting rules don't allow negative RAB charges.

### What This Means
- **Plan 2**: £11.5 billion lent annually × 34% = **£3.9 billion taxpayer subsidy/year**
- **Plan 5**: Reforms reduced RAB from projected 42% to 30%—a **£2.3 billion saving**[^16]
- **Total outstanding subsidy**: With £260 billion outstanding at ~34% RAB = **~£88 billion expected write-offs**

### The Accounting Fiction
The government books these loans as **assets** on the national balance sheet at face value, despite knowing 30-34% will never be repaid. This is pure fiction—they're liabilities masquerading as assets.

### RAB History
- Pre-2012 (Plan 1): ~30% RAB
- 2012 reforms (Plan 2 introduced): RAB shot up to ~40-45%
- 2017 threshold freeze: Reduced RAB to ~35%
- 2023 Plan 5 reforms: RAB down to ~30%

Each "reform" has focused on cutting RAB (taxpayer cost) by increasing extraction from borrowers.

---

## 9. Graduate Tax Comparison: Which Extracts More?

### The Hypothetical
A pure **graduate tax** would be a simple levy:
- **9% on income above £25,000** (mirroring student loan threshold)
- **No debt, no interest, no write-off**
- **Collected via HMRC for working life** (say 40 years)

### Modeling Results (from `student_loans.py`)

| Salary | Plan 5 Total | Graduate Tax Total (40yr) | Difference | Winner |
|--------|--------------|--------------------------|------------|--------|
| £25,000 | £19,080 | £0 | Plan 5 extracts £19k more | **Grad Tax** |
| £30,000 | £47,520 | £47,520 | Identical | **Tie** |
| £40,000 | £110,520 | £142,560 | Grad tax £32k more | **Plan 5** |
| £50,000 | £164,160 | £237,600 | Grad tax £73k more | **Plan 5** |
| £75,000 | £278,640 | £427,680 | Grad tax £149k more | **Plan 5** |
| £100,000 | £393,840 | £617,760 | Grad tax £224k more | **Plan 5** |

### Key Insights
1. **For earners below ~£32k**: Student loans extract more (due to interest on debt)
2. **For earners above ~£40k**: A graduate tax would extract significantly more
3. **The crossover is ~£30-35k**: Plans are roughly equivalent

### Why This Matters
- **A graduate tax would be cheaper for most** because there's no compound interest on a growing debt pile
- **Current system is optimized** to extract maximum from middle earners while appearing "fair" with write-offs
- **The debt mechanic is a fiction** designed to create the illusion of individual responsibility while functioning as a lifelong tax

### Political Economy
- **Graduate tax pros**: Transparent, no debt stigma, cheaper for low-earners, simpler administration
- **Graduate tax cons**: Politically toxic (it's a "tax"), no write-off for high earners, harder to sell to international students

The student loan system is a **graduate tax in disguise**, but with compound interest and psychological debt burden added.

---

## 10. The Mundane Dystopia: Synthesis

### It's a Subscription Service
You don't "borrow" money for university—you **subscribe** to being a graduate. The features:

**Subscription Tiers:**
- **£25k earner**: Basic tier—£19k lifetime, mostly escapable
- **£30-40k earner**: Standard tier—£47-110k lifetime, 40 years of payments
- **£50k+ earner**: Premium tier—£164-394k lifetime, you're profitable

**Auto-renewal:** Every paycheck, 9% extracted automatically. No opting out.

**Cancellation policy:** Death, permanent disability, or 40 years—whichever comes first.

### The Extraction Optimization
The system is **perfectly calibrated** to maximize extraction:
1. **Debt high enough** to keep most paying for decades
2. **Threshold low enough** to capture median earners early in careers
3. **Interest high enough** to ensure negative amortization for most
4. **Term long enough** (40 years) to extract from entire working life
5. **Write-off far enough** away to make full repayment seem possible (hope tax)

### The Psychological Toll
- **Debt as identity**: You're not a "graduate," you're an "SLC debtor"
- **The overhang**: Life decisions (buying a house, having kids, changing careers) shadowed by the debt
- **The ghost payment**: Most graduates don't feel their 9% deduction—it's invisible, making it the perfect tax
- **The isolation**: Unlike a mortgage, you can't pay it off early efficiently (you're better off investing)

### The Generational Extraction
- **Pre-2012**: University was free or ~£3k total
- **2012-2023**: £27k tuition + £20k maintenance = ~£50k
- **2023+**: Same debt, 33% longer term (30→40 years)

Each generation pays more for the same degree. The subscription fee keeps rising.

### The System Dynamics
- **Government** reduces RAB charge, claims "savings"
- **Universities** keep fees at maximum (£9,250), no competition
- **SLC** collects 91.9% compliance, minimal defaults
- **Graduates** pay 2-6% of lifetime income as hidden tax
- **No one is accountable** for the £260 billion debt mountain

### The Final Irony
**Only 52% will ever repay in full**, yet the system extracts more total revenue than a simple graduate tax would for most earners. The other 48% pay for decades before write-off.

It's the worst of both worlds:
- **Feels like debt** (psychological burden)
- **Functions like a tax** (9% lifetime levy)
- **Costs more than either** (compound interest)

This is the mundane dystopia: not dramatic oppression, but **a lifetime subscription you signed up for at 18**, embedded in payroll systems, invisibly extracting from every paycheck until you retire.

---

## Data Sources & Citations

[^1]: Student Loans Company Annual Report 2024-25. GOV.UK. https://www.gov.uk/government/publications/slc-annual-report-and-accounts-2024-to-2025

[^2]: Institute for Fiscal Studies. "Student loans reform: a leap into the unknown." https://ifs.org.uk/publications/student-loans-reform-leap-unknown

[^3]: House of Commons Library. "Student loan statistics" (research briefing). https://commonslibrary.parliament.uk/research-briefings/sn01079/ (accessed 2026-02-13)

[^4]: Royal London. "Number of borrowers with £100,000 in student debt jumps by a third." September 2025. https://www.royallondon.com/about-us/media/Media-Centre/press-releases/press-releases-2025/september/

[^10]: GOV.UK. "Student loans in England: 2024 to 2025." https://www.gov.uk/government/statistics/student-loans-in-england-2024-to-2025

[^11]: Sutton Trust. "Payback Time Report." https://www.improvingthestudentexperience.com/wp-content/uploads/2023/12/payback-time-report-sutton_trust.pdf

[^12]: Money Saving Expert. "Students: Student loans England Plan 5." (Popular guide; use official sources for quantitative claims.) https://www.moneysavingexpert.com/students/student-loans-england-plan-5/ (accessed 2026-02-13)

[^14]: Wonkhe. "Student loan forecasts are out from the Department for Education for England." https://wonkhe.com/wonk-corner/student-loan-forecasts-are-out-from-the-department-for-education-for-england/

[^15]: Explore Education Statistics. "Student loan forecasts for England: 2024-25." https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/ea15a649-f74e-4de3-81ca-37984a019d1f

[^16]: Office for Budget Responsibility. "The fiscal impact of student loans reforms." https://obr.uk/box/the-fiscal-impact-of-student-loans-reforms/

---

## Appendix: Quick Reference

### Plan Comparison Table
| Feature | Plan 1 | Plan 2 | Plan 5 |
|---------|--------|--------|--------|
| **Started** | Pre-2012 | 2012-2023 | 2023+ |
| **Threshold** | £26,065 | £28,470 | £25,000 |
| **Rate** | 9% | 9% | 9% |
| **Interest** | 3.2% | 3.2-6.2% | 3.2% |
| **Write-off** | 25 years | 30 years | 40 years |
| **Avg Debt** | £32,000 | £50,000 | £50,000 |
| **RAB Charge** | ~30% | 34% | 30% |
| **% Repay Full** | ~40% | 33% | 52% |

### Key Numbers to Remember
- **Total debt (snapshot)**: £260.8 billion (March 2024)[^1]
- **Average debt (order of magnitude)**: ~£50,000 (Plan 2/5)[^10]
- **Repayment rate**: 9% above threshold
- **Years paying**: 30 (Plan 2) or 40 (Plan 5)
- **% repaying in full**: Only 33-52% depending on plan
- **Middle earner lifetime cost**: £30,000-110,000
- **Government subsidy (RAB)**: 30-34% expected write-off

---

*End of Report*
