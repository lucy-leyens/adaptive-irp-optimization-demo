from __future__ import annotations

from .base import QuantitySolver
from irp_demo.core.models import Instance, QuantityResult, RouteStructure


class ScipLPSolver(QuantitySolver):
    def solve(self, instance: Instance, structure: RouteStructure) -> QuantityResult:
        try:
            from pyscipopt import Model, quicksum
        except ImportError as exc:
            raise RuntimeError("PySCIPOpt is required for the SCIP LP solver. Install the project dependencies.") from exc

        model = Model("fixed_route_quantity_lp")
        model.hideOutput()

        visits = {
            (i, t): any(i in route for route in structure[t])
            for i in instance.customer_ids
            for t in range(instance.periods)
        }

        q = {
            (i, t): model.addVar(lb=0.0, name=f"q_{i}_{t}")
            for i in instance.customer_ids
            for t in range(instance.periods)
            if visits[i, t]
        }
        inv = {
            (i, t): model.addVar(lb=instance.customer(i).min_inventory,
                                 ub=instance.customer(i).max_inventory,
                                 name=f"I_{i}_{t}")
            for i in instance.customer_ids
            for t in range(instance.periods)
        }
        supplier = {
            t: model.addVar(lb=0.0, name=f"I0_{t}")
            for t in range(instance.periods)
        }

        for i in instance.customer_ids:
            c = instance.customer(i)
            for t in range(instance.periods):
                q_it = q.get((i, t), 0.0)
                prev = c.initial_inventory if t == 0 else inv[i, t - 1]
                model.addCons(inv[i, t] == prev + q_it - c.demand[t])

                # At t=0 without a visit, both ``prev`` and ``q_it`` are plain
                # Python numbers. In that case ``prev + q_it <= max_inventory``
                # would be evaluated by Python to True/False before SCIP sees it.
                # The condition is constant, so validate it directly instead of
                # passing a boolean to model.addCons().
                if t == 0 and (i, t) not in q:
                    if c.initial_inventory > c.max_inventory + 1e-9:
                        return QuantityResult(feasible=False, status="initial_inventory_above_capacity")
                else:
                    model.addCons(prev + q_it <= c.max_inventory)

        for t in range(instance.periods):
            prev = instance.supplier_initial_inventory if t == 0 else supplier[t - 1]
            delivered = quicksum(q.get((i, t), 0.0) for i in instance.customer_ids)
            model.addCons(supplier[t] == prev + instance.production[t] - delivered)

            for route in structure[t]:
                model.addCons(quicksum(q.get((i, t), 0.0) for i in route) <= instance.vehicle_capacity)

        objective = quicksum(
            instance.customer(i).holding_cost * inv[i, t]
            for i in instance.customer_ids
            for t in range(instance.periods)
        ) + quicksum(
            instance.supplier_holding_cost * supplier[t]
            for t in range(instance.periods)
        )
        model.setObjective(objective, "minimize")
        model.optimize()

        status = str(model.getStatus())
        if status not in {"optimal", "bestsollimit", "timelimit"} or model.getNSols() == 0:
            return QuantityResult(feasible=False, status=status)

        quantities = {(i, t): model.getVal(var) for (i, t), var in q.items()}
        inventories = {(i, t): model.getVal(var) for (i, t), var in inv.items()}
        supplier_inventory = {t: model.getVal(var) for t, var in supplier.items()}
        return QuantityResult(
            feasible=True,
            holding_cost=float(model.getObjVal()),
            quantities=quantities,
            inventories=inventories,
            supplier_inventory=supplier_inventory,
            status=status,
        )
