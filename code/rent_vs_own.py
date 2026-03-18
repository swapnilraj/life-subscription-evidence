#!/usr/bin/env python3
"""
UK Rent vs Ownership Wealth Divergence Model
==============================================

Models 30-year comparison of renter vs buyer starting at age 25 in 2024.
Calculates cumulative wealth divergence year by year.

Provenance summary (from `research/data/provenance/model_inputs/rent_vs_own_inputs.json`):
- Derived from primary sources: `property_price_2024`, `monthly_rent_2024`, `rent_inflation`,
  `mortgage_rate`, `house_price_growth`, `savings_return`, `property_tax_monthly`
- Explicit assumptions: `mortgage_term_years`, `maintenance_percent`, `insurance_monthly`,
  `renters_insurance_monthly`
- Full register: `research/data/provenance/ASSUMPTION_REGISTER.md`

Author: Research Agent
Date: 2026-02-13
"""

import json
import csv
from pathlib import Path
from provenance import load_model_inputs, record_run


class RentVsOwnModel:
    """
    Models wealth accumulation for renter vs homeowner over 30 years.
    """
    
    def __init__(self):
        config = load_model_inputs("rent_vs_own_inputs")
        params = config["parameters"]

        # === INITIAL CONDITIONS (2024) ===
        self.start_year = params["start_year"]
        self.start_age = params["start_age"]
        self.years = params["years"]
        
        # === PROPERTY PURCHASE PARAMETERS ===
        self.property_price_2024 = params["property_price_2024"]
        self.deposit_percent = params["deposit_percent"]
        self.deposit = self.property_price_2024 * self.deposit_percent  # £58,000
        self.mortgage_amount = self.property_price_2024 - self.deposit  # £232,000
        self.mortgage_rate = params["mortgage_rate"]
        self.mortgage_term_years = params["mortgage_term_years"]
        
        # === RENT PARAMETERS ===
        self.monthly_rent_2024 = params["monthly_rent_2024"]
        self.rent_inflation = params["rent_inflation"]
        
        # === HOUSE PRICE GROWTH ===
        self.house_price_growth = params["house_price_growth"]
        
        # === ADDITIONAL COSTS ===
        # Homeowner
        self.maintenance_percent = params["maintenance_percent"]
        self.property_tax_monthly = params["property_tax_monthly"]
        self.insurance_monthly = params["insurance_monthly"]
        
        # Renter
        self.renters_insurance_monthly = params["renters_insurance_monthly"]
        
        # === OPPORTUNITY COST ===
        self.savings_return = params["savings_return"]
        
    def calculate_monthly_mortgage_payment(self):
        """Calculate fixed monthly mortgage payment using standard formula."""
        P = self.mortgage_amount
        r = self.mortgage_rate / 12  # Monthly interest rate
        n = self.mortgage_term_years * 12  # Total number of payments
        
        # M = P * [r(1+r)^n] / [(1+r)^n - 1]
        if r == 0:
            return P / n
        
        monthly_payment = P * (r * (1 + r)**n) / ((1 + r)**n - 1)
        return monthly_payment
    
    def calculate_mortgage_balance(self, months_paid, monthly_payment):
        """Calculate remaining mortgage balance after n months."""
        P = self.mortgage_amount
        r = self.mortgage_rate / 12
        n = self.mortgage_term_years * 12
        
        if r == 0:
            return P - (monthly_payment * months_paid)
        
        # Remaining balance formula
        balance = P * ((1 + r)**n - (1 + r)**months_paid) / ((1 + r)**n - 1)
        return max(0, balance)
    
    def run_simulation(self):
        """Run 30-year simulation comparing renter vs buyer."""
        
        # Calculate mortgage payment
        monthly_mortgage = self.calculate_monthly_mortgage_payment()
        
        # Storage for annual data
        results = []
        columns = ['year', 'age', 'years_elapsed', 'buyer_property_value', 'buyer_mortgage_balance',
                  'buyer_equity', 'buyer_cash', 'buyer_net_worth', 'buyer_total_paid', 
                  'buyer_annual_cost', 'renter_cash', 'renter_net_worth', 'renter_total_paid',
                  'renter_annual_cost', 'monthly_rent', 'wealth_gap', 'wealth_gap_percent']
        
        # === BUYER: Initial position ===
        buyer_cash = 0  # Spent £58k on deposit
        buyer_property_value = self.property_price_2024
        buyer_mortgage_balance = self.mortgage_amount
        buyer_equity = buyer_property_value - buyer_mortgage_balance
        buyer_net_worth = buyer_equity + buyer_cash
        
        # === RENTER: Initial position ===
        renter_cash = self.deposit  # Still has £58k that wasn't spent on deposit
        renter_net_worth = renter_cash
        
        # Current monthly rent
        current_monthly_rent = self.monthly_rent_2024
        
        # Track cumulative payments
        buyer_total_paid = self.deposit
        renter_total_paid = 0
        
        # === YEAR-BY-YEAR SIMULATION ===
        for year in range(self.years + 1):  # 0 to 30
            current_year = self.start_year + year
            current_age = self.start_age + year
            months_elapsed = year * 12
            
            # === BUYER CALCULATIONS ===
            if year > 0:  # After year 0
                # Mortgage payments over the year
                annual_mortgage_payments = monthly_mortgage * 12
                
                # Additional costs
                annual_maintenance = buyer_property_value * self.maintenance_percent
                annual_property_tax = self.property_tax_monthly * 12
                annual_insurance = self.insurance_monthly * 12
                
                buyer_annual_cost = (annual_mortgage_payments + annual_maintenance + 
                                   annual_property_tax + annual_insurance)
                buyer_total_paid += buyer_annual_cost
                
                # House price appreciation
                buyer_property_value *= (1 + self.house_price_growth)
                
                # Mortgage balance
                buyer_mortgage_balance = self.calculate_mortgage_balance(
                    months_elapsed, monthly_mortgage
                )
            else:
                # Year 0: just the deposit
                buyer_annual_cost = self.deposit
                
            # Calculate buyer equity and net worth
            buyer_equity = buyer_property_value - buyer_mortgage_balance
            buyer_net_worth = buyer_equity + buyer_cash
            
            # === RENTER CALCULATIONS ===
            if year > 0:
                monthly_rent_for_year = current_monthly_rent

                # Rent for the year (increases annually)
                annual_rent = monthly_rent_for_year * 12
                annual_renters_insurance = self.renters_insurance_monthly * 12
                
                renter_annual_cost = annual_rent + annual_renters_insurance
                renter_total_paid += renter_annual_cost
                
                # Money that would have been spent on mortgage/costs vs rent
                # Renter pays rent, buyer pays mortgage+costs
                # Difference goes to savings
                monthly_cost_difference = (monthly_mortgage + self.property_tax_monthly + 
                                          self.insurance_monthly + 
                                          (buyer_property_value * self.maintenance_percent / 12) - 
                                          monthly_rent_for_year - self.renters_insurance_monthly)
                
                annual_savings_difference = monthly_cost_difference * 12
                
                # monthly_cost_difference = buyer_monthly_cost - renter_monthly_cost
                # Positive => renter spends less than buyer, so renter can invest the difference.
                # Negative => renter spends more than buyer, so renter must draw down savings.
                renter_cash += annual_savings_difference
                
                # Apply investment return on accumulated cash
                renter_cash *= (1 + self.savings_return)
                
                # Inflate rent for next year
                current_monthly_rent *= (1 + self.rent_inflation)
            else:
                monthly_rent_for_year = current_monthly_rent
            
            renter_net_worth = renter_cash
            
            # === WEALTH GAP ===
            wealth_gap = buyer_net_worth - renter_net_worth
            wealth_gap_percent = (wealth_gap / renter_net_worth * 100) if renter_net_worth > 0 else 0
            
            # === STORE RESULTS ===
            results.append({
                'year': current_year,
                'age': current_age,
                'years_elapsed': year,
                
                # Buyer metrics
                'buyer_property_value': round(buyer_property_value, 2),
                'buyer_mortgage_balance': round(buyer_mortgage_balance, 2),
                'buyer_equity': round(buyer_equity, 2),
                'buyer_cash': round(buyer_cash, 2),
                'buyer_net_worth': round(buyer_net_worth, 2),
                'buyer_total_paid': round(buyer_total_paid, 2),
                'buyer_annual_cost': round(buyer_annual_cost, 2) if year > 0 else round(self.deposit, 2),
                
                # Renter metrics
                'renter_cash': round(renter_cash, 2),
                'renter_net_worth': round(renter_net_worth, 2),
                'renter_total_paid': round(renter_total_paid, 2),
                'renter_annual_cost': round(renter_annual_cost, 2) if year > 0 else 0,
                'monthly_rent': round(monthly_rent_for_year, 2),
                
                # Comparison
                'wealth_gap': round(wealth_gap, 2),
                'wealth_gap_percent': round(wealth_gap_percent, 2),
            })
        
        return results, columns
    
    def generate_summary(self, results):
        """Generate summary statistics from simulation."""
        final = results[-1]
        total_years = self.years
        
        summary = {
            'simulation_period': f"{self.start_year} - {self.start_year + total_years}",
            'age_range': f"{self.start_age} - {self.start_age + total_years}",
            
            'initial_conditions': {
                'property_price': f"£{self.property_price_2024:,.0f}",
                'deposit_required': f"£{self.deposit:,.0f} ({self.deposit_percent*100:.0f}%)",
                'monthly_mortgage_payment': f"£{self.calculate_monthly_mortgage_payment():,.2f}",
                'initial_monthly_rent': f"£{self.monthly_rent_2024:,.0f}",
                'mortgage_rate': f"{self.mortgage_rate*100:.1f}%",
                'mortgage_term': f"{self.mortgage_term_years} years",
            },
            
            'derived_inputs': {
                'market_rent_inflation': f"{self.rent_inflation*100:.1f}% annually",
                'house_price_growth': f"{self.house_price_growth*100:.1f}% annually",
                'savings_return': f"{self.savings_return*100:.1f}% annually",
            },

            'assumptions': {
                'maintenance_cost': f"{self.maintenance_percent*100:.1f}% of property value",
            },
            
            'final_positions': {
                'buyer': {
                    'age': int(final['age']),
                    'property_value': f"£{final['buyer_property_value']:,.2f}",
                    'mortgage_remaining': f"£{final['buyer_mortgage_balance']:,.2f}",
                    'equity': f"£{final['buyer_equity']:,.2f}",
                    'net_worth': f"£{final['buyer_net_worth']:,.2f}",
                    'total_paid': f"£{final['buyer_total_paid']:,.2f}",
                },
                'renter': {
                    'age': int(final['age']),
                    'cash_savings': f"£{final['renter_cash']:,.2f}",
                    'net_worth': f"£{final['renter_net_worth']:,.2f}",
                    'total_paid': f"£{final['renter_total_paid']:,.2f}",
                    'final_monthly_rent': f"£{final['monthly_rent']:,.2f}",
                }
            },
            
            'wealth_divergence': {
                'absolute_gap': f"£{final['wealth_gap']:,.2f}",
                'ratio': f"{final['buyer_net_worth'] / final['renter_net_worth']:.1f}:1" if final['renter_net_worth'] > 0 else "N/A",
                'buyer_advantage': f"£{final['wealth_gap']:,.2f}",
            },
            
            'key_findings': {
                'renter_dead_money': f"£{final['renter_total_paid']:,.2f}",
                'buyer_equity_built': f"£{final['buyer_equity']:,.2f}",
                'property_appreciation': f"£{final['buyer_property_value'] - self.property_price_2024:,.2f}",
                'rent_escalation': f"{((final['monthly_rent'] / self.monthly_rent_2024) - 1) * 100:.1f}% increase over 30 years",
            }
        }
        
        return summary


def main():
    """Run the simulation and save results."""
    
    print("=" * 80)
    print("UK RENT VS OWNERSHIP WEALTH DIVERGENCE MODEL")
    print("=" * 80)
    print()
    
    # Initialize model
    model = RentVsOwnModel()
    
    print("Running 30-year simulation...")
    print()
    
    # Run simulation
    results, columns = model.run_simulation()
    
    # Generate summary
    summary = model.generate_summary(results)
    
    # Print summary
    print("SIMULATION SUMMARY")
    print("-" * 80)
    print(f"Period: {summary['simulation_period']}")
    print(f"Age Range: {summary['age_range']}")
    print()
    
    print("INITIAL CONDITIONS:")
    for key, value in summary['initial_conditions'].items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    print()
    
    print("DERIVED INPUTS:")
    for key, value in summary['derived_inputs'].items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    print()

    print("ASSUMPTIONS:")
    for key, value in summary['assumptions'].items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    print()
    
    print("FINAL POSITIONS (Age 55):")
    print()
    print("BUYER:")
    for key, value in summary['final_positions']['buyer'].items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    print()
    print("RENTER:")
    for key, value in summary['final_positions']['renter'].items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    print()
    
    print("WEALTH DIVERGENCE:")
    for key, value in summary['wealth_divergence'].items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    print()
    
    print("KEY FINDINGS:")
    for key, value in summary['key_findings'].items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    print()
    
    # Save outputs
    output_dir = Path(__file__).parent.parent / 'research' / 'data'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save CSV
    csv_path = output_dir / 'rent_vs_own_simulation.csv'
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(results)
    print(f"✓ Saved detailed year-by-year data: {csv_path}")
    
    # Save JSON summary
    json_path = output_dir / 'rent_vs_own_summary.json'
    with open(json_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✓ Saved summary: {json_path}")
    
    # Print key milestones
    print()
    print("KEY MILESTONES:")
    print("-" * 80)
    milestones = [0, 5, 10, 15, 20, 25, 30]
    for year in milestones:
        row = next(r for r in results if r['years_elapsed'] == year)
        print(f"Year {year} (Age {int(row['age'])}):")
        print(f"  Buyer Net Worth: £{row['buyer_net_worth']:,.0f}")
        print(f"  Renter Net Worth: £{row['renter_net_worth']:,.0f}")
        print(f"  Wealth Gap: £{row['wealth_gap']:,.0f}")
        print()
    
    print("=" * 80)
    print("THE LIFE SUBSCRIPTION: Quantified")
    print("=" * 80)
    print()
    print(f"After 30 years of equivalent housing consumption:")
    print(f"  • Buyer builds {summary['final_positions']['buyer']['equity']} in equity")
    print(f"  • Renter pays {summary['key_findings']['renter_dead_money']} in 'dead money'")
    print(f"  • Wealth gap: {summary['wealth_divergence']['ratio']}")
    print()
    print("This is not a housing market. This is a wealth extraction machine.")
    print()

    record_run(
        script_name=Path(__file__).name,
        input_files=["research/data/provenance/model_inputs/rent_vs_own_inputs.json"],
        output_files=[
            "research/data/rent_vs_own_simulation.csv",
            "research/data/rent_vs_own_summary.json",
        ],
    )


if __name__ == '__main__':
    main()
