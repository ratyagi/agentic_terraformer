# Runs code-based environmental simulations
# Goal: Numerically simulate impact of each scenario.
new_emissions = baseline_emissions - sum(action_effects)
cost = sum(action_costs)
jobs_impact = compute_jobs_impact(...)
