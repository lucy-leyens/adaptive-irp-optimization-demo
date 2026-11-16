from __future__ import annotations

import numpy as np
from .base import Controller


class AdaptiveController(Controller):
    """Reward-based adaptive sequence generator.

    The first heuristic is sampled uniformly. Subsequent heuristics are sampled
    from transition scores. After each selected heuristic, stop/continue scores
    determine whether the sequence ends.
    """

    def __init__(
        self,
        n_heuristics: int,
        max_sequence_length: int,
        seed: int,
        initial_transition_score: float = 1.0,
        initial_stop_score: float = 1.0,
        initial_continue_score: float = 1.0,
        transition_learning_rate: float = 0.5,
        termination_learning_rate: float = 0.25,
    ):
        self.n = n_heuristics
        self.max_sequence_length = max_sequence_length
        self.rng = np.random.default_rng(seed)
        self.transition_scores = np.full((self.n, self.n), initial_transition_score, dtype=float)
        self.termination_scores = np.column_stack([
            np.full(self.n, initial_continue_score, dtype=float),
            np.full(self.n, initial_stop_score, dtype=float),
        ])
        self.transition_lr = transition_learning_rate
        self.termination_lr = termination_learning_rate
        self._last_decisions: list[tuple[int, int]] = []  # (heuristic, 0=continue / 1=stop)

    @staticmethod
    def _probabilities(scores: np.ndarray) -> np.ndarray:
        total = scores.sum()
        return scores / total if total > 0 else np.full_like(scores, 1.0 / len(scores))

    def generate_sequence(self) -> list[int]:
        first = int(self.rng.integers(self.n))
        sequence = [first]
        self._last_decisions = []

        while len(sequence) < self.max_sequence_length:
            current = sequence[-1]
            decision_probs = self._probabilities(self.termination_scores[current])
            decision = int(self.rng.choice([0, 1], p=decision_probs))
            self._last_decisions.append((current, decision))
            if decision == 1:
                break

            probs = self._probabilities(self.transition_scores[current])
            nxt = int(self.rng.choice(np.arange(self.n), p=probs))
            sequence.append(nxt)

        if len(sequence) == self.max_sequence_length:
            self._last_decisions.append((sequence[-1], 1))
        return sequence

    def update(self, sequence: list[int], reward: float) -> None:
        if reward <= 0:
            return
        for i, j in zip(sequence, sequence[1:]):
            self.transition_scores[i, j] += self.transition_lr * reward
        for heuristic_idx, decision in self._last_decisions:
            self.termination_scores[heuristic_idx, decision] += self.termination_lr * reward
