from __future__ import annotations

import random
from .base import Controller


class RandomController(Controller):
    def __init__(self, n_heuristics: int, max_sequence_length: int, seed: int):
        self.n_heuristics = n_heuristics
        self.max_sequence_length = max_sequence_length
        self.rng = random.Random(seed)

    def generate_sequence(self) -> list[int]:
        length = self.rng.randint(1, self.max_sequence_length)
        return [self.rng.randrange(self.n_heuristics) for _ in range(length)]
