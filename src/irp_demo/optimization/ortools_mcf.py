from __future__ import annotations

from dataclasses import dataclass

from .base import QuantitySolver
from irp_demo.core.models import Instance, QuantityResult, RouteStructure


@dataclass
class ArcSpec:
    tail: str
    head: str
    lower: float
    upper: float
    cost: float
    quantity_key: tuple[int, int] | None = None
    inventory_key: tuple[int, int] | None = None
    supplier_period: int | None = None


class OrToolsMCFSolver(QuantitySolver):
    def __init__(self, quantity_scale: int = 100, cost_scale: int = 100):
        self.quantity_scale = quantity_scale
        self.cost_scale = cost_scale

    def solve(self, instance: Instance, structure: RouteStructure) -> QuantityResult:
        try:
            from ortools.graph.python import min_cost_flow
        except ImportError as exc:
            raise RuntimeError("Google OR-Tools is required for the MCF solver. Install the project dependencies.") from exc

        total_available = (
            instance.supplier_initial_inventory
            + sum(instance.production)
            + sum(c.initial_inventory for c in instance.customers)
        )
        total_demand = sum(sum(c.demand) for c in instance.customers)
        if total_available + 1e-9 < total_demand:
            return QuantityResult(feasible=False, status="insufficient_total_supply")

        balances: dict[str, float] = {}
        arcs: list[ArcSpec] = []

        def add_balance(node: str, value: float) -> None:
            balances[node] = balances.get(node, 0.0) + value

        for t in range(instance.periods):
            add_balance(f"s_{t}", instance.production[t] + (instance.supplier_initial_inventory if t == 0 else 0.0))

        for c in instance.customers:
            add_balance(f"c_{c.id}_pre_0", c.initial_inventory)
            for t in range(instance.periods):
                add_balance(f"c_{c.id}_post_{t}", -c.demand[t])

        add_balance("phi", -(total_available - total_demand))

        # Supplier inventory arcs.
        for t in range(instance.periods):
            head = f"s_{t + 1}" if t < instance.periods - 1 else "phi"
            arcs.append(ArcSpec(
                tail=f"s_{t}", head=head, lower=0.0, upper=total_available,
                cost=instance.supplier_holding_cost, supplier_period=t,
            ))

        # Route-capacity and delivery arcs.
        for t, routes in enumerate(structure):
            for r_idx, route in enumerate(routes):
                rnode = f"r_{t}_{r_idx}"
                arcs.append(ArcSpec(f"s_{t}", rnode, 0.0, instance.vehicle_capacity, 0.0))
                for i in route:
                    arcs.append(ArcSpec(
                        rnode, f"c_{i}_pre_{t}", 0.0, instance.vehicle_capacity, 0.0,
                        quantity_key=(i, t),
                    ))

        # Customer pre/post capacity and inventory arcs.
        for c in instance.customers:
            for t in range(instance.periods):
                arcs.append(ArcSpec(
                    f"c_{c.id}_pre_{t}", f"c_{c.id}_post_{t}",
                    0.0, c.max_inventory, 0.0,
                ))
                head = f"c_{c.id}_pre_{t + 1}" if t < instance.periods - 1 else "phi"
                arcs.append(ArcSpec(
                    f"c_{c.id}_post_{t}", head,
                    c.min_inventory, c.max_inventory, c.holding_cost,
                    inventory_key=(c.id, t),
                ))

        # Lower-bound transformation: out(y)-in(y)=b - out(lower)+in(lower).
        adjusted = dict(balances)
        constant_cost = 0.0
        for a in arcs:
            adjusted[a.tail] = adjusted.get(a.tail, 0.0) - a.lower
            adjusted[a.head] = adjusted.get(a.head, 0.0) + a.lower
            constant_cost += a.cost * a.lower

        nodes = sorted(set(adjusted) | {a.tail for a in arcs} | {a.head for a in arcs})
        node_id = {name: idx for idx, name in enumerate(nodes)}
        solver = min_cost_flow.SimpleMinCostFlow()

        arc_indices: list[int] = []
        for a in arcs:
            capacity = round((a.upper - a.lower) * self.quantity_scale)
            unit_cost = round(a.cost * self.cost_scale)
            idx = solver.add_arc_with_capacity_and_unit_cost(
                node_id[a.tail], node_id[a.head], capacity, unit_cost
            )
            arc_indices.append(idx)

        for node, value in adjusted.items():
            solver.set_node_supply(node_id[node], round(value * self.quantity_scale))

        status = solver.solve()
        if status != solver.OPTIMAL:
            return QuantityResult(feasible=False, status=f"ortools_status_{status}")

        quantities: dict[tuple[int, int], float] = {}
        inventories: dict[tuple[int, int], float] = {}
        supplier_inventory: dict[int, float] = {}

        for spec, idx in zip(arcs, arc_indices):
            flow = spec.lower + solver.flow(idx) / self.quantity_scale
            if spec.quantity_key is not None:
                quantities[spec.quantity_key] = flow
            if spec.inventory_key is not None:
                inventories[spec.inventory_key] = flow
            if spec.supplier_period is not None:
                supplier_inventory[spec.supplier_period] = flow

        transformed_cost = solver.optimal_cost() / (self.quantity_scale * self.cost_scale)
        return QuantityResult(
            feasible=True,
            holding_cost=transformed_cost + constant_cost,
            quantities=quantities,
            inventories=inventories,
            supplier_inventory=supplier_inventory,
            status="optimal",
        )
