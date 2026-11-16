from __future__ import annotations

from abc import ABC, abstractmethod
import random

from irp_demo.core.models import Instance, RouteStructure


class Heuristic(ABC):
    name: str

    @abstractmethod
    def apply(self, instance: Instance, structure: RouteStructure, rng: random.Random) -> bool:
        """Modify structure in place. Return True if a move was applied."""
        raise NotImplementedError
