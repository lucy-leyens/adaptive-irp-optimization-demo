# Adaptive Optimization Framework for Inventory Routing

A compact portfolio project demonstrating how **mathematical optimization**, **heuristic search**, **reward-based adaptive learning**, and **modular Python software design** can be combined for an Inventory Routing Problem (IRP).

> **Portfolio note.** This is an independent, simplified reimplementation inspired by Master's thesis research conducted at Fraunhofer IKS. It does not contain the original Fraunhofer source code and deliberately omits selected details of the full research framework.

## What this project demonstrates

The demo starts from a **precomputed feasible construction solution** and improves its route/visit structure using a reduced sequence-based selection hyper-heuristic (SSHH).

Three experiment variants are provided:

| Run | Heuristic selection | Quantity reoptimization | Purpose |
|---|---|---|---|
| `baseline_lp` | random sequence selection | SCIP LP | transparent baseline |
| `proposed_lp` | adaptive reward-based selection | SCIP LP | isolate effect of adaptive search |
| `proposed_mcf` | adaptive reward-based selection | OR-Tools minimum-cost flow | adaptive search + specialized network solver |

The run names `proposed_lp` and `proposed_mcf` are simply configuration labels. Both use the **adaptive reward-based controller** described below.

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

### 2. Run the default comparison

```bash
irp-demo compare --config configs/demo.yaml
```

or equivalently:

```bash
python -m irp_demo.cli compare --config configs/demo.yaml
```

The default configuration is intentionally short so that a reviewer can run it quickly.

### 3. Run a longer experiment

```bash
irp-demo compare --config configs/demo.yaml --time-limit 1800
```

`1800` seconds corresponds to a 30-minute search budget **per configured run**.

### 4. Run selected variants only

```bash
irp-demo compare --config configs/demo.yaml --runs baseline_lp proposed_mcf --time-limit 60
```

## Configuration

The central experiment configuration is [`configs/demo.yaml`](configs/demo.yaml).

Example:

```yaml
instance: data/instances/small_6x3.json
initial_solution: data/initial_solutions/small_6x3.json
output_dir: results
seed: 7
time_limit_seconds: 60
max_iterations: 5000

runs:
  - name: baseline_lp
    profile: configs/profiles/random.yaml
    quantity_solver: scip_lp

  - name: proposed_lp
    profile: configs/profiles/proposed.yaml
    quantity_solver: scip_lp

  - name: proposed_mcf
    profile: configs/profiles/proposed.yaml
    quantity_solver: ortools_mcf
```

The **search profile** and the **quantity solver** are independent configuration choices. This makes it easy to distinguish algorithmic effects from solver effects.

## Random vs. adaptive profile

### Random profile

The baseline selects low-level heuristics uniformly at random and uses a simple non-worsening acceptance rule.

### Proposed adaptive profile

The adaptive controller maintains:

- transition scores between low-level heuristics,
- stop/continue scores controlling sequence length,
- reward updates based on observed solution improvements.

Successful heuristic sequences therefore become more likely to be sampled again. This is intentionally described as **reward-based adaptive / reinforcement-learning-inspired selection**, rather than as a full reinforcement-learning implementation.

The public demo uses a smaller operator portfolio than the full thesis implementation.

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

The console prints a compact summary containing:

```text
Run
Initial objective
Best objective
Improvement
Iterations
Feasible candidates
Infeasible candidates
Accepted candidates
Runtime
```

Plot a trace with:

```bash
python -m irp_demo.visualization.plot_trace results/proposed_mcf_trace.csv
```

The trace shows how the best objective value evolves during the search.

## Instances and starting solutions

The repository contains small **synthetic demonstration instances** and matching saved starting route structures. They are not proprietary benchmark or Fraunhofer project data.

The starting solution files represent the output of a construction phase. Keeping construction separate makes comparisons between search profiles reproducible: each method starts from exactly the same route structure.

## Visualization

The public repository currently contains a lightweight **objective-trace plot** based on the generated CSV trace files.

Its purpose is to make the search process easy to inspect: a reviewer can see when improvements occur and how the best-known objective evolves over the available search time.

The original animation tooling developed in the Fraunhofer research context is **not included** here.

## Suggested reviewer path

If you only have a few minutes:

1. Read this README.
2. Look at [`src/irp_demo/controller/adaptive.py`](src/irp_demo/controller/adaptive.py).
3. Compare [`src/irp_demo/optimization/scip_lp.py`](src/irp_demo/optimization/scip_lp.py) with [`src/irp_demo/optimization/ortools_mcf.py`](src/irp_demo/optimization/ortools_mcf.py).
4. Run `irp-demo compare --config configs/demo.yaml --time-limit 30`.
5. Inspect the generated objective traces and summaries.

## Scope

This repository is designed as a readable portfolio project, not as a reproduction package for the complete Master's thesis. It intentionally prioritizes clarity, architecture, and reproducible comparison over feature completeness.
