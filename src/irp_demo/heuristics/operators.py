from __future__ import annotations

import random

from .base import Heuristic
from irp_demo.core.models import Instance, RouteStructure


def _nonempty_routes(structure: RouteStructure):
    return [(t, r_idx, r) for t, routes in enumerate(structure) for r_idx, r in enumerate(routes) if r]


class TwoOpt(Heuristic):
    name = "two_opt"

    def apply(self, instance: Instance, structure: RouteStructure, rng: random.Random) -> bool:
        options = [(t, r_idx, r) for t, r_idx, r in _nonempty_routes(structure) if len(r) >= 3]
        if not options:
            return False
        _, _, route = rng.choice(options)
        i, j = sorted(rng.sample(range(len(route)), 2))
        if i == j:
            return False
        route[i:j + 1] = reversed(route[i:j + 1])
        return True


class IntraRouteRelocate(Heuristic):
    name = "intra_route_relocate"

    def apply(self, instance: Instance, structure: RouteStructure, rng: random.Random) -> bool:
        options = [(t, r_idx, r) for t, r_idx, r in _nonempty_routes(structure) if len(r) >= 2]
        if not options:
            return False
        _, _, route = rng.choice(options)
        i, j = rng.sample(range(len(route)), 2)
        node = route.pop(i)
        route.insert(j, node)
        return True


class MoveVisitPeriod(Heuristic):
    name = "move_visit_period"

    def apply(self, instance: Instance, structure: RouteStructure, rng: random.Random) -> bool:
        sources = _nonempty_routes(structure)
        if not sources or instance.periods < 2:
            return False
        source_t, source_r_idx, source_route = rng.choice(sources)
        customer = rng.choice(source_route)
        target_periods = [t for t in range(instance.periods) if t != source_t]
        rng.shuffle(target_periods)
        for target_t in target_periods:
            if any(customer in r for r in structure[target_t]):
                continue
            if structure[target_t]:
                target_route = rng.choice(structure[target_t])
                target_route.insert(rng.randrange(len(target_route) + 1), customer)
            elif instance.fleet_size > 0:
                structure[target_t].append([customer])
            else:
                continue
            source_route.remove(customer)
            if not source_route:
                structure[source_t].pop(source_r_idx)
            return True
        return False


class RemoveVisit(Heuristic):
    name = "remove_visit"

    def apply(self, instance: Instance, structure: RouteStructure, rng: random.Random) -> bool:
        sources = _nonempty_routes(structure)
        if not sources:
            return False
        t, r_idx, route = rng.choice(sources)
        route.pop(rng.randrange(len(route)))
        if not route:
            structure[t].pop(r_idx)
        return True


class InsertVisit(Heuristic):
    name = "insert_visit"

    def apply(self, instance: Instance, structure: RouteStructure, rng: random.Random) -> bool:
        options: list[tuple[int, int]] = []
        all_ids = set(instance.customer_ids)
        for t in range(instance.periods):
            visited = {i for route in structure[t] for i in route}
            for customer in all_ids - visited:
                options.append((t, customer))
        if not options:
            return False
        t, customer = rng.choice(options)
        if structure[t]:
            route = rng.choice(structure[t])
            route.insert(rng.randrange(len(route) + 1), customer)
            return True
        if len(structure[t]) < instance.fleet_size:
            structure[t].append([customer])
            return True
        return False


def default_portfolio() -> list[Heuristic]:
    return [TwoOpt(), IntraRouteRelocate(), MoveVisitPeriod(), RemoveVisit(), InsertVisit()]
