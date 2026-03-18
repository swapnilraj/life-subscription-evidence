#!/usr/bin/env python3
"""
Subscription Economy Analysis: UK Household "Stack" Modeling
Compares 2005 vs 2025 ownership vs subscription models
Calculates subscription spend as % of household income
Shows growth trajectory and ownership erosion

Provenance summary (from `research/data/provenance/model_inputs/subscriptions_inputs.json`):
- Derived from primary sources: monthly income baseline (with backcast scaling)
- Explicit assumptions: category-level household stack compositions by year
- Computed from modeled stack definitions: subscription count trajectory
- Full register: `research/data/provenance/ASSUMPTION_REGISTER.md`
"""

from dataclasses import dataclass
from typing import Dict, List
import json
from pathlib import Path
from provenance import load_model_inputs, record_run


@dataclass
class MonthlyExpense:
    """Represents a monthly recurring expense"""
    category: str
    amount: float
    is_subscription: bool = False  # True if discretionary subscription, False if utility/necessity
    owned_in_2005: bool = False  # True if this represented ownership rather than access


class HouseholdStack:
    """Models monthly recurring payments for a UK household"""
    
    def __init__(self, year: int, household_type: str = "median"):
        self.year = year
        self.household_type = household_type
        self.expenses: List[MonthlyExpense] = []
        
    def add_expense(self, category: str, amount: float, is_subscription: bool = False, owned_in_2005: bool = False):
        """Add a monthly expense to the stack"""
        self.expenses.append(MonthlyExpense(category, amount, is_subscription, owned_in_2005))
    
    def total_monthly(self) -> float:
        """Calculate total monthly expenses"""
        return sum(exp.amount for exp in self.expenses)
    
    def total_subscriptions(self) -> float:
        """Calculate total discretionary subscription spending"""
        return sum(exp.amount for exp in self.expenses if exp.is_subscription)
    
    def total_owned_converted(self) -> float:
        """Calculate spending on things that were owned in 2005 but are now subscribed"""
        return sum(exp.amount for exp in self.expenses if exp.owned_in_2005)
    
    def breakdown(self) -> Dict[str, float]:
        """Get expense breakdown by category"""
        return {exp.category: exp.amount for exp in self.expenses}
    
    def summary(self) -> Dict[str, float]:
        """Generate summary statistics"""
        return {
            'total_monthly': self.total_monthly(),
            'total_subscriptions': self.total_subscriptions(),
            'total_owned_converted': self.total_owned_converted(),
            'num_subscriptions': sum(1 for exp in self.expenses if exp.is_subscription),
            'year': self.year
        }


_INPUTS = load_model_inputs("subscriptions_inputs")
_STACKS = _INPUTS["household_stacks"]
_INCOMES = {int(year): value for year, value in _INPUTS["income_monthly"].items() if year != "provenance"}


def build_stack(year: int) -> HouseholdStack:
    """Build household stack for a configured year."""
    stack_data = _STACKS[str(year)]
    stack = HouseholdStack(year, stack_data.get("household_type", "median"))
    for expense in stack_data["expenses"]:
        stack.add_expense(
            expense["category"],
            expense["amount"],
            is_subscription=expense.get("is_subscription", False),
            owned_in_2005=expense.get("owned_in_2005", False),
        )
    return stack


def build_2005_stack() -> HouseholdStack:
    return build_stack(2005)


def build_2015_stack() -> HouseholdStack:
    return build_stack(2015)


def build_2025_stack() -> HouseholdStack:
    return build_stack(2025)


def calculate_income_percentage(stack: HouseholdStack, median_income_monthly: float) -> Dict[str, float]:
    """Calculate expenses as percentage of household income"""
    total = stack.total_monthly()
    subs = stack.total_subscriptions()
    owned_converted = stack.total_owned_converted()
    
    return {
        'total_pct': (total / median_income_monthly) * 100,
        'subscriptions_pct': (subs / median_income_monthly) * 100,
        'owned_converted_pct': (owned_converted / median_income_monthly) * 100,
        'income_monthly': median_income_monthly
    }


def generate_ascii_chart():
    """Generate ASCII art chart for visualization"""
    stacks = {
        2005: build_2005_stack(),
        2015: build_2015_stack(),
        2025: build_2025_stack()
    }
    
    incomes = _INCOMES
    
    chart = []
    chart.append("\n" + "="*80)
    chart.append("SUBSCRIPTION GROWTH VISUALIZATION (ASCII)")
    chart.append("="*80)
    
    for year in [2005, 2015, 2025]:
        stack = stacks[year]
        total = stack.total_monthly()
        subs = stack.total_subscriptions()
        income = incomes[year]
        pct = (total / income) * 100
        
        # Create bar graph
        bar_length = int(pct)
        bar = "█" * bar_length
        
        chart.append(f"\n{year}: £{total:.0f}/mo ({pct:.1f}% of income)")
        chart.append(f"[{bar}]")
        chart.append(f"Subscriptions: £{subs:.0f}/mo ({(subs/income)*100:.1f}% of income)")
    
    # Growth trajectory
    chart.append("\n" + "="*80)
    chart.append("SUBSCRIPTION COUNT TRAJECTORY")
    chart.append("="*80)
    years = _INPUTS["subscription_count_series"]["years"]
    counts = _INPUTS["subscription_count_series"]["counts"]
    
    for year, count in zip(years, counts):
        dots = "●" * int(count * 2)
        chart.append(f"{year}: {count} avg subscriptions  {dots}")
    
    return "\n".join(chart)


def generate_report():
    """Generate comprehensive text report"""
    print("=" * 80)
    print("UK HOUSEHOLD SUBSCRIPTION ECONOMY ANALYSIS")
    print("Comparing 2005 vs 2025: Ownership → Access")
    print("=" * 80)
    print()
    
    # Build stacks
    stack_2005 = build_2005_stack()
    stack_2015 = build_2015_stack()
    stack_2025 = build_2025_stack()
    
    # Income data
    incomes = _INCOMES
    
    # Print 2005 breakdown
    print("\n📊 2005 HOUSEHOLD STACK")
    print("-" * 80)
    print(f"{'Category':<35} {'Monthly Cost':>15} {'Type':>15}")
    print("-" * 80)
    for exp in stack_2005.expenses:
        exp_type = "Subscription" if exp.is_subscription else "Utility/Necessity"
        print(f"{exp.category:<35} £{exp.amount:>14.2f} {exp_type:>15}")
    print("-" * 80)
    summary_2005 = stack_2005.summary()
    income_pct_2005 = calculate_income_percentage(stack_2005, incomes[2005])
    print(f"{'TOTAL MONTHLY STACK':<35} £{summary_2005['total_monthly']:>14.2f}")
    print(f"{'Discretionary Subscriptions':<35} £{summary_2005['total_subscriptions']:>14.2f}")
    print(f"{'Median Monthly Income':<35} £{incomes[2005]:>14.2f}")
    print(f"{'Stack as % of Income':<35} {income_pct_2005['total_pct']:>14.1f}%")
    print(f"{'Subscriptions as % of Income':<35} {income_pct_2005['subscriptions_pct']:>14.1f}%")
    
    # Print 2025 breakdown
    print("\n\n📊 2025 HOUSEHOLD STACK")
    print("-" * 80)
    print(f"{'Category':<35} {'Monthly Cost':>15} {'Type':>15}")
    print("-" * 80)
    for exp in sorted(stack_2025.expenses, key=lambda x: x.amount, reverse=True):
        exp_type = "🔄 Subscription" if exp.is_subscription else "⚡ Utility"
        owned_marker = " [Was Owned]" if exp.owned_in_2005 else ""
        print(f"{exp.category:<35} £{exp.amount:>14.2f} {exp_type:>15}{owned_marker}")
    print("-" * 80)
    summary_2025 = stack_2025.summary()
    income_pct_2025 = calculate_income_percentage(stack_2025, incomes[2025])
    print(f"{'TOTAL MONTHLY STACK':<35} £{summary_2025['total_monthly']:>14.2f}")
    print(f"{'Discretionary Subscriptions':<35} £{summary_2025['total_subscriptions']:>14.2f}")
    print(f"{'Previously Owned, Now Subscribed':<35} £{summary_2025['total_owned_converted']:>14.2f}")
    print(f"{'Median Monthly Income':<35} £{incomes[2025]:>14.2f}")
    print(f"{'Stack as % of Income':<35} {income_pct_2025['total_pct']:>14.1f}%")
    print(f"{'Subscriptions as % of Income':<35} {income_pct_2025['subscriptions_pct']:>14.1f}%")
    print(f"{'Owned→Subscribed as % of Income':<35} {income_pct_2025['owned_converted_pct']:>14.1f}%")
    
    # Comparison
    print("\n\n📈 GROWTH ANALYSIS (2005 → 2025)")
    print("=" * 80)
    total_increase = summary_2025['total_monthly'] - summary_2005['total_monthly']
    total_pct_increase = (total_increase / summary_2005['total_monthly']) * 100
    income_increase = incomes[2025] - incomes[2005]
    income_pct_increase = (income_increase / incomes[2005]) * 100
    
    print(f"Total Stack Increase:        £{total_increase:.2f}/month (+{total_pct_increase:.1f}%)")
    print(f"Median Income Increase:      £{income_increase:.2f}/month (+{income_pct_increase:.1f}%)")
    print(f"")
    print(f"Stack grew {total_pct_increase:.1f}% while income grew only {income_pct_increase:.1f}%")
    print(f"Stack outpaced income by {total_pct_increase - income_pct_increase:.1f} percentage points")
    print(f"")
    categories_2005 = {expense.category for expense in stack_2005.expenses}
    new_subscription_categories = [
        expense
        for expense in stack_2025.expenses
        if expense.is_subscription and expense.category not in categories_2005
    ]
    converted_categories = [expense for expense in stack_2025.expenses if expense.owned_in_2005]

    print(f"New Subscription Categories Added (model assumptions):")
    for expense in sorted(new_subscription_categories, key=lambda item: item.amount, reverse=True):
        print(f"  • {expense.category:<45} £{expense.amount:>7.2f}/month")
    if not new_subscription_categories:
        print("  • None")

    print(f"")
    print(f"Ownership → Subscription Conversions (model assumptions):")
    for expense in sorted(converted_categories, key=lambda item: item.amount, reverse=True):
        print(f"  • {expense.category:<45} £{expense.amount:>7.2f}/month")
    print(f"  TOTAL:                                           £{summary_2025['total_owned_converted']:.2f}/month")
    print(f"")
    print(f"💡 What you used to BUY and OWN, you now RENT and ACCESS.")
    
    # Annual costs
    print("\n\n💰 ANNUAL COSTS")
    print("=" * 80)
    annual_2005 = summary_2005['total_monthly'] * 12
    annual_2025 = summary_2025['total_monthly'] * 12
    annual_subs_2025 = summary_2025['total_subscriptions'] * 12
    
    print(f"2005 Annual Stack:           £{annual_2005:,.2f}")
    print(f"2025 Annual Stack:           £{annual_2025:,.2f}")
    print(f"2025 Subscriptions Only:     £{annual_subs_2025:,.2f}")
    print(f"")
    print(f"You now pay £{annual_2025 - annual_2005:,.2f} MORE per year than in 2005")
    print(f"Of that increase, £{annual_subs_2025:,.2f} is discretionary subscriptions")
    
    # 10-year analysis
    print("\n\n⏰ 10-YEAR COST ANALYSIS")
    print("=" * 80)
    print(f"2005 model over 10 years:    £{annual_2005 * 10:,.2f}")
    print(f"2025 model over 10 years:    £{annual_2025 * 10:,.2f}")
    print(f"Difference:                  £{(annual_2025 - annual_2005) * 10:,.2f}")
    print(f"")
    print(f"What you get for that £{(annual_2025 - annual_2005) * 10:,.2f} extra:")
    print(f"  → Access to content you don't own")
    print(f"  → Software licenses that expire if you stop paying")
    print(f"  → A car you'll never own (return in 3 years, repeat cycle)")
    print(f"  → Music you can't keep")
    print(f"  → Films that can be removed from your library")
    print(f"")
    print(f"What you DON'T get:")
    print(f"  → Ownership")
    print(f"  → Equity")
    print(f"  → Assets")
    print(f"  → The ability to stop paying")
    
    # Save data to JSON
    data = {
        '2005': {
            'breakdown': stack_2005.breakdown(),
            'summary': summary_2005,
            'income_analysis': income_pct_2005
        },
        '2015': {
            'breakdown': stack_2015.breakdown(),
            'summary': stack_2015.summary(),
            'income_analysis': calculate_income_percentage(stack_2015, incomes[2015])
        },
        '2025': {
            'breakdown': stack_2025.breakdown(),
            'summary': summary_2025,
            'income_analysis': income_pct_2025
        },
        'growth_analysis': {
            'total_increase_monthly': float(total_increase),
            'total_pct_increase': float(total_pct_increase),
            'income_pct_increase': float(income_pct_increase),
            'stack_vs_income_gap': float(total_pct_increase - income_pct_increase),
            'annual_increase': float((annual_2025 - annual_2005)),
            'ten_year_difference': float((annual_2025 - annual_2005) * 10)
        }
    }
    
    return data


def save_ascii_chart():
    """Save ASCII chart to file"""
    chart = generate_ascii_chart()
    output_path = Path(__file__).resolve().parent / 'subscription_chart.txt'
    with open(output_path, 'w') as f:
        f.write(chart)
    print(chart)
    print(f"\n📊 ASCII chart saved to: {output_path}")
    return str(output_path)


def save_data_json(data: Dict = None):
    """Save analysis data to JSON"""
    if data is None:
        data = generate_report()
    output_path = Path(__file__).resolve().parent / 'subscription_data.json'
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"\n💾 Data saved to: {output_path}")
    return str(output_path)


if __name__ == "__main__":
    print("Starting Subscription Economy Analysis...\n")
    
    # Generate text report
    data = generate_report()
    
    # Save JSON data
    json_path = save_data_json(data)
    
    # Generate and save ASCII visualization
    chart_path = save_ascii_chart()

    pct_2005 = data['2005']['income_analysis']['total_pct']
    pct_2025 = data['2025']['income_analysis']['total_pct']
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\n📁 Output files:")
    print(f"  • Data JSON: {json_path}")
    print(f"  • ASCII Chart: {chart_path}")
    print(f"  • Research: {(Path(__file__).resolve().parents[1] / 'research' / 'data' / 'subscription-economy.md')}")
    print(f"\n🎯 Key Takeaway:")
    print(f"   The average UK household now spends {pct_2025:.1f}% of income on recurring payments,")
    print(f"   up from {pct_2005:.1f}% in 2005. Subscriptions have replaced ownership across music,")
    print(f"   film, software, and even cars. You pay more, own nothing, and can't stop.")
    print(f"\n   Welcome to the subscription dystopia. 🔄")

    record_run(
        script_name=Path(__file__).name,
        input_files=["research/data/provenance/model_inputs/subscriptions_inputs.json"],
        output_files=[
            "code/subscription_data.json",
            "code/subscription_chart.txt",
        ],
    )
