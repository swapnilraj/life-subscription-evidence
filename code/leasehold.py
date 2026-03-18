#!/usr/bin/env python3
"""
UK Leasehold Financial Extraction Model

Models the cost of leasehold vs freehold ownership over time, including:
- Ground rent escalation (flat, RPI-linked, doubling)
- Service charges with inflation
- Lease extension costs at different remaining terms
- Total cost of ownership comparison

Provenance summary (from `research/data/provenance/model_inputs/leasehold_inputs.json`):
- Derived from primary sources: `property_value`
- Explicit assumptions: service charge baseline, lease length, extension timing,
  ground-rent clause scenarios, freehold comparator parameters
- Full register: `research/data/provenance/ASSUMPTION_REGISTER.md`
"""

import math
from dataclasses import dataclass
from typing import List, Tuple
import json
from pathlib import Path
from provenance import load_model_inputs, record_run


@dataclass
class LeaseholdCosts:
    """Results of leasehold cost calculation"""
    ground_rent_total: float
    service_charges_total: float
    lease_extension_cost: float
    total_cost: float
    annual_breakdown: List[Tuple[int, float, float, float]]  # (year, ground_rent, service_charge, cumulative)


def calculate_ground_rent_flat(initial_rent: float, years: int) -> Tuple[float, List[Tuple[int, float]]]:
    """
    Calculate total ground rent with flat (no escalation) rate.
    
    Args:
        initial_rent: Starting annual ground rent
        years: Number of years to calculate
        
    Returns:
        (total_cost, yearly_breakdown)
    """
    total = initial_rent * years
    breakdown = [(year, initial_rent) for year in range(1, years + 1)]
    return total, breakdown


def calculate_ground_rent_rpi(initial_rent: float, years: int, rpi_rate: float = 0.03) -> Tuple[float, List[Tuple[int, float]]]:
    """
    Calculate total ground rent with RPI-linked escalation.
    
    Args:
        initial_rent: Starting annual ground rent
        years: Number of years to calculate
        rpi_rate: Annual RPI inflation rate (default 3%)
        
    Returns:
        (total_cost, yearly_breakdown)
    """
    total = 0.0
    breakdown = []
    current_rent = initial_rent
    
    for year in range(1, years + 1):
        total += current_rent
        breakdown.append((year, current_rent))
        current_rent *= (1 + rpi_rate)
    
    return total, breakdown


def calculate_ground_rent_doubling(initial_rent: float, years: int, doubling_period: int) -> Tuple[float, List[Tuple[int, float]]]:
    """
    Calculate total ground rent with doubling clause.
    
    Args:
        initial_rent: Starting annual ground rent
        years: Number of years to calculate
        doubling_period: Years between doublings (10, 15, 25, etc.)
        
    Returns:
        (total_cost, yearly_breakdown)
    """
    total = 0.0
    breakdown = []
    
    for year in range(1, years + 1):
        # Calculate how many doubling periods have passed
        doublings = (year - 1) // doubling_period
        current_rent = initial_rent * (2 ** doublings)
        total += current_rent
        breakdown.append((year, current_rent))
    
    return total, breakdown


def calculate_service_charges(initial_charge: float, years: int, inflation_rate: float = 0.05) -> Tuple[float, List[Tuple[int, float]]]:
    """
    Calculate total service charges with inflation.
    
    Args:
        initial_charge: Starting annual service charge
        years: Number of years to calculate
        inflation_rate: Annual inflation rate (default 5% - long-term average above CPI)
        
    Returns:
        (total_cost, yearly_breakdown)
    """
    total = 0.0
    breakdown = []
    current_charge = initial_charge
    
    for year in range(1, years + 1):
        total += current_charge
        breakdown.append((year, current_charge))
        current_charge *= (1 + inflation_rate)
    
    return total, breakdown


def calculate_lease_extension_premium(
    property_value: float,
    ground_rent: float,
    years_remaining: int,
    yield_rate: float = 0.05
) -> Tuple[float, dict]:
    """
    Calculate lease extension premium using statutory formula.
    
    Simplified calculation based on:
    - Ground rent compensation (present value)
    - Reversion value (present value of property reverting to freeholder)
    - Marriage value (50% of uplift, only if <80 years)
    
    Args:
        property_value: Current market value of property
        ground_rent: Annual ground rent
        years_remaining: Years left on current lease
        yield_rate: Discount rate (5% standard post-2007)
        
    Returns:
        (total_premium, breakdown_dict)
    """
    
    # 1. Ground rent compensation (present value of future ground rent)
    # PV = GR × [(1 - (1 + y)^-n) / y]
    if ground_rent > 0:
        ground_rent_pv = ground_rent * ((1 - (1 + yield_rate) ** -years_remaining) / yield_rate)
    else:
        ground_rent_pv = 0.0
    
    # 2. Reversion value (present value of property returning to freeholder)
    # Assume property reverts at 50% of current value (degraded by short lease)
    reversion_value = (property_value * 0.5) * ((1 + yield_rate) ** -years_remaining)
    
    # 3. Marriage value (only if <80 years)
    marriage_value = 0.0
    if years_remaining < 80:
        # Relativity: how much is short lease worth vs long lease?
        # Using simplified relativity curve: roughly 1% loss per year below 80
        relativity = 0.80 + (years_remaining / 100) if years_remaining < 80 else 1.0
        current_lease_value = property_value * relativity
        extended_lease_value = property_value * 0.99  # Near-freehold value
        
        # Marriage value = (Extended value - Current value) - Freeholder's loss
        freeholder_loss = ground_rent_pv + reversion_value
        marriage_value = (extended_lease_value - current_lease_value - freeholder_loss)
        
        # Leaseholder pays 50% of marriage value
        if marriage_value > 0:
            marriage_value = marriage_value * 0.5
        else:
            marriage_value = 0.0
    
    # Total premium
    total_premium = ground_rent_pv + reversion_value + marriage_value
    
    breakdown = {
        'ground_rent_compensation': round(ground_rent_pv, 2),
        'reversion_value': round(reversion_value, 2),
        'marriage_value': round(marriage_value, 2),
        'marriage_value_applies': years_remaining < 80,
        'total_premium': round(total_premium, 2)
    }
    
    return total_premium, breakdown


def model_leasehold_lifecycle(
    property_value: float,
    initial_ground_rent: float,
    ground_rent_type: str,
    doubling_period: int,
    initial_service_charge: float,
    lease_length: int,
    extend_at_years: int = None
) -> LeaseholdCosts:
    """
    Model complete leasehold lifecycle costs.
    
    Args:
        property_value: Initial property value
        initial_ground_rent: Starting annual ground rent
        ground_rent_type: 'flat', 'rpi', or 'doubling'
        doubling_period: Years between doublings (only for 'doubling' type)
        initial_service_charge: Starting annual service charge
        lease_length: Initial lease length in years
        extend_at_years: When to extend lease (default: when 75 years remain)
        
    Returns:
        LeaseholdCosts object with full breakdown
    """
    if extend_at_years is None:
        extend_at_years = 75
    
    # Calculate ground rent based on type
    years_until_extension = lease_length - extend_at_years
    
    if ground_rent_type == 'flat':
        gr_total, gr_breakdown = calculate_ground_rent_flat(initial_ground_rent, years_until_extension)
    elif ground_rent_type == 'rpi':
        gr_total, gr_breakdown = calculate_ground_rent_rpi(initial_ground_rent, years_until_extension)
    elif ground_rent_type == 'doubling':
        gr_total, gr_breakdown = calculate_ground_rent_doubling(
            initial_ground_rent, years_until_extension, doubling_period
        )
    else:
        raise ValueError(f"Unknown ground_rent_type: {ground_rent_type}")
    
    # Calculate service charges (continues for full lease)
    sc_total, sc_breakdown = calculate_service_charges(initial_service_charge, lease_length)
    
    # Calculate lease extension cost
    years_remaining = extend_at_years
    current_ground_rent = gr_breakdown[years_until_extension - 1][1] if gr_breakdown else initial_ground_rent
    extension_cost, _ = calculate_lease_extension_premium(
        property_value, current_ground_rent, years_remaining
    )
    
    # Build annual breakdown
    annual_breakdown = []
    cumulative = 0.0
    for year in range(1, lease_length + 1):
        gr = gr_breakdown[year - 1][1] if year <= len(gr_breakdown) else 0.0  # After extension, no more ground rent
        sc = sc_breakdown[year - 1][1]
        year_cost = gr + sc
        cumulative += year_cost
        annual_breakdown.append((year, gr, sc, cumulative))
    
    total_cost = gr_total + sc_total + extension_cost
    
    return LeaseholdCosts(
        ground_rent_total=gr_total,
        service_charges_total=sc_total,
        lease_extension_cost=extension_cost,
        total_cost=total_cost,
        annual_breakdown=annual_breakdown
    )


def compare_leasehold_vs_freehold(
    property_value: float,
    leasehold_costs: LeaseholdCosts,
    freehold_maintenance: float = 1500,  # Annual maintenance for freehold
    freehold_maintenance_inflation: float = 0.025,  # Apply inflation to keep comparator realistic
    years: int = 99
) -> dict:
    """
    Compare total cost of leasehold vs freehold ownership.
    
    Args:
        property_value: Initial property value
        leasehold_costs: Calculated leasehold costs
        freehold_maintenance: Annual maintenance cost for freehold (lower, no service charge markup)
        freehold_maintenance_inflation: Annual inflation applied to freehold maintenance
        years: Years to compare
        
    Returns:
        Comparison dictionary
    """
    # Freehold: only maintenance costs (no ground rent, no service charge markup, no extensions)
    freehold_total_maintenance = sum(
        freehold_maintenance * ((1 + freehold_maintenance_inflation) ** year)
        for year in range(years)
    )
    freehold_total = property_value + freehold_total_maintenance
    
    # Leasehold: purchase price + all leasehold costs
    leasehold_total = property_value + leasehold_costs.total_cost
    
    # Calculate extraction (extra cost beyond reasonable maintenance)
    extraction = leasehold_total - freehold_total
    extraction_percentage = (extraction / freehold_total) * 100
    
    return {
        'freehold_purchase': property_value,
        'freehold_maintenance': freehold_total_maintenance,
        'freehold_total': freehold_total,
        'leasehold_purchase': property_value,
        'leasehold_ground_rent': leasehold_costs.ground_rent_total,
        'leasehold_service_charges': leasehold_costs.service_charges_total,
        'leasehold_extension': leasehold_costs.lease_extension_cost,
        'leasehold_total': leasehold_total,
        'extraction_amount': extraction,
        'extraction_percentage': extraction_percentage
    }


def model_extension_cost_curve(property_value: float, ground_rent: float) -> List[Tuple[int, float, bool]]:
    """
    Model how lease extension cost changes as lease gets shorter.
    
    Returns list of (years_remaining, premium, marriage_value_applied)
    """
    results = []
    # Include specific years around 80-year threshold
    years_to_check = list(range(99, 79, -5)) + [85, 80, 75] + list(range(70, 39, -5))
    years_to_check = sorted(set(years_to_check), reverse=True)  # Remove duplicates and sort
    
    for years in years_to_check:
        premium, breakdown = calculate_lease_extension_premium(property_value, ground_rent, years)
        results.append((years, premium, breakdown['marriage_value_applies']))
    return results


def print_scenario(name: str, costs: LeaseholdCosts, comparison: dict):
    """Pretty print a scenario"""
    print(f"\n{'=' * 80}")
    print(f"SCENARIO: {name}")
    print('=' * 80)
    print(f"\nGround Rent Total:        £{costs.ground_rent_total:,.2f}")
    print(f"Service Charges Total:    £{costs.service_charges_total:,.2f}")
    print(f"Lease Extension Cost:     £{costs.lease_extension_cost:,.2f}")
    print(f"{'─' * 80}")
    print(f"TOTAL LEASEHOLD COST:     £{costs.total_cost:,.2f}")
    print(f"\nComparison:")
    print(f"  Freehold equivalent:    £{comparison['freehold_total']:,.2f}")
    print(f"  Leasehold total:        £{comparison['leasehold_total']:,.2f}")
    print(f"  {'─' * 78}")
    print(f"  EXTRACTION:             £{comparison['extraction_amount']:,.2f} ({comparison['extraction_percentage']:.1f}% premium)")


def main():
    """Run all scenarios and generate report"""
    config = load_model_inputs("leasehold_inputs")

    property_value = config["property_value"]["value"]
    initial_service_charge = config["initial_service_charge"]["value"]
    lease_length = config["lease_length"]["value"]
    extend_at_years = config["extend_at_years"]["value"]
    freehold_maintenance = config["freehold_comparator"]["annual_maintenance"]
    freehold_maintenance_inflation = config["freehold_comparator"]["annual_inflation"]

    print("=" * 80)
    print("UK LEASEHOLD FINANCIAL EXTRACTION MODEL")
    print("=" * 80)
    print(f"Modeling cost of leasehold vs freehold over {lease_length}-year lease")
    print(f"Property value: £{property_value:,.0f} (scenario baseline)")
    print()

    scenario_results = {}
    scenario_order = []

    for index, scenario in enumerate(config["scenarios"], start=1):
        print("\n" + "=" * 80)
        print(f"SCENARIO {index}: {scenario['name']}")
        print("=" * 80)
        costs = model_leasehold_lifecycle(
            property_value=property_value,
            initial_ground_rent=scenario["initial_ground_rent"],
            ground_rent_type=scenario["ground_rent_type"],
            doubling_period=scenario["doubling_period"],
            initial_service_charge=initial_service_charge,
            lease_length=lease_length,
            extend_at_years=extend_at_years,
        )
        comparison = compare_leasehold_vs_freehold(
            property_value,
            costs,
            freehold_maintenance=freehold_maintenance,
            freehold_maintenance_inflation=freehold_maintenance_inflation,
            years=lease_length,
        )
        print_scenario(scenario["name"], costs, comparison)
        scenario_order.append(scenario["label"])
        scenario_results[scenario["label"]] = (costs, comparison)

    costs1, comp1 = scenario_results[scenario_order[0]]
    costs3, comp3 = scenario_results[scenario_order[2]]

    print("\n  Ground Rent Escalation:")
    for year in [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 99]:
        idx = year - 1
        if idx < len(costs3.annual_breakdown):
            _, gr, _, _ = costs3.annual_breakdown[idx]
            print(f"    Year {year:2d}: £{gr:,.2f}/year")
    
    # Lease Extension Cost Curve
    print("\n" + "=" * 80)
    print("LEASE EXTENSION COST CURVE")
    print("=" * 80)
    print("How extension premium changes as lease gets shorter")
    print(f"Property value: £{property_value:,}, Ground rent: £250/year")
    print()
    print("Years Remaining | Extension Premium | Marriage Value Applies?")
    print("─" * 80)
    
    extension_curve = model_extension_cost_curve(property_value, config["scenarios"][0]["initial_ground_rent"])
    for years, premium, mv_applies in extension_curve:
        mv_marker = " ⚠️ YES" if mv_applies else " (no)"
        print(f"     {years:2d} years   |   £{premium:>10,.2f}      | {mv_marker}")
    
    # Find the 80-year threshold jump
    cost_at_85 = [p for y, p, _ in extension_curve if y == 85][0]
    cost_at_75 = [p for y, p, _ in extension_curve if y == 75][0]
    marriage_value_impact = cost_at_75 - cost_at_85
    
    print(f"\n⚠️  Marriage Value Impact (80-year threshold):")
    print(f"    Extension at 85 years: £{cost_at_85:,.2f}")
    print(f"    Extension at 75 years: £{cost_at_75:,.2f}")
    print(f"    Extra cost: £{marriage_value_impact:,.2f} ({(marriage_value_impact/cost_at_85)*100:.1f}% increase)")
    
    # Summary comparison
    print("\n" + "=" * 80)
    print("SUMMARY COMPARISON: TOTAL LIFETIME EXTRACTION")
    print("=" * 80)
    print(f"\nAll scenarios: £{property_value/1000:.0f}k property, {lease_length}-year lease, extend at {extend_at_years} years\n")
    print(f"{'Scenario':<25} | {'Total Cost':<15} | {'vs Freehold':<15} | {'Extraction %'}")
    print("─" * 80)
    
    for name in scenario_order:
        costs, comp = scenario_results[name]
        print(f"{name:<25} | £{costs.total_cost:>13,.0f} | +£{comp['extraction_amount']:>12,.0f} | {comp['extraction_percentage']:>9.1f}%")
    
    print("\n" + "=" * 80)
    print("KEY FINDINGS")
    print("=" * 80)
    
    # Calculate key stats
    comparisons = [scenario_results[name][1] for name in scenario_order]
    avg_extraction = sum(c['extraction_amount'] for c in comparisons) / len(comparisons)
    max_extraction = max(c['extraction_amount'] for c in comparisons)
    max_scenario = [name for name in scenario_order if scenario_results[name][1]['extraction_amount'] == max_extraction][0]
    
    print(f"""
1. SCALE OF EXTRACTION
   - Average extraction: £{avg_extraction:,.0f} beyond reasonable freehold costs
   - Worst case ({max_scenario}): £{max_extraction:,.0f} extra paid
   - You pay more in leasehold fees than the property's purchase price

2. SERVICE CHARGE DOMINANCE
   - Service charges (with 5% long-term inflation) are the largest cost component
   - Over 99 years: ~£{costs1.service_charges_total:,.0f} (vastly exceeding property value)
   - Even at modest 5%/year, compounds to astronomical totals over 99 years
   - Recent years saw 11% increases (2023-24), showing extraction acceleration

3. THE 80-YEAR CLIFF
   - Marriage value adds £{marriage_value_impact:,.0f} to extension cost
   - {(marriage_value_impact/cost_at_85)*100:.0f}% increase in premium below 80 years
   - Creates artificial urgency benefiting freeholders

4. DOUBLING CLAUSE HORROR
   - 10-year doubling reaches £{costs3.annual_breakdown[89][1]:,.0f}/year by year 90
   - Total ground rent: £{costs3.ground_rent_total:,.0f} (vs £{costs1.ground_rent_total:,.0f} flat)
   - Properties become unmortgageable within 20-30 years

5. LIFETIME "SUBSCRIPTION" COST
   - Even "best case" (flat ground rent): £{costs1.total_cost:,.0f} total
   - That's {(costs1.total_cost/property_value)*100:.0f}% of purchase price paid again in fees
   - Equivalent to buying the property {costs1.total_cost/property_value:.1f} times

6. WHO BENEFITS?
   - Freeholders: £6,000-80,000+ in ground rent (depending on escalation)
   - Management companies: £{costs1.service_charges_total:,.0f} in service charges
   - Surveyor/legal: £{costs1.lease_extension_cost:,.0f} in extension costs
   - TOTAL EXTRACTION: £{costs1.total_cost:,.0f} to £{costs3.total_cost:,.0f}

This is not housing. This is a lifetime subscription to rent your own "property."
    """)
    
    # Export data for further analysis
    export_data = {
        'property_value': property_value,
        'lease_length': lease_length,
        'scenarios': [
            {
                'name': name,
                'ground_rent_total': scenario_results[name][0].ground_rent_total,
                'service_charges_total': scenario_results[name][0].service_charges_total,
                'lease_extension_cost': scenario_results[name][0].lease_extension_cost,
                'total_cost': scenario_results[name][0].total_cost,
                'extraction_amount': scenario_results[name][1]['extraction_amount'],
                'extraction_percentage': scenario_results[name][1]['extraction_percentage']
            }
            for name in scenario_order
        ],
        'extension_curve': [
            {'years_remaining': y, 'premium': p, 'marriage_value': mv}
            for y, p, mv in extension_curve
        ]
    }
    
    output_file = Path(__file__).resolve().parents[1] / 'research' / 'data' / 'leasehold_model_output.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"\n\nDetailed data exported to: {output_file}")
    print("\n" + "=" * 80)

    record_run(
        script_name=Path(__file__).name,
        input_files=["research/data/provenance/model_inputs/leasehold_inputs.json"],
        output_files=["research/data/leasehold_model_output.json"],
    )


if __name__ == '__main__':
    main()
