# Diagnostic clustered instance

`diagnostic_12x4_clustered` is a deliberately structured **diagnostic** instance, not a benchmark instance.

It contains 12 customers arranged in three spatial clusters and four planning periods. The saved initial solution deliberately mixes customers from different clusters across the three vehicle routes.

Inventory bounds are tight (`initial_inventory = 0`, `demand = 2`, `max_inventory = 3`), so each customer requires a visit in every period. This has two useful effects for controller testing:

1. removing a visit without restoring it generally makes the candidate quantity-infeasible;
2. a `remove_visit -> insert_visit` sequence can effectively relocate a customer between routes in the same period.

The second pattern gives the adaptive sequence controller a repeated transition that it can potentially learn and reinforce.

## Recommended controller ablation

Compare:

- `random_mcf`: random sequence selection + MCF;
- `adaptive_mcf`: adaptive sequence selection + MCF.

Both use the same quantity solver, maximum sequence length, threshold-acceptance rule, instance, and time limit. The intended difference is therefore the sequence-selection mechanism.

Do **not** present this instance as evidence that the adaptive method is universally superior. It is intended to make the learning mechanism observable. Final portfolio claims should be based on multiple seeds and preferably additional instances.
