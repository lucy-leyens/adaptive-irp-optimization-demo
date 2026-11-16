# Adaptive Optimization Framework for Inventory Routing

A compact portfolio project demonstrating how **mathematical optimization**, **heuristic search**, **reward-based adaptive learning**, and **modular Python software design** can be combined for an Inventory Routing Problem (IRP).

> **Portfolio note.** This is an independent, simplified reimplementation inspired by Master's thesis research conducted at Fraunhofer IKS. It does not contain the original Fraunhofer source code and deliberately omits selected details of the full research framework.

## What this project demonstrates

The demo starts from a **precomputed feasible construction solution** and improves its route/visit structure using a reduced sequence-based selection hyper-heuristic (SSHH).

The recommended diagnostic experiment uses a synthetic clustered 12-customer / 4-period instance and provides three variants:

| Run | Heuristic selection | Quantity reoptimization | Purpose |
|---|---|---|---|
| `random_mcf` | random sequence selection | OR-Tools minimum-cost flow | controller baseline |
| `adaptive_mcf` | adaptive reward-based selection | OR-Tools minimum-cost flow | isolate the effect of adaptive search |
| `adaptive_lp` | adaptive reward-based selection | SCIP LP | compare quantity-reoptimization backends |

The adaptive runs use the profile stored in `configs/profiles/proposed.yaml`. The file name is only a configuration label; the controller itself is adaptive and reward-based.

This setup supports two clean comparisons:

- **Random vs. adaptive controller:** `random_mcf` vs. `adaptive_mcf`
- **SCIP LP vs. OR-Tools MCF:** `adaptive_lp` vs. `adaptive_mcf`

The optimization objective combines route cost and inventory holding cost. The main reported metric is the **best objective value**, together with runtime, number of iterations, feasible/infeasible candidates, accepted moves, and the objective trace over time.

## Architecture

```text
Config / CLI
    |
    v
Application API
    |
    v
Experiment Runner
    |
    +----> Controller -------------------+
    |       |                            |
    |       +-> Random profile           |
    |       +-> Adaptive profile         |
    |              |                     |
    |              +-> reward / scores --+
    |
    +----> Reduced heuristic portfolio
    |       +-> 2-opt
    |       +-> intra-route relocate
    |       +-> move visit period
    |       +-> remove visit
    |       +-> insert visit
    |
    +----> Quantity Evaluator
            +-> SCIP LP
            +-> OR-Tools MCF
```

See [`docs/architecture.md`](docs/architecture.md) for more detail.

## Quick start

### 1. Create an environment

```bash
python -m venv .venv
```

Activate it and install the project:

```bash
pip install -e .
```

The project uses:

- **PySCIPOpt / SCIP** for the fixed-route LP baseline,
- **Google OR-Tools** for the time-expanded minimum-cost-flow model,
- NumPy / pandas for experiment logic and reporting,
- matplotlib for lightweight result plots.

### 2. Run the recommended controller comparison

```bash
irp-demo compare --config configs/diagnostic_12x4.yaml --runs random_mcf adaptive_mcf --time-limit 30
```

This comparison uses the same instance, starting solution, minimum-cost-flow backend, and search budget. The main difference is the controller: random versus adaptive heuristic selection.

### 3. Compare quantity-reoptimization backends

```bash
irp-demo compare --config configs/diagnostic_12x4.yaml --runs adaptive_lp adaptive_mcf --time-limit 30
```

This keeps the adaptive search profile fixed while changing the quantity-reoptimization method.

### 4. Run a longer experiment

```bash
irp-demo compare --config configs/diagnostic_12x4.yaml --runs random_mcf adaptive_mcf --time-limit 1800
```

`1800` seconds corresponds to a 30-minute search budget **per configured run**.

### 5. Optional small smoke test

The repository also contains a smaller 6-customer / 3-period configuration for a very quick functionality check:

```bash
irp-demo compare --config configs/demo.yaml
```

## Configuration

The recommended comparison configuration is [`configs/diagnostic_12x4.yaml`](configs/diagnostic_12x4.yaml):

```yaml
instance: data/instances/diagnostic_12x4_clustered.json
initial_solution: data/initial_solutions/diagnostic_12x4_clustered.json
output_dir: results
seed: 7
time_limit_seconds: 30
max_iterations: 1000000

runs:
  - name: random_mcf
    profile: configs/profiles/random_matched.yaml
    quantity_solver: ortools_mcf

  - name: adaptive_mcf
    profile: configs/profiles/proposed.yaml
    quantity_solver: ortools_mcf

  - name: adaptive_lp
    profile: configs/profiles/proposed.yaml
    quantity_solver: scip_lp
```

The **search controller** and the **quantity solver** are independent configuration choices. This makes it possible to distinguish controller effects from solver effects.

## Random vs. adaptive profile

### Random profile

The random controller selects low-level heuristics without adapting its selection probabilities based on previous search outcomes.

For the diagnostic comparison, `random_matched.yaml` uses matched search settings so that the controller itself is the main experimental difference.

### Adaptive profile

The adaptive controller maintains:

- transition scores between low-level heuristics,
- stop/continue scores controlling sequence length,
- reward updates based on observed solution improvements.

Successful heuristic sequences therefore become more likely to be sampled again. This is intentionally described as **reward-based adaptive / reinforcement-learning-inspired selection**, rather than as a full reinforcement-learning implementation.

The adaptive configuration is stored in [`configs/profiles/proposed.yaml`](configs/profiles/proposed.yaml). The public demo uses a smaller operator portfolio than the full thesis implementation.

## LP vs. minimum-cost flow

For every fixed route structure, delivery quantities and inventory levels must be reoptimized.

`scip_lp` solves the corresponding continuous linear program directly with SCIP.

`ortools_mcf` builds a time-expanded network with supplier, route, customer pre-/post-demand, and terminal nodes, then solves the specialized minimum-cost-flow problem with OR-Tools.

This gives a clean experiment:

```text
same adaptive search + same candidate route structures
                    |
          +---------+---------+
          |                   |
       SCIP LP          OR-Tools MCF
```

The objective values of LP and MCF should agree for the same fixed route structure, while runtime may differ.

## Output

Each run writes:

```text
results/<run_name>_summary.json
results/<run_name>_trace.csv
```

The console prints a compact summary containing the initial and best objective values, improvement, iteration counts, candidate statistics, and runtime.

For example, after running `adaptive_mcf`, plot its objective trace with:

```bash
python -m irp_demo.visualization.plot_trace results/adaptive_mcf_trace.csv
```

The trace shows how the best objective value evolves during the search.

## Instances and starting solutions

The repository contains small **synthetic demonstration instances** and matching saved starting route structures. They are not proprietary benchmark or Fraunhofer project data.

The starting solution files represent the output of a construction phase. Keeping construction separate makes comparisons between search profiles reproducible: each method starts from exactly the same route structure.

The diagnostic 12-customer instance is intentionally clustered so that there are meaningful opportunities for route restructuring while the example remains small enough to inspect.

## Visualization

The public repository currently contains a lightweight **objective-trace plot** based on the generated CSV trace files.

Its purpose is to make the search process easy to inspect: a reviewer can see when improvements occur and how the best-known objective evolves over the available search time.

The original animation tooling developed in the Fraunhofer research context is **not included** here.

## Suggested reviewer path

If you only have a few minutes:

1. Read this README.
2. Look at [`src/irp_demo/controller/adaptive.py`](src/irp_demo/controller/adaptive.py).
3. Compare [`src/irp_demo/optimization/scip_lp.py`](src/irp_demo/optimization/scip_lp.py) with [`src/irp_demo/optimization/ortools_mcf.py`](src/irp_demo/optimization/ortools_mcf.py).
4. Run `irp-demo compare --config configs/diagnostic_12x4.yaml --runs random_mcf adaptive_mcf --time-limit 30`.
5. Inspect the generated objective traces and summary files.

## Scope

This repository is designed as a readable portfolio project, not as a reproduction package for the complete Master's thesis. It intentionally prioritizes clarity, architecture, and reproducible comparison over feature completeness.
