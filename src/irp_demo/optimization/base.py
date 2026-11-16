from __future__ import annotations

from abc import ABC, abstractmethod
from irp_demo.core.models import Instance, QuantityResult, RouteStructure


class QuantitySolver(ABC):
    @abstractmethod
    def solve(self, instance: Instance, structure: RouteStructure) -> QuantityResult:
        raise NotImplementedError
