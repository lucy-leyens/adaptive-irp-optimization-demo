from __future__ import annotations

from abc import ABC, abstractmethod


class Controller(ABC):
    @abstractmethod
    def generate_sequence(self) -> list[int]:
        raise NotImplementedError

    def update(self, sequence: list[int], reward: float) -> None:
        return None
