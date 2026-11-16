from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import yaml

from irp_demo.core.models import load_instance, load_route_structure
from irp_demo.experiments.runner import SearchRunner
from irp_demo.optimization.evaluator import Evaluator
from irp_demo.optimization.ortools_mcf import OrToolsMCFSolver
from irp_demo.optimization.scip_lp import ScipLPSolver
from irp_demo.reporting.io import print_summary, write_results


@dataclass
class CompareRequest:
    config_path: str
    selected_runs: list[str] | None = None
    time_limit_override: float | None = None


class OptimizationAPI:
    def compare(self, request: CompareRequest):
        config_path = Path(request.config_path)
        cfg = yaml.safe_load(config_path.read_text())

        instance = load_instance(cfg["instance"])
        initial = load_route_structure(cfg["initial_solution"])
        time_limit = request.time_limit_override or float(cfg["time_limit_seconds"])
        selected = set(request.selected_runs or [])
        summaries = []

        for run_cfg in cfg["runs"]:
            if selected and run_cfg["name"] not in selected:
                continue

            profile = yaml.safe_load(Path(run_cfg["profile"]).read_text())
            solver_name = run_cfg["quantity_solver"]
            if solver_name == "scip_lp":
                solver = ScipLPSolver()
            elif solver_name == "ortools_mcf":
                solver = OrToolsMCFSolver()
            else:
                raise ValueError(f"Unknown quantity solver: {solver_name}")

            runner = SearchRunner(
                instance=instance,
                evaluator=Evaluator(solver),
                profile=profile,
                seed=int(cfg["seed"]),
            )
            summary, trace, best_structure, _ = runner.run(
                name=run_cfg["name"],
                solver_name=solver_name,
                initial=initial,
                time_limit=time_limit,
                max_iterations=int(cfg["max_iterations"]),
            )
            write_results(cfg["output_dir"], summary, trace, best_structure)
            print_summary(summary)
            summaries.append(summary)

        return summaries
