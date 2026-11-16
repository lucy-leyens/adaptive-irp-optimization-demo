from __future__ import annotations

from irp_demo.core.models import Evaluation, Instance, RouteStructure
from irp_demo.core.objective import routing_cost, structurally_valid
from .base import QuantitySolver


class Evaluator:
    def __init__(self, quantity_solver: QuantitySolver):
        self.quantity_solver = quantity_solver

    def evaluate(self, instance: Instance, structure: RouteStructure) -> Evaluation:
        if not structurally_valid(instance, structure):
            return Evaluation(feasible=False)
        q = self.quantity_solver.solve(instance, structure)
        if not q.feasible:
            return Evaluation(feasible=False, quantity_result=q)
        r_cost = routing_cost(instance, structure)
        return Evaluation(
            feasible=True,
            total_cost=r_cost + q.holding_cost,
            routing_cost=r_cost,
            holding_cost=q.holding_cost,
            quantity_result=q,
        )
