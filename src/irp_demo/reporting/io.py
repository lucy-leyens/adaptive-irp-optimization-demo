from __future__ import annotations

import json
from pathlib import Path
import pandas as pd


def write_results(output_dir: str | Path, summary, trace: list[dict], best_structure) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{summary.name}_summary.json").write_text(
        json.dumps({**summary.to_dict(), "best_route_structure": best_structure}, indent=2)
    )
    pd.DataFrame(trace).to_csv(out / f"{summary.name}_trace.csv", index=False)


def print_summary(summary) -> None:
    print(f"\nRun: {summary.name}")
    print(f"Profile:              {summary.profile}")
    print(f"Quantity solver:      {summary.solver}")
    print(f"Initial objective:    {summary.initial_objective:.3f}")
    print(f"Best objective:       {summary.best_objective:.3f}")
    print(f"Improvement:          {summary.improvement_percent:.2f} %")
    print(f"Iterations:           {summary.iterations}")
    print(f"Feasible candidates:  {summary.feasible_candidates}")
    print(f"Infeasible candidates:{summary.infeasible_candidates}")
    print(f"Accepted candidates:  {summary.accepted_candidates}")
    print(f"Runtime:              {summary.runtime_seconds:.2f} s")
