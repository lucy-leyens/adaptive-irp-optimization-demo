from __future__ import annotations

from dataclasses import dataclass, field
from copy import deepcopy
from math import hypot
from typing import Any
import json
from pathlib import Path


@dataclass(frozen=True)
class Customer:
    id: int
    x: float
    y: float
    initial_inventory: float
    min_inventory: float
    max_inventory: float
    holding_cost: float
    demand: tuple[float, ...]


@dataclass(frozen=True)
class Instance:
    name: str
    periods: int
    fleet_size: int
    vehicle_capacity: float
    depot_x: float
    depot_y: float
    supplier_initial_inventory: float
    production: tuple[float, ...]
    supplier_holding_cost: float
    customers: tuple[Customer, ...]

    @property
    def customer_ids(self) -> tuple[int, ...]:
        return tuple(c.id for c in self.customers)

    def customer(self, customer_id: int) -> Customer:
        return next(c for c in self.customers if c.id == customer_id)

    def coordinates(self, node: int) -> tuple[float, float]:
        if node == 0:
            return self.depot_x, self.depot_y
        c = self.customer(node)
        return c.x, c.y

    def travel_cost(self, i: int, j: int) -> float:
        xi, yi = self.coordinates(i)
        xj, yj = self.coordinates(j)
        return hypot(xi - xj, yi - yj)


RouteStructure = list[list[list[int]]]


@dataclass
class QuantityResult:
    feasible: bool
    holding_cost: float = float("inf")
    quantities: dict[tuple[int, int], float] = field(default_factory=dict)
    inventories: dict[tuple[int, int], float] = field(default_factory=dict)
    supplier_inventory: dict[int, float] = field(default_factory=dict)
    status: str = "unknown"


@dataclass
class Evaluation:
    feasible: bool
    total_cost: float = float("inf")
    routing_cost: float = float("inf")
    holding_cost: float = float("inf")
    quantity_result: QuantityResult | None = None


def load_instance(path: str | Path) -> Instance:
    data: dict[str, Any] = json.loads(Path(path).read_text())
    customers = tuple(
        Customer(
            id=c["id"],
            x=c["x"],
            y=c["y"],
            initial_inventory=c["initial_inventory"],
            min_inventory=c["min_inventory"],
            max_inventory=c["max_inventory"],
            holding_cost=c["holding_cost"],
            demand=tuple(c["demand"]),
        )
        for c in data["customers"]
    )
    return Instance(
        name=data["name"],
        periods=data["periods"],
        fleet_size=data["fleet_size"],
        vehicle_capacity=data["vehicle_capacity"],
        depot_x=data["depot"]["x"],
        depot_y=data["depot"]["y"],
        supplier_initial_inventory=data["supplier_initial_inventory"],
        production=tuple(data["production"]),
        supplier_holding_cost=data["supplier_holding_cost"],
        customers=customers,
    )


def load_route_structure(path: str | Path) -> RouteStructure:
    data = json.loads(Path(path).read_text())
    return [[list(route) for route in period] for period in data["routes"]]


def copy_structure(structure: RouteStructure) -> RouteStructure:
    return deepcopy(structure)
