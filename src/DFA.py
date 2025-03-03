from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar, Dict, Tuple, Set, FrozenSet

STATE = TypeVar('STATE')

@dataclass
class DFA[STATE]:
    S: set[str]
    K: set[STATE]
    q0: STATE
    d: dict[tuple[STATE, str], STATE]
    F: set[STATE]

    def accept(self, word: str) -> bool:
        # Simulate the DFA on the given word
        current_state = self.q0
        for char in word:
            if char in self.S:
                current_state = self.d.get((current_state, char))
            else:
                return False
        return current_state in self.F

    def remap_states[OTHER_STATE](self, f: Callable[[STATE], 'OTHER_STATE']) -> 'DFA[OTHER_STATE]':
        # Optional, for remapping states
        pass

    def reversed_delta(self, symbol: str, Q: set[STATE]) -> set[STATE]:
        # Compute reverse delta (delta^-1) for a symbol and a set of states
        X = set()
        for (state, char), target in self.d.items():
            if char == symbol and target in Q:
                X.add(state)
        return X

    def split_partition(self, P: list[set[STATE]], W: list[set[STATE]], X: set[STATE]) -> None:
        # Split partitions based on reverse delta
        for R in list(P):  # Copy P to safely modify while iterating
            R1 = R.intersection(X)
            R2 = R - R1
            if R1 and R2:  # If R can be split
                P.remove(R)
                P.append(R1)
                P.append(R2)
                if R in W:
                    W.remove(R)
                    W.append(R1)
                    W.append(R2)
                else:
                    W.append(R1 if len(R1) <= len(R2) else R2)

    def map_groups_to_states(self, P: list[set[STATE]], state_map: Dict[FrozenSet[STATE], STATE]) -> Tuple[STATE, Set[STATE]]:
        # Map each group in P to a representative state
        new_F = set()
        new_q0 = None

        for group in P:
            if not group:  # Skip empty groups
                continue
            group = frozenset(group)
            repr_state = next(iter(group))  # Choose a representative state
            state_map[group] = repr_state
            if self.q0 in group:
                new_q0 = repr_state
            if group & self.F:
                new_F.add(repr_state)

        return new_q0, new_F

    def build_new_transitions(self, P: list[set[STATE]], state_map: Dict[FrozenSet[STATE], STATE]) -> Dict[Tuple[STATE, str], STATE]:
        # Build the new transition function
        new_d = {}

        for (state, symbol), target in self.d.items():
            new_state, new_target = None, None
            for group in P:
                if state in group:
                    new_state = state_map.get(frozenset(group))
                if target in group:
                    new_target = state_map.get(frozenset(group))
            if new_state is not None and new_target is not None:
                new_d[(new_state, symbol)] = new_target

        return new_d

    def minimize(self) -> 'DFA[STATE]':
        # Minimize the DFA using partition refinement
        W = [self.F, self.K - self.F]  # Partitions that wait their turn to be split
        P = [self.F, self.K - self.F]  # Current partitioning

        while W:
            Q = W.pop()
            for symbol in self.S:
                X = self.reversed_delta(symbol, Q)
                self.split_partition(P, W, X)

        state_map = {}
        new_q0, new_F = self.map_groups_to_states(P, state_map)
        new_d = self.build_new_transitions(P, state_map)

        return DFA(
            S=self.S,
            K=set(state_map.values()),
            q0=new_q0,
            d=new_d,
            F=new_F
        )
