#!/usr/bin/env python3
"""
UK Student Loan Lifetime Repayment Calculator
Models the dystopian extraction mechanics of the student loan system across different salary bands.

Provenance summary (from `research/data/provenance/model_inputs/student_loans_inputs.json`):
- Derived from primary sources: plan repayment thresholds, repayment rates, write-off periods,
  and Plan 1/Plan 2 interest-rate table inputs
- Explicit assumptions: salary bands, salary growth scenario, graduate-tax rate and working years,
  Plan 5 interest-rate proxy, average debt assumptions; graduate-tax threshold/rate are auto-set
  from extracted repayment policy parameters
- Full register: `research/data/provenance/ASSUMPTION_REGISTER.md`
"""

import csv
from dataclasses import dataclass
from typing import Dict, List, Tuple
from pathlib import Path
from provenance import load_model_inputs, record_run


@dataclass
class LoanPlan:
    """Configuration for a student loan plan."""
    name: str
    threshold: float  # Annual repayment threshold
    rate: float  # Repayment rate (as decimal, e.g., 0.09 for 9%)
    interest_rate: float  # Average interest rate over lifetime
    write_off_years: int  # Years until debt is written off
    avg_debt: float  # Average debt at graduation


def _build_plan(plan_data: Dict) -> LoanPlan:
    return LoanPlan(
        name=plan_data["name"],
        threshold=plan_data["threshold"],
        rate=plan_data["rate"],
        interest_rate=plan_data["interest_rate"],
        write_off_years=plan_data["write_off_years"],
        avg_debt=plan_data["avg_debt"],
    )


_INPUTS = load_model_inputs("student_loans_inputs")
_PLANS = [_build_plan(plan_data) for plan_data in _INPUTS["plans"]]
_PLAN_MAP = {plan.name: plan for plan in _PLANS}

PLAN_1 = _PLAN_MAP["Plan 1"]
PLAN_2 = _PLAN_MAP["Plan 2"]
PLAN_5 = _PLAN_MAP["Plan 5"]

SALARY_BANDS = _INPUTS["salary_bands"]["values"]
DEFAULT_SALARY_GROWTH = _INPUTS["scenario_parameters"]["default_salary_growth"]["value"]
GRAD_TAX_SETTINGS = _INPUTS["scenario_parameters"]["graduate_tax"]


def calculate_lifetime_repayment(
    starting_salary: float,
    plan: LoanPlan,
    salary_growth: float = DEFAULT_SALARY_GROWTH,
    years: int = None
) -> Dict:
    """
    Calculate lifetime student loan repayment for a given starting salary.
    
    Args:
        starting_salary: Initial annual salary
        plan: LoanPlan configuration
        salary_growth: Annual salary growth rate (default 2%)
        years: Years to simulate (defaults to plan's write-off period)
    
    Returns:
        Dictionary with repayment details
    """
    if years is None:
        years = plan.write_off_years
    
    # Initialize
    remaining_debt = plan.avg_debt
    total_repaid = 0
    salary = starting_salary
    
    yearly_breakdown = []
    
    for year in range(years):
        # Calculate repayment for this year
        if salary > plan.threshold:
            annual_repayment = (salary - plan.threshold) * plan.rate
        else:
            annual_repayment = 0
        
        # Add interest to remaining debt
        interest_accrued = remaining_debt * plan.interest_rate
        
        # Update debt
        remaining_debt = remaining_debt + interest_accrued - annual_repayment
        
        # Can't have negative debt
        if remaining_debt < 0:
            annual_repayment += remaining_debt  # Adjust final payment
            remaining_debt = 0
        
        total_repaid += annual_repayment
        
        yearly_breakdown.append({
            'year': year + 1,
            'salary': salary,
            'repayment': annual_repayment,
            'interest_accrued': interest_accrued,
            'remaining_debt': remaining_debt
        })
        
        # Increase salary for next year
        salary *= (1 + salary_growth)
        
        # Break if debt is fully repaid
        if remaining_debt == 0:
            break

    simulated_years = len(yearly_breakdown)

    total_income = 0.0
    current_salary = starting_salary
    for _ in range(simulated_years):
        total_income += current_salary
        current_salary *= (1 + salary_growth)
    
    # Calculate effective metrics
    effective_tax_rate = (total_repaid / total_income) if total_income > 0 else 0
    amount_vs_borrowed = (total_repaid / plan.avg_debt) if plan.avg_debt > 0 else 0
    written_off = max(0, remaining_debt)
    fully_repaid = (written_off == 0)
    
    return {
        'starting_salary': starting_salary,
        'plan': plan.name,
        'total_repaid': total_repaid,
        'amount_borrowed': plan.avg_debt,
        'amount_vs_borrowed': amount_vs_borrowed,
        'written_off': written_off,
        'fully_repaid': fully_repaid,
        'years_to_repay': year + 1 if fully_repaid else years,
        'effective_annual_tax': total_repaid / simulated_years if simulated_years > 0 else 0,
        'effective_tax_rate': effective_tax_rate,
        'simulated_years': simulated_years,
        'yearly_breakdown': yearly_breakdown
    }


def compare_plans_by_salary(salary: float) -> List[Dict]:
    """Compare all three plans for a given salary."""
    plans = [PLAN_1, PLAN_2, PLAN_5]
    results = []
    
    for plan in plans:
        result = calculate_lifetime_repayment(salary, plan)
        results.append({
            'Plan': result['plan'],
            'Starting Salary': f"£{salary:,.0f}",
            'Total Repaid': f"£{result['total_repaid']:,.0f}",
            'Borrowed': f"£{result['amount_borrowed']:,.0f}",
            'Repaid vs Borrowed': f"{result['amount_vs_borrowed']:.2f}x",
            'Written Off': f"£{result['written_off']:,.0f}",
            'Fully Repaid?': 'Yes' if result['fully_repaid'] else 'No',
            'Years': result['years_to_repay'],
            'Effective Tax Rate': f"{result['effective_tax_rate']*100:.1f}%"
        })
    
    return results


def analyze_salary_bands() -> List[Dict]:
    """Analyze repayment across multiple salary bands."""
    salary_bands = SALARY_BANDS
    
    all_results = []
    for salary in salary_bands:
        for plan in [PLAN_2, PLAN_5]:  # Focus on current plans
            result = calculate_lifetime_repayment(salary, plan)
            all_results.append({
                'Salary': f"£{salary:,.0f}",
                'Plan': result['plan'],
                'Total Repaid': result['total_repaid'],
                'Borrowed': result['amount_borrowed'],
                'Multiplier': result['amount_vs_borrowed'],
                'Written Off': result['written_off'],
                'Fully Repaid': result['fully_repaid'],
                'Years': result['years_to_repay'],
                'Annual Cost': result['effective_annual_tax'],
                'Effective Tax %': result['effective_tax_rate'] * 100
            })
    
    return all_results


def calculate_hidden_tax_rate(salary: float, plan: LoanPlan) -> float:
    """
    Calculate the 'hidden tax' - what % of income goes to loan repayment.
    This shows how student loans function as a graduate tax.
    """
    result = calculate_lifetime_repayment(salary, plan, salary_growth=DEFAULT_SALARY_GROWTH)
    
    # Total income over the period
    total_income = 0
    current_salary = salary
    for _ in range(result['years_to_repay']):
        total_income += current_salary
        current_salary *= (1 + DEFAULT_SALARY_GROWTH)
    
    if total_income > 0:
        return (result['total_repaid'] / total_income) * 100
    return 0


def compare_to_graduate_tax() -> List[Dict]:
    """
    Compare student loans to a hypothetical 9% graduate tax above £25k.
    Shows which system extracts more.
    """
    salary_bands = SALARY_BANDS
    results = []
    
    # Hypothetical graduate tax: 9% above £25k for life
    grad_tax_threshold = GRAD_TAX_SETTINGS["threshold"]
    grad_tax_rate = GRAD_TAX_SETTINGS["rate"]
    working_years = GRAD_TAX_SETTINGS["working_years"]
    
    for salary in salary_bands:
        # Plan 5 repayment
        plan5_result = calculate_lifetime_repayment(salary, PLAN_5)
        
        # Graduate tax calculation (40 years)
        grad_tax_total = 0
        current_salary = salary
        for _ in range(working_years):
            if current_salary > grad_tax_threshold:
                grad_tax_total += (current_salary - grad_tax_threshold) * grad_tax_rate
            current_salary *= (1 + DEFAULT_SALARY_GROWTH)
        
        results.append({
            'Salary': f"£{salary:,.0f}",
            'Plan 5 Total': f"£{plan5_result['total_repaid']:,.0f}",
            'Graduate Tax Total': f"£{grad_tax_total:,.0f}",
            'Difference': f"£{(grad_tax_total - plan5_result['total_repaid']):,.0f}",
            'Plan 5 Extracts More?': grad_tax_total < plan5_result['total_repaid']
        })
    
    return results


def print_table(data: List[Dict]):
    """Print a list of dictionaries as a formatted table."""
    if not data:
        return
    
    # Get headers
    headers = list(data[0].keys())
    
    # Calculate column widths
    col_widths = {}
    for header in headers:
        col_widths[header] = len(str(header))
        for row in data:
            col_widths[header] = max(col_widths[header], len(str(row[header])))
    
    # Print header
    header_line = " | ".join(str(h).ljust(col_widths[h]) for h in headers)
    print(header_line)
    print("-" * len(header_line))
    
    # Print rows
    for row in data:
        row_line = " | ".join(str(row[h]).ljust(col_widths[h]) for h in headers)
        print(row_line)


def print_dystopia_summary():
    """
    Print the key dystopian insights about the system.
    """
    print("=" * 80)
    print("UK STUDENT LOANS: THE LIFE SUBSCRIPTION")
    print("=" * 80)
    print()
    
    print("EXTRACTION RATES BY SALARY (Plan 5, starting 2023+)")
    print("-" * 80)
    all_results = analyze_salary_bands()
    plan5_results = [r for r in all_results if r['Plan'] == 'Plan 5']
    
    for row in plan5_results:
        print(f"\n{row['Salary']} earner:")
        print(f"  • Pays back: £{row['Total Repaid']:,.0f} (borrowed £{row['Borrowed']:,.0f})")
        print(f"  • Multiplier: {row['Multiplier']:.2f}x original debt")
        print(f"  • Annual cost: £{row['Annual Cost']:,.0f}/year")
        print(f"  • Effective tax: {row['Effective Tax %']:.1f}% of lifetime income")
        if row['Fully Repaid']:
            print(f"  • Fully repaid in {row['Years']} years ✓")
        else:
            print(f"  • £{row['Written Off']:,.0f} written off after {row['Years']} years")
    
    print("\n" + "=" * 80)
    print("PLAN 2 VS PLAN 5: HOW MUCH WORSE?")
    print("=" * 80)
    
    for salary in [30_000, 50_000, 75_000]:
        plan2 = calculate_lifetime_repayment(salary, PLAN_2)
        plan5 = calculate_lifetime_repayment(salary, PLAN_5)
        difference = plan5['total_repaid'] - plan2['total_repaid']
        
        print(f"\n£{salary:,} earner:")
        print(f"  Plan 2: £{plan2['total_repaid']:,.0f} over {PLAN_2.write_off_years} years")
        print(f"  Plan 5: £{plan5['total_repaid']:,.0f} over {PLAN_5.write_off_years} years")
        print(f"  Plan 5 extracts £{difference:,.0f} MORE ({difference/plan2['total_repaid']*100:.1f}% increase)")
    
    print("\n" + "=" * 80)
    print("STUDENT LOANS VS GRADUATE TAX")
    print("=" * 80)
    print()
    comparison_results = compare_to_graduate_tax()
    print_table(comparison_results)
    
    print("\n" + "=" * 80)
    print("THE HIDDEN TAX RATES")
    print("=" * 80)
    print("\nWhat % of your lifetime income goes to student loans?")
    print("(This is the 'subscription fee' for having gone to university)\n")
    
    for salary in [25_000, 30_000, 40_000, 50_000, 75_000, 100_000]:
        hidden_tax = calculate_hidden_tax_rate(salary, PLAN_5)
        print(f"  £{salary:,}: {hidden_tax:.2f}% of lifetime income")


def save_to_csv(data: List[Dict], filename: str):
    """Save a list of dictionaries to CSV."""
    if not data:
        return

    output_path = Path(filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)


if __name__ == "__main__":
    print_dystopia_summary()
    
    # Optional: Save detailed breakdowns to CSV
    print("\n" + "=" * 80)
    print("Saving detailed analysis to CSVs...")
    print("=" * 80)
    
    output_dir = Path(__file__).resolve().parents[1] / 'research' / 'data'
    output_dir.mkdir(parents=True, exist_ok=True)

    all_results = analyze_salary_bands()
    save_to_csv(all_results, str(output_dir / 'repayment-analysis.csv'))
    print("✓ Saved: research/data/repayment-analysis.csv")
    
    comparison = compare_to_graduate_tax()
    save_to_csv(comparison, str(output_dir / 'graduate-tax-comparison.csv'))
    print("✓ Saved: research/data/graduate-tax-comparison.csv")
    
    # Generate detailed breakdown for a median earner
    median_result = calculate_lifetime_repayment(35_000, PLAN_5)
    save_to_csv(median_result['yearly_breakdown'], str(output_dir / 'yearly-breakdown-35k.csv'))
    print("✓ Saved: research/data/yearly-breakdown-35k.csv (£35k earner, Plan 5)")

    record_run(
        script_name=Path(__file__).name,
        input_files=["research/data/provenance/model_inputs/student_loans_inputs.json"],
        output_files=[
            "research/data/repayment-analysis.csv",
            "research/data/graduate-tax-comparison.csv",
            "research/data/yearly-breakdown-35k.csv",
        ],
    )
