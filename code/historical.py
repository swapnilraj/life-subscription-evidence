#!/usr/bin/env python3
"""
Historical Household Expenditure Analysis: Ownership → Subscription Shift
===========================================================================

This module processes historical UK household expenditure data to quantify
the shift from ownership-based consumption to subscription-based extraction.

Provenance summary (from `research/data/provenance/model_inputs/historical_inputs.json`):
- Derived from primary sources: 2024 weekly expenditure, 2024 housing/transport category amounts,
  2024 affordability ratio, weekly income baseline derived from ONS household income metric
- Explicit assumptions: 1975/1985/2005/2015 backcast snapshots retained for comparison
- Full register: `research/data/provenance/ASSUMPTION_REGISTER.md`

Author: Research Agent
Date: February 13, 2026
"""

import json
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from enum import Enum
import statistics
from pathlib import Path
from provenance import load_model_inputs, record_run


class SpendingType(Enum):
    """Categorization of spending by ownership model"""
    OWNED = "owned"  # One-time purchase, permanent ownership
    SUBSCRIBED = "subscribed"  # Recurring payment, no ownership
    HYBRID = "hybrid"  # Mix of ownership and subscription (e.g., car finance)
    ESSENTIAL_RECURRING = "essential_recurring"  # Mandatory recurring (utilities)


@dataclass
class ExpenditureCategory:
    """Represents a category of household expenditure"""
    name: str
    spending_type: SpendingType
    weekly_amount: float  # In GBP per week
    as_pct_of_income: float  # Percentage of average income
    description: str = ""
    notes: str = ""
    
    def annual_amount(self) -> float:
        """Convert weekly to annual expenditure"""
        return self.weekly_amount * 52


@dataclass
class HouseholdSnapshot:
    """Snapshot of household expenditure patterns for a given year"""
    year: int
    avg_weekly_income: float
    avg_weekly_expenditure: float
    categories: List[ExpenditureCategory] = field(default_factory=list)
    
    # Key metrics
    house_price_to_income_ratio: float = 0.0
    homeownership_rate: float = 0.0
    household_debt_to_gdp: float = 0.0
    savings_rate: float = 0.0
    real_wage_index: float = 100.0  # Indexed to base year

    def effective_weekly_income(self) -> float:
        """
        Return the best available weekly income estimate.
        Falls back to an implied income derived from savings rate when
        snapshots only provide expenditure-proxy income values.
        """
        if self.avg_weekly_income > self.avg_weekly_expenditure:
            return self.avg_weekly_income

        if 0 < self.savings_rate < 100 and self.avg_weekly_expenditure > 0:
            return self.avg_weekly_expenditure / (1 - self.savings_rate / 100)

        return self.avg_weekly_income
    
    def total_subscribed(self) -> float:
        """Total weekly spending on subscriptions"""
        return sum(
            cat.weekly_amount 
            for cat in self.categories 
            if cat.spending_type in [SpendingType.SUBSCRIBED, SpendingType.ESSENTIAL_RECURRING]
        )
    
    def total_owned(self) -> float:
        """Total weekly spending on ownership-based purchases"""
        return sum(
            cat.weekly_amount 
            for cat in self.categories 
            if cat.spending_type == SpendingType.OWNED
        )
    
    def subscription_pct_of_income(self) -> float:
        """Percentage of income going to subscription/recurring payments"""
        income = self.effective_weekly_income()
        if income == 0:
            return 0.0
        return (self.total_subscribed() / income) * 100
    
    def ownership_pct_of_income(self) -> float:
        """Percentage of income going to ownership purchases"""
        income = self.effective_weekly_income()
        if income == 0:
            return 0.0
        return (self.total_owned() / income) * 100
    
    def discretionary_income(self) -> float:
        """Weekly income after all expenditure"""
        return self.effective_weekly_income() - self.avg_weekly_expenditure
    
    def discretionary_pct(self) -> float:
        """Discretionary income as % of total income"""
        income = self.effective_weekly_income()
        if income == 0:
            return 0.0
        return (self.discretionary_income() / income) * 100


def load_snapshots_from_provenance() -> List[HouseholdSnapshot]:
    """Load modeled historical snapshots from provenance-linked input JSON."""
    payload = load_model_inputs("historical_inputs")
    snapshots: List[HouseholdSnapshot] = []

    for snapshot_data in payload["snapshots"]:
        categories = [
            ExpenditureCategory(
                name=category["name"],
                spending_type=SpendingType(category["spending_type"]),
                weekly_amount=category["weekly_amount"],
                as_pct_of_income=category["as_pct_of_income"],
                description=category.get("description", ""),
                notes=category.get("notes", ""),
            )
            for category in snapshot_data["categories"]
        ]
        snapshots.append(
            HouseholdSnapshot(
                year=snapshot_data["year"],
                avg_weekly_income=snapshot_data["avg_weekly_income"],
                avg_weekly_expenditure=snapshot_data["avg_weekly_expenditure"],
                categories=categories,
                house_price_to_income_ratio=snapshot_data["house_price_to_income_ratio"],
                homeownership_rate=snapshot_data["homeownership_rate"],
                household_debt_to_gdp=snapshot_data["household_debt_to_gdp"],
                savings_rate=snapshot_data["savings_rate"],
                real_wage_index=snapshot_data["real_wage_index"],
            )
        )

    return snapshots


# Historical data based on research findings
# All amounts in 2024 real terms (adjusted for inflation where noted)

def create_1975_snapshot() -> HouseholdSnapshot:
    """Household expenditure snapshot for 1975"""
    income = 96.39  # Real weekly expenditure (proxy for income after housing)
    
    categories = [
        ExpenditureCategory(
            "Housing (mortgage/rent)", SpendingType.ESSENTIAL_RECURRING,
            30.0, 31.1,
            "Mortgage at 3.6x income ratio (affordable ownership era)"
        ),
        ExpenditureCategory(
            "Food & Non-Alcoholic Beverages", SpendingType.OWNED,
            20.0, 20.8,
            "Grocery purchases, own food outright"
        ),
        ExpenditureCategory(
            "Transport (car ownership)", SpendingType.OWNED,
            10.0, 10.4,
            "Car purchased outright or hire purchase (eventual ownership)"
        ),
        ExpenditureCategory(
            "Utilities (gas, electric, water)", SpendingType.ESSENTIAL_RECURRING,
            8.0, 8.3,
            "Essential services, unavoidable"
        ),
        ExpenditureCategory(
            "Clothing & Footwear", SpendingType.OWNED,
            6.0, 6.2,
            "Purchase and own clothing"
        ),
        ExpenditureCategory(
            "Recreation (CDs, books, cinema)", SpendingType.OWNED,
            5.0, 5.2,
            "Buy media and entertainment, own permanently"
        ),
        ExpenditureCategory(
            "Communication (landline)", SpendingType.SUBSCRIBED,
            1.5, 1.6,
            "Phone line rental, early subscription"
        ),
        ExpenditureCategory(
            "Household goods (appliances)", SpendingType.OWNED,
            4.0, 4.2,
            "Buy washing machine, TV, etc. Own for 10-20 years"
        ),
        ExpenditureCategory(
            "Education", SpendingType.OWNED,
            0.5, 0.5,
            "Free university tuition, minimal costs"
        ),
        ExpenditureCategory(
            "Insurance & Financial Services", SpendingType.SUBSCRIBED,
            3.0, 3.1,
            "Home/car insurance, early recurring payments"
        ),
        ExpenditureCategory(
            "Miscellaneous", SpendingType.HYBRID,
            8.39, 8.7,
            "Other goods and services"
        ),
    ]
    
    return HouseholdSnapshot(
        year=1975,
        avg_weekly_income=96.39,
        avg_weekly_expenditure=96.39,
        categories=categories,
        house_price_to_income_ratio=3.61,  # Estimated for early 1980s
        homeownership_rate=55.0,  # Estimated
        household_debt_to_gdp=55.5,  # 1987 data (earliest available)
        savings_rate=10.0,  # Estimated higher than recent
        real_wage_index=50.0  # Relative to 2024
    )


def create_1985_snapshot() -> HouseholdSnapshot:
    """Household expenditure snapshot for 1985"""
    income = 111.0  # ~15% growth from 1975 in real terms
    
    categories = [
        ExpenditureCategory(
            "Housing (mortgage/rent)", SpendingType.ESSENTIAL_RECURRING,
            35.0, 31.5,
            "Mortgage at 3.6x income (1984 most affordable year)"
        ),
        ExpenditureCategory(
            "Food & Non-Alcoholic Beverages", SpendingType.OWNED,
            22.0, 19.8,
            "Grocery purchases"
        ),
        ExpenditureCategory(
            "Transport (car ownership)", SpendingType.OWNED,
            12.0, 10.8,
            "Mostly outright ownership, some hire purchase"
        ),
        ExpenditureCategory(
            "Utilities (gas, electric, water)", SpendingType.ESSENTIAL_RECURRING,
            9.0, 8.1,
            "Essential utilities"
        ),
        ExpenditureCategory(
            "Clothing & Footwear", SpendingType.OWNED,
            7.0, 6.3,
            "Purchase clothing"
        ),
        ExpenditureCategory(
            "Recreation (CDs, VHS, cinema)", SpendingType.OWNED,
            6.0, 5.4,
            "Media purchases, own permanently"
        ),
        ExpenditureCategory(
            "Communication (landline)", SpendingType.SUBSCRIBED,
            2.0, 1.8,
            "Phone line rental"
        ),
        ExpenditureCategory(
            "Household goods", SpendingType.OWNED,
            4.5, 4.1,
            "Appliances and durables"
        ),
        ExpenditureCategory(
            "Education", SpendingType.OWNED,
            0.5, 0.5,
            "Still largely free tuition"
        ),
        ExpenditureCategory(
            "Insurance & Financial", SpendingType.SUBSCRIBED,
            3.5, 3.2,
            "Insurance premiums"
        ),
        ExpenditureCategory(
            "Miscellaneous", SpendingType.HYBRID,
            9.5, 8.6,
            "Other spending"
        ),
    ]
    
    return HouseholdSnapshot(
        year=1985,
        avg_weekly_income=111.0,
        avg_weekly_expenditure=111.0,
        categories=categories,
        house_price_to_income_ratio=3.61,
        homeownership_rate=63.0,
        household_debt_to_gdp=55.5,
        savings_rate=9.0,
        real_wage_index=60.0
    )


def create_2005_snapshot() -> HouseholdSnapshot:
    """Household expenditure snapshot for 2005"""
    income = 450.0  # Significant real growth pre-financial crisis
    
    categories = [
        ExpenditureCategory(
            "Housing (mortgage/rent)", SpendingType.ESSENTIAL_RECURRING,
            130.0, 28.9,
            "House prices rising; ~5-6x income ratio"
        ),
        ExpenditureCategory(
            "Food & Non-Alcoholic Beverages", SpendingType.OWNED,
            70.0, 15.6,
            "Groceries"
        ),
        ExpenditureCategory(
            "Transport (mix ownership/finance)", SpendingType.HYBRID,
            60.0, 13.3,
            "Mix of owned cars and car finance emerging"
        ),
        ExpenditureCategory(
            "Utilities", SpendingType.ESSENTIAL_RECURRING,
            35.0, 7.8,
            "Gas, electric, water"
        ),
        ExpenditureCategory(
            "Communication (mobile + landline)", SpendingType.SUBSCRIBED,
            12.0, 2.7,
            "Mobile phones becoming universal"
        ),
        ExpenditureCategory(
            "Recreation (DVDs + early digital)", SpendingType.HYBRID,
            35.0, 7.8,
            "Still buying DVDs, but iTunes emerging"
        ),
        ExpenditureCategory(
            "Clothing", SpendingType.OWNED,
            30.0, 6.7,
            "Fashion purchases"
        ),
        ExpenditureCategory(
            "Household goods", SpendingType.OWNED,
            20.0, 4.4,
            "Appliances, furniture"
        ),
        ExpenditureCategory(
            "Education (student loans emerging)", SpendingType.SUBSCRIBED,
            8.0, 1.8,
            "Tuition fees introduced 1998, debt building"
        ),
        ExpenditureCategory(
            "Insurance & Financial", SpendingType.SUBSCRIBED,
            18.0, 4.0,
            "Multiple insurance products"
        ),
        ExpenditureCategory(
            "Miscellaneous", SpendingType.HYBRID,
            32.0, 7.1,
            "Other spending"
        ),
    ]
    
    return HouseholdSnapshot(
        year=2005,
        avg_weekly_income=450.0,
        avg_weekly_expenditure=450.0,
        categories=categories,
        house_price_to_income_ratio=5.5,
        homeownership_rate=70.5,  # Near peak
        household_debt_to_gdp=95.0,  # Rapidly rising
        savings_rate=6.5,
        real_wage_index=90.0
    )


def create_2015_snapshot() -> HouseholdSnapshot:
    """Household expenditure snapshot for 2015"""
    income = 520.0  # Stagnation post-2008
    
    categories = [
        ExpenditureCategory(
            "Housing (mortgage/rent)", SpendingType.ESSENTIAL_RECURRING,
            145.0, 27.9,
            "High prices, declining ownership, rising renting"
        ),
        ExpenditureCategory(
            "Food & Non-Alcoholic Beverages", SpendingType.OWNED,
            80.0, 15.4,
            "Groceries"
        ),
        ExpenditureCategory(
            "Transport (leasing growing)", SpendingType.HYBRID,
            70.0, 13.5,
            "PCP and leasing becoming common"
        ),
        ExpenditureCategory(
            "Utilities", SpendingType.ESSENTIAL_RECURRING,
            40.0, 7.7,
            "Rising energy costs"
        ),
        ExpenditureCategory(
            "Communication (mobile + broadband)", SpendingType.SUBSCRIBED,
            18.0, 3.5,
            "Smartphones + broadband mandatory"
        ),
        ExpenditureCategory(
            "Streaming & Digital Entertainment", SpendingType.SUBSCRIBED,
            10.0, 1.9,
            "Netflix, Spotify emerging"
        ),
        ExpenditureCategory(
            "Recreation (other)", SpendingType.HYBRID,
            25.0, 4.8,
            "Experiences, some ownership"
        ),
        ExpenditureCategory(
            "Clothing", SpendingType.OWNED,
            28.0, 5.4,
            "Fashion"
        ),
        ExpenditureCategory(
            "Household goods", SpendingType.OWNED,
            18.0, 3.5,
            "Appliances"
        ),
        ExpenditureCategory(
            "Education (student loans)", SpendingType.SUBSCRIBED,
            15.0, 2.9,
            "£9,000 tuition fees, large debt stock"
        ),
        ExpenditureCategory(
            "Software & Digital Services", SpendingType.SUBSCRIBED,
            5.0, 1.0,
            "Office 365, cloud storage, apps"
        ),
        ExpenditureCategory(
            "Insurance & Financial", SpendingType.SUBSCRIBED,
            22.0, 4.2,
            "Insurance, pension contributions"
        ),
        ExpenditureCategory(
            "Miscellaneous", SpendingType.HYBRID,
            44.0, 8.5,
            "Other spending"
        ),
    ]
    
    return HouseholdSnapshot(
        year=2015,
        avg_weekly_income=520.0,
        avg_weekly_expenditure=520.0,
        categories=categories,
        house_price_to_income_ratio=7.2,
        homeownership_rate=64.5,
        household_debt_to_gdp=85.0,
        savings_rate=9.3,
        real_wage_index=92.0  # Barely above 2005
    )


def create_2024_snapshot() -> HouseholdSnapshot:
    """Household expenditure snapshot for 2024 (FYE 2024)"""
    income = 650.0  # Slight real growth from 2015
    expenditure = 623.30  # ONS data
    
    categories = [
        ExpenditureCategory(
            "Housing (net), fuel and power", SpendingType.ESSENTIAL_RECURRING,
            113.30, 17.4,
            "Rent/mortgage + utilities; homeownership 65%"
        ),
        ExpenditureCategory(
            "Food & Non-Alcoholic Beverages", SpendingType.OWNED,
            85.0, 13.1,
            "Groceries"
        ),
        ExpenditureCategory(
            "Transport (heavily leased)", SpendingType.HYBRID,
            88.20, 13.6,
            "1.98M vehicles on lease; leasing now standard"
        ),
        ExpenditureCategory(
            "Communication (mobile + broadband)", SpendingType.SUBSCRIBED,
            20.0, 3.1,
            "Smartphone + broadband essential"
        ),
        ExpenditureCategory(
            "Streaming & Digital Entertainment", SpendingType.SUBSCRIBED,
            25.0, 3.8,
            "Netflix, Disney+, Spotify, YouTube Premium, etc."
        ),
        ExpenditureCategory(
            "Recreation & Culture (other)", SpendingType.HYBRID,
            35.0, 5.4,
            "Experiences, gym memberships, other"
        ),
        ExpenditureCategory(
            "Clothing & Footwear", SpendingType.OWNED,
            30.0, 4.6,
            "Fashion purchases"
        ),
        ExpenditureCategory(
            "Household goods", SpendingType.OWNED,
            25.0, 3.8,
            "Appliances, furniture"
        ),
        ExpenditureCategory(
            "Education (student loans)", SpendingType.SUBSCRIBED,
            20.0, 3.1,
            "9% of income over threshold for graduates"
        ),
        ExpenditureCategory(
            "Software & Digital Services", SpendingType.SUBSCRIBED,
            12.0, 1.8,
            "Office 365, Adobe CC, cloud storage, apps, gaming subs"
        ),
        ExpenditureCategory(
            "Subscription Boxes & Services", SpendingType.SUBSCRIBED,
            8.0, 1.2,
            "Meal kits, beauty boxes, etc."
        ),
        ExpenditureCategory(
            "Insurance & Financial Services", SpendingType.SUBSCRIBED,
            30.0, 4.6,
            "Home, car, life, pet insurance; pension"
        ),
        ExpenditureCategory(
            "Health & Personal Care", SpendingType.HYBRID,
            25.0, 3.8,
            "Prescriptions, personal care"
        ),
        ExpenditureCategory(
            "Miscellaneous goods and services", SpendingType.HYBRID,
            106.8, 16.4,
            "Other spending (catch-all)"
        ),
    ]
    
    return HouseholdSnapshot(
        year=2024,
        avg_weekly_income=650.0,
        avg_weekly_expenditure=623.30,
        categories=categories,
        house_price_to_income_ratio=7.7,
        homeownership_rate=65.0,
        household_debt_to_gdp=78.1,
        savings_rate=9.5,
        real_wage_index=93.0  # 15 years of stagnation
    )


class HistoricalAnalysis:
    """Analyzer for historical expenditure trends"""
    
    def __init__(self):
        self.snapshots = load_snapshots_from_provenance()
    
    def subscription_extraction_trend(self) -> List[Tuple[int, float, float]]:
        """
        Calculate subscription extraction as % of income over time.
        Returns: List of (year, subscription_pct, ownership_pct)
        """
        return [
            (s.year, s.subscription_pct_of_income(), s.ownership_pct_of_income())
            for s in self.snapshots
        ]
    
    def wage_vs_housing_divergence(self) -> List[Tuple[int, float, float]]:
        """
        Track real wage growth vs housing affordability.
        Returns: List of (year, real_wage_index, house_price_ratio)
        """
        return [
            (s.year, s.real_wage_index, s.house_price_to_income_ratio)
            for s in self.snapshots
        ]
    
    def ownership_rate_decline(self) -> List[Tuple[int, float]]:
        """
        Homeownership rate over time.
        Returns: List of (year, homeownership_rate)
        """
        return [
            (s.year, s.homeownership_rate)
            for s in self.snapshots
        ]
    
    def debt_accumulation(self) -> List[Tuple[int, float, float]]:
        """
        Household debt and savings rate.
        Returns: List of (year, debt_to_gdp, savings_rate)
        """
        return [
            (s.year, s.household_debt_to_gdp, s.savings_rate)
            for s in self.snapshots
        ]
    
    def discretionary_income_squeeze(self) -> List[Tuple[int, float, float]]:
        """
        Discretionary income available after expenditure.
        Returns: List of (year, discretionary_£, discretionary_%)
        """
        return [
            (s.year, s.discretionary_income(), s.discretionary_pct())
            for s in self.snapshots
        ]
    
    def generate_summary_report(self) -> str:
        """Generate a text summary of key findings"""
        report_lines = [
            "=" * 80,
            "HISTORICAL EXPENDITURE ANALYSIS: OWNERSHIP → SUBSCRIPTION SHIFT",
            "=" * 80,
            "",
            "1. SUBSCRIPTION EXTRACTION TREND",
            "-" * 80,
        ]
        
        sub_trend = self.subscription_extraction_trend()
        report_lines.append(f"{'Year':<10} {'Subscriptions %':<20} {'Ownership %':<20}")
        report_lines.append("-" * 50)
        for year, sub_pct, own_pct in sub_trend:
            report_lines.append(f"{year:<10} {sub_pct:>18.1f}% {own_pct:>18.1f}%")
        
        # Calculate change
        first_sub = sub_trend[0][1]
        last_sub = sub_trend[-1][1]
        delta_sub = last_sub - first_sub
        
        sub_direction = "increased" if delta_sub >= 0 else "decreased"

        report_lines.extend([
            "",
            f"FINDING: Subscription extraction {sub_direction} by {abs(delta_sub):.1f} percentage points",
            f"         from {first_sub:.1f}% ({sub_trend[0][0]}) to {last_sub:.1f}% ({sub_trend[-1][0]})",
            "",
            "2. WAGE vs HOUSING AFFORDABILITY",
            "-" * 80,
        ])
        
        wage_housing = self.wage_vs_housing_divergence()
        report_lines.append(f"{'Year':<10} {'Real Wage Index':<20} {'House Price Ratio':<20}")
        report_lines.append("-" * 50)
        for year, wage_idx, house_ratio in wage_housing:
            report_lines.append(f"{year:<10} {wage_idx:>18.1f} {house_ratio:>18.1f}x")
        
        report_lines.extend([
            "",
            f"FINDING: Real wages increased {wage_housing[-1][1] - wage_housing[0][1]:.1f} points",
            f"         while house prices went from {wage_housing[0][2]:.1f}x to {wage_housing[-1][2]:.1f}x income",
            f"         Housing became {((wage_housing[-1][2] / wage_housing[0][2]) - 1) * 100:.0f}% less affordable",
            "",
            "3. HOMEOWNERSHIP DECLINE",
            "-" * 80,
        ])
        
        ownership = self.ownership_rate_decline()
        report_lines.append(f"{'Year':<10} {'Homeownership Rate':<20}")
        report_lines.append("-" * 50)
        for year, rate in ownership:
            report_lines.append(f"{year:<10} {rate:>18.1f}%")
        
        # Peak was 2005
        peak_idx = max(range(len(ownership)), key=lambda i: ownership[i][1])
        peak_year, peak_rate = ownership[peak_idx]
        current_year, current_rate = ownership[-1]
        decline = peak_rate - current_rate
        
        report_lines.extend([
            "",
            f"FINDING: Homeownership peaked at {peak_rate:.1f}% in {peak_year}",
            f"         Declined to {current_rate:.1f}% by {current_year} (-{decline:.1f}pp)",
            "",
            "4. HOUSEHOLD DEBT & SAVINGS",
            "-" * 80,
        ])
        
        debt_data = self.debt_accumulation()
        report_lines.append(f"{'Year':<10} {'Debt/GDP %':<20} {'Savings Rate %':<20}")
        report_lines.append("-" * 50)
        for year, debt, savings in debt_data:
            report_lines.append(f"{year:<10} {debt:>18.1f}% {savings:>18.1f}%")
        
        report_lines.extend([
            "",
            "5. DISCRETIONARY INCOME SQUEEZE",
            "-" * 80,
        ])
        
        disc_data = self.discretionary_income_squeeze()
        report_lines.append(f"{'Year':<10} {'Discretionary £/wk':<20} {'As % Income':<20}")
        report_lines.append("-" * 50)
        for year, disc_amt, disc_pct in disc_data:
            report_lines.append(f"{year:<10} £{disc_amt:>17.2f} {disc_pct:>18.1f}%")
        
        peak_debt_row = max(debt_data, key=lambda row: row[1])
        peak_debt_year, peak_debt = peak_debt_row[0], peak_debt_row[1]

        report_lines.extend([
            "",
            "=" * 80,
            "CONCLUSION: RECURRING BURDEN SHIFT",
            "=" * 80,
            "",
            f"• Subscription payments went from {sub_trend[0][1]:.1f}% to {sub_trend[-1][1]:.1f}% of income ({delta_sub:+.1f}pp)",
            f"• Housing affordability worsened by {((wage_housing[-1][2] / wage_housing[0][2]) - 1) * 100:.0f}%",
            f"• Homeownership fell by {decline:.1f} percentage points from peak",
            f"• Household debt peaked at {peak_debt:.1f}% of GDP ({peak_debt_year})",
            "",
            "The model shows sustained pressure from recurring costs and housing",
            "affordability deterioration, with category composition shifting over time.",
            "",
            "=" * 80,
        ])
        
        return "\n".join(report_lines)
    
    def export_to_json(self, filepath: str):
        """Export all data to JSON for visualization"""
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "metadata": {
                "title": "UK Household Expenditure: Ownership to Subscription Shift",
                "analysis_date": "2026-02-13",
                "source": "ONS, IFS, Resolution Foundation, Bank of England",
            },
            "snapshots": []
        }
        
        for snapshot in self.snapshots:
            snap_data = {
                "year": snapshot.year,
                "metrics": {
                    "avg_weekly_income": snapshot.avg_weekly_income,
                    "avg_weekly_expenditure": snapshot.avg_weekly_expenditure,
                    "subscription_pct_of_income": snapshot.subscription_pct_of_income(),
                    "ownership_pct_of_income": snapshot.ownership_pct_of_income(),
                    "discretionary_income": snapshot.discretionary_income(),
                    "discretionary_pct": snapshot.discretionary_pct(),
                    "house_price_to_income": snapshot.house_price_to_income_ratio,
                    "homeownership_rate": snapshot.homeownership_rate,
                    "debt_to_gdp": snapshot.household_debt_to_gdp,
                    "savings_rate": snapshot.savings_rate,
                    "real_wage_index": snapshot.real_wage_index,
                },
                "categories": [
                    {
                        "name": cat.name,
                        "spending_type": cat.spending_type.value,
                        "weekly_amount": cat.weekly_amount,
                        "annual_amount": cat.annual_amount(),
                        "pct_of_income": cat.as_pct_of_income,
                        "description": cat.description,
                    }
                    for cat in snapshot.categories
                ]
            }
            data["snapshots"].append(snap_data)
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Data exported to {output_path}")


def generate_visualization_csv(analysis: HistoricalAnalysis, output_dir: str):
    """Generate CSV files for easy charting in spreadsheets"""
    import csv
    import os
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Subscription vs Ownership trend
    with open(f"{output_dir}/subscription_trend.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Year', 'Subscription %', 'Ownership %'])
        for year, sub, own in analysis.subscription_extraction_trend():
            writer.writerow([year, f"{sub:.2f}", f"{own:.2f}"])
    
    # 2. Wage vs Housing affordability
    with open(f"{output_dir}/wage_housing.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Year', 'Real Wage Index', 'House Price to Income Ratio'])
        for year, wage, ratio in analysis.wage_vs_housing_divergence():
            writer.writerow([year, f"{wage:.1f}", f"{ratio:.2f}"])
    
    # 3. Homeownership rate
    with open(f"{output_dir}/homeownership.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Year', 'Homeownership Rate %'])
        for year, rate in analysis.ownership_rate_decline():
            writer.writerow([year, f"{rate:.1f}"])
    
    # 4. Debt and savings
    with open(f"{output_dir}/debt_savings.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Year', 'Debt to GDP %', 'Savings Rate %'])
        for year, debt, savings in analysis.debt_accumulation():
            writer.writerow([year, f"{debt:.1f}", f"{savings:.1f}"])
    
    # 5. Discretionary income
    with open(f"{output_dir}/discretionary.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Year', 'Discretionary £/week', 'Discretionary %'])
        for year, amt, pct in analysis.discretionary_income_squeeze():
            writer.writerow([year, f"{amt:.2f}", f"{pct:.2f}"])
    
    print(f"CSV files generated in {output_dir}/")


def main():
    """Main execution: analyze data and generate outputs"""
    print("\n" + "=" * 80)
    print("HISTORICAL HOUSEHOLD EXPENDITURE ANALYSIS")
    print("Ownership → Subscription Extraction Model")
    print("=" * 80 + "\n")
    
    # Create analysis instance
    analysis = HistoricalAnalysis()
    
    # Generate and print summary report
    report = analysis.generate_summary_report()
    print(report)
    
    # Export data
    output_base = Path(__file__).resolve().parents[1] / "research" / "data"
    output_base.mkdir(parents=True, exist_ok=True)
    
    # JSON for programmatic use
    json_path = output_base / "historical_analysis.json"
    analysis.export_to_json(str(json_path))
    
    # CSVs for visualization
    csv_dir = output_base / "csv"
    generate_visualization_csv(analysis, str(csv_dir))
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\nOutputs generated:")
    print(f"  - Summary report (printed above)")
    print(f"  - JSON data: {json_path}")
    print(f"  - CSV files: {csv_dir}/")
    print(f"\nNext steps:")
    print(f"  1. Review historical-comparison.md for detailed findings")
    print(f"  2. Use CSV files to create charts in spreadsheet software")
    print(f"  3. Import JSON into visualization tools (D3.js, Python matplotlib, etc.)")
    print(f"  4. Calculate subscription burden by income decile (future work)")
    print()

    record_run(
        script_name=Path(__file__).name,
        input_files=["research/data/provenance/model_inputs/historical_inputs.json"],
        output_files=[
            "research/data/historical_analysis.json",
            "research/data/csv/subscription_trend.csv",
            "research/data/csv/wage_housing.csv",
            "research/data/csv/homeownership.csv",
            "research/data/csv/debt_savings.csv",
            "research/data/csv/discretionary.csv",
        ],
    )


if __name__ == "__main__":
    main()
