from __future__ import annotations

from .models import Instance, RouteStructure


def route_cost(instance: Instance, route: list[int]) -> float:
    if not route:
        return 0.0
    nodes = [0, *route, 0]
    return sum(instance.travel_cost(i, j) for i, j in zip(nodes, nodes[1:]))


def routing_cost(instance: Instance, structure: RouteStructure) -> float:
    return sum(route_cost(instance, route) for period in structure for route in period)


def structurally_valid(instance: Instance, structure: RouteStructure) -> bool:
    if len(structure) != instance.periods:
        return False
    valid_customers = set(instance.customer_ids)
    for period_routes in structure:
        if len(period_routes) > instance.fleet_size:
            return False
        seen: set[int] = set()
        for route in period_routes:
            if not route:
                return False
            if len(route) != len(set(route)):
                return False
            if any(i not in valid_customers for i in route):
                return False
            for i in route:
                if i in seen:
                    return False
                seen.add(i)
    return True
