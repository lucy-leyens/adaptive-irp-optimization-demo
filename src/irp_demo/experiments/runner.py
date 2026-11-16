from __future__ import annotations

from dataclasses import dataclass, asdict
import random
import time
from typing import Any

from irp_demo.controller.adaptive import AdaptiveController
from irp_demo.controller.random_controller import RandomController
from irp_demo.core.models import Evaluation, Instance, RouteStructure, copy_structure
from irp_demo.heuristics.operators import default_portfolio
from irp_demo.optimization.evaluator import Evaluator


@dataclass
class RunSummary:
    name: str
    profile: str
    solver: str
    initial_objective: float
    best_objective: float
    improvement_percent: float
    iterations: int
    feasible_candidates: int
    infeasible_candidates: int
    accepted_candidates: int
    runtime_seconds: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SearchRunner:
    def __init__(self, instance: Instance, evaluator: Evaluator, profile: dict, seed: int):
        self.instance = instance
        self.evaluator = evaluator
        self.profile = profile
        self.seed = seed
        self.rng = random.Random(seed)
        self.heuristics = default_portfolio()

        if profile["controller"] == "adaptive":
            self.controller = AdaptiveController(
                n_heuristics=len(self.heuristics),
                max_sequence_length=profile["max_sequence_length"],
                seed=seed,
                initial_transition_score=profile.get("initial_transition_score", 1.0),
                initial_stop_score=profile.get("initial_stop_score", 1.0),
                initial_continue_score=profile.get("initial_continue_score", 1.0),
                transition_learning_rate=profile.get("transition_learning_rate", 0.5),
                termination_learning_rate=profile.get("termination_learning_rate", 0.25),
            )
        else:
            self.controller = RandomController(
                n_heuristics=len(self.heuristics),
                max_sequence_length=profile["max_sequence_length"],
                seed=seed,
            )

    def _reward(self, candidate: Evaluation, current: Evaluation, best: Evaluation) -> float:
        if not candidate.feasible:
            return 0.0
        reward_cfg = self.profile.get("reward", {})
        if candidate.total_cost < best.total_cost - 1e-9:
            return float(reward_cfg.get("global_best", 3.0))
        if candidate.total_cost < current.total_cost - 1e-9:
            return float(reward_cfg.get("current_improvement", 1.0))
        return 0.0

    def _accept(self, candidate: Evaluation, current: Evaluation, best: Evaluation, elapsed_fraction: float) -> bool:
        if not candidate.feasible:
            return False
        cfg = self.profile.get("acceptance", {"type": "non_worsening"})
        if cfg["type"] == "non_worsening":
            return candidate.total_cost <= current.total_cost + 1e-9
        if cfg["type"] == "best_relative_threshold":
            start = float(cfg.get("threshold_start", 0.01))
            end = float(cfg.get("threshold_end", 0.0001))
            threshold = start + (end - start) * min(max(elapsed_fraction, 0.0), 1.0)
            return (
                candidate.total_cost <= current.total_cost + 1e-9
                or candidate.total_cost <= best.total_cost * (1.0 + threshold)
            )
        raise ValueError(f"Unknown acceptance type: {cfg['type']}")

    def run(self, name: str, solver_name: str, initial: RouteStructure, time_limit: float, max_iterations: int):
        current_structure = copy_structure(initial)
        current_eval = self.evaluator.evaluate(self.instance, current_structure)
        if not current_eval.feasible:
            raise RuntimeError("Saved construction solution is not quantity-feasible for the selected solver.")
        best_structure = copy_structure(current_structure)
        best_eval = current_eval
        initial_objective = current_eval.total_cost

        start = time.perf_counter()
        trace = [{"seconds": 0.0, "iteration": 0, "best_objective": best_eval.total_cost}]
        feasible = infeasible = accepted = 0
        iteration = 0

        while iteration < max_iterations:
            elapsed = time.perf_counter() - start
            if elapsed >= time_limit:
                break
            iteration += 1
            candidate_structure = copy_structure(current_structure)
            sequence = self.controller.generate_sequence()
            for h_idx in sequence:
                self.heuristics[h_idx].apply(self.instance, candidate_structure, self.rng)

            candidate_eval = self.evaluator.evaluate(self.instance, candidate_structure)
            if candidate_eval.feasible:
                feasible += 1
            else:
                infeasible += 1

            reward = self._reward(candidate_eval, current_eval, best_eval)
            self.controller.update(sequence, reward)

            elapsed_fraction = min((time.perf_counter() - start) / max(time_limit, 1e-9), 1.0)
            if self._accept(candidate_eval, current_eval, best_eval, elapsed_fraction):
                current_structure = candidate_structure
                current_eval = candidate_eval
                accepted += 1

            if candidate_eval.feasible and candidate_eval.total_cost < best_eval.total_cost - 1e-9:
                best_structure = copy_structure(candidate_structure)
                best_eval = candidate_eval
                trace.append({
                    "seconds": time.perf_counter() - start,
                    "iteration": iteration,
                    "best_objective": best_eval.total_cost,
                })

        runtime = time.perf_counter() - start
        improvement = 100.0 * (initial_objective - best_eval.total_cost) / initial_objective
        summary = RunSummary(
            name=name,
            profile=self.profile.get("name", self.profile["controller"]),
            solver=solver_name,
            initial_objective=initial_objective,
            best_objective=best_eval.total_cost,
            improvement_percent=improvement,
            iterations=iteration,
            feasible_candidates=feasible,
            infeasible_candidates=infeasible,
            accepted_candidates=accepted,
            runtime_seconds=runtime,
        )
        return summary, trace, best_structure, best_eval
