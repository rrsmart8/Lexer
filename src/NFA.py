from .DFA import DFA

from dataclasses import dataclass
from collections.abc import Callable
from typing import FrozenSet, Set, Dict, Tuple

EPSILON = ''

@dataclass
class NFA[STATE]:
    S: set[str]
    K: set[STATE]
    q0: STATE
    d: dict[tuple[STATE, str], set[STATE]]
    F: set[STATE]

    def epsilon_closure(self, state: STATE) -> set[STATE]:
        
        closure = {state}
        stack = [state]
        
        while stack:
            current = stack.pop()
            if (current, EPSILON) in self.d:
                for next_state in self.d[(current, EPSILON)]:
                    if next_state not in closure:
                        closure.add(next_state)
                        stack.append(next_state)
        
        return closure
    
    def is_final_state(self, dfa_state: FrozenSet[STATE], dfa_final_states: Set[FrozenSet[STATE]]) -> bool:
        is_final = any(state in self.F for state in dfa_state)
        if is_final:
            dfa_final_states.add(dfa_state)
        return is_final


    def subset_construction(self) -> DFA[FrozenSet[STATE]]:
        # Define the alphabet excluding epsilon
        alphabet = self.S - {EPSILON}

        # Initial state of DFA is the epsilon closure of the NFA's initial state
        initial_closure = self.epsilon_closure(self.q0)
        dfa_initial_state = frozenset(initial_closure)

        # Initialize DFA components
        dfa_states: Set[FrozenSet[STATE]] = {dfa_initial_state}
        dfa_transitions: Dict[Tuple[FrozenSet[STATE], str], FrozenSet[STATE]] = {}
        dfa_final_states: Set[FrozenSet[STATE]] = set()

        # Mark initial state as final if it contains any NFA final states
        self.is_final_state(dfa_initial_state, dfa_final_states)

        # stack for unprocessed DFA states
        stack = [dfa_initial_state]

        while stack:
            current_dfa_state = stack.pop()

            for symbol in alphabet:
                # Compute the set of NFA states reachable from current_dfa_state via 'symbol'
                next_states = set()
                for nfa_state in current_dfa_state:
                    if (nfa_state, symbol) in self.d:
                        next_states.update(self.d[(nfa_state, symbol)])

                # Compute the epsilon closure of the reachable states
                combined_closure = set()
                for state in next_states:
                    combined_closure.update(self.epsilon_closure(state))

                # Convert to frozenset for immutability and as DFA state
                next_dfa_state = frozenset(combined_closure)

                # Add the transition to the DFA
                dfa_transitions[(current_dfa_state, symbol)] = next_dfa_state

                # If the new DFA state is not already processed, add it to the stack
                if next_dfa_state not in dfa_states:
                    dfa_states.add(next_dfa_state)
                    stack.append(next_dfa_state)

                    # Check and update final states
                    self.is_final_state(next_dfa_state, dfa_final_states)

        # Create and return the DFA
        return DFA(
            S=alphabet,
            K=dfa_states,
            q0=dfa_initial_state,
            d=dfa_transitions,
            F=dfa_final_states
        )

        
    
    def remap_states[OTHER_STATE](self, f: 'Callable[[STATE], OTHER_STATE]') -> 'NFA[OTHER_STATE]':
        # optional, but may be useful for the second stage of the project. Works similarly to 'remap_states'
        # from the DFA class. See the comments there for more details.
        pass
