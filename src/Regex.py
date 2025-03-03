from typing import Set
from dataclasses import dataclass
from itertools import count
from .NFA import NFA

STATE_GEN = count()
def new_state():
    return next(STATE_GEN)

EPSILON = ''

@dataclass
class Regex:
    def thompson(self) -> NFA[int]:
        raise NotImplementedError

@dataclass
class Literal(Regex):
    char: str
    def thompson(self) -> NFA[int]:
        start = new_state()
        end = new_state()
        transitions = {(start, self.char): {end}}
        return NFA(
            S={self.char},
            K={start, end},
            q0=start,
            d=transitions,
            F={end}
        )

@dataclass
class Epsilon(Regex):
    def thompson(self) -> NFA[int]:
        start = new_state()
        return NFA(
            S=set(),
            K={start},
            q0=start,
            d={},
            F={start}
        )


@dataclass
class Concatenation(Regex):
    left: Regex
    right: Regex

    def thompson(self) -> NFA[int]:
        # Generate NFAs for the sub-expressions
        left_nfa = self.left.thompson()
        right_nfa = self.right.thompson()

        # Combine the state transitions from both NFAs
        combined_transitions = left_nfa.d.copy()
        for key, destinations in right_nfa.d.items():
            if key in combined_transitions:
                combined_transitions[key].update(destinations)
            else:
                combined_transitions[key] = destinations.copy()

        # Link the final states of the left NFA to the initial state of the right NFA with epsilon transitions
        for final_state in left_nfa.F:
            epsilon_key = (final_state, EPSILON)
            if epsilon_key not in combined_transitions:
                combined_transitions[epsilon_key] = set()
            combined_transitions[epsilon_key].add(right_nfa.q0)

        # Define the combined state set and alphabet
        all_states = left_nfa.S.union(right_nfa.S)
        all_symbols = left_nfa.K.union(right_nfa.K)

        # Construct the concatenated NFA
        concatenated_nfa = NFA(
            S=all_states,
            K=all_symbols,
            q0=left_nfa.q0,
            d=combined_transitions,
            F=right_nfa.F
        )

        return concatenated_nfa

@dataclass
class Alternation(Regex):
    left: Regex
    right: Regex

    def thompson(self) -> NFA[int]:
        fresh_init = new_state()
        fresh_final = new_state()

        nfa_left = self.left.thompson()
        nfa_right = self.right.thompson()

        # Merge transitions
        delta = dict(nfa_left.d)
        delta.update(nfa_right.d)

        # Epsilon transitions from fresh_init to both sub-NFAs' starts
        delta[(fresh_init, EPSILON)] = {nfa_left.q0, nfa_right.q0}

        # Link left sub-NFA final states to fresh_final
        for end_state in nfa_left.F:
            delta.setdefault((end_state, EPSILON), set()).add(fresh_final)

        # Link right sub-NFA final states to fresh_final
        for end_state in nfa_right.F:
            delta.setdefault((end_state, EPSILON), set()).add(fresh_final)

        # Construct the combined NFA
        return NFA(
            S=nfa_left.S.union(nfa_right.S),
            K=nfa_left.K.union(nfa_right.K, {fresh_init, fresh_final}),
            q0=fresh_init,
            d=delta,
            F={fresh_final}
        )

@dataclass
class KleeneStar(Regex):
    expr: Regex

    def thompson(self) -> NFA[int]:
        initial = new_state()
        final = new_state()

        sub_nfa = self.expr.thompson()

        delta = dict(sub_nfa.d)
        delta[(initial, EPSILON)] = {sub_nfa.q0, final}
        for s in sub_nfa.F:
            delta.setdefault((s, EPSILON), set()).update({sub_nfa.q0, final})

        return NFA(
            S=sub_nfa.S,
            K=sub_nfa.K.union({initial, final}),
            q0=initial,
            d=delta,
            F={final}
        )
        
@dataclass
class Plus(Regex):
    expr: Regex

    def thompson(self) -> NFA[int]:
        sub_expr_nfa = self.expr.thompson()
        init = new_state()
        done = new_state()

        edge_map = dict(sub_expr_nfa.d)
        edge_map[(init, EPSILON)] = {sub_expr_nfa.q0}

        for st in sub_expr_nfa.F:
            edge_map.setdefault((st, EPSILON), set()).update({done, sub_expr_nfa.q0})

        return NFA(
            S=sub_expr_nfa.S,
            K=sub_expr_nfa.K.union({init, done}),
            q0=init,
            d=edge_map,
            F={done}
        )
@dataclass
class Question(Regex):
    expr: Regex
    def thompson(self) -> NFA[int]:
        # expr? = expr|epsilon
        return Alternation(self.expr, Epsilon()).thompson()

@dataclass
class CharacterClass(Regex):
    chars: Set[str]
    def thompson(self) -> NFA[int]:
        start = new_state()
        end = new_state()
        transitions = {}
        for c in self.chars:
            transitions.setdefault((start, c), set()).add(end)
        return NFA(
            S=self.chars,
            K={start, end},
            q0=start,
            d=transitions,
            F={end}
        )


# A small tokenizer for the regex
def tokenize(regex: str):
    i = 0
    length = len(regex)
    tokens = []
    while i < length:
        c = regex[i]
        
        # If we encounter an actual newline character in the regex,
        # treat it as a literal character.
        if c == '\n':
            tokens.append(('LIT', '\n'))
            i += 1
            continue

        # For other whitespace characters, skip them
        if c.isspace():
            i += 1
            continue

        if c == '\\':
            # Escaped character
            i += 1
            if i < length:
                esc = regex[i]
                tokens.append(('LIT', '\\' + esc))
        elif c in {'(', ')', '|', '*', '+', '?'}:
            tokens.append((c, c))
        elif c == '[':
            # character class
            end = regex.find(']', i+1)
            if end == -1:
                raise ValueError("Unclosed character class")
            content = regex[i+1:end]
            chars = set()
            j = 0
            while j < len(content):
                if j+2 < len(content) and content[j+1] == '-':
                    start_c = content[j]
                    end_c = content[j+2]
                    for cc in range(ord(start_c), ord(end_c)+1):
                        chars.add(chr(cc))
                    j += 3
                else:
                    chars.add(content[j])
                    j += 1
            tokens.append(('CLASS', chars))
            i = end
        else:
            # literal character
            tokens.append(('LIT', c))
        i += 1

    return tokens



class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def advance(self):
        tok = self.peek()
        if tok:
            self.pos += 1
        return tok

    def expect(self, type_, value=None):
        tok = self.peek()
        if not tok or tok[0] != type_ and tok[1] != value:
            raise ValueError(f"Expected {type_}{' '+value if value else ''}, got {tok}")
        return self.advance()

    def parse(self) -> Regex:
        # parse regex
        node = self.parse_union_expr()
        if self.peek() is not None:
            raise ValueError("Extra input after valid regex")
        return node

    def parse_union_expr(self) -> Regex:
        node = self.parse_concat_expr()
        while True:
            tok = self.peek()
            if tok and tok[0] == '|':
                self.advance()
                right = self.parse_concat_expr()
                node = Alternation(node, right)
            else:
                break
        return node

    def parse_concat_expr(self) -> Regex:
        node = self.parse_kleene_expr()
        while True:
            tok = self.peek()
            # If next token is '|', it should be handled by union_expr, not here.
            if tok and tok[0] == '|':
                break
            if tok and (tok[0] in ['LIT', 'CLASS', '(']):
                right = self.parse_kleene_expr()
                node = Concatenation(node, right)
            else:
                break
        return node


    def parse_kleene_expr(self) -> Regex:
        node = self.parse_basic_expr()
        while True:
            tok = self.peek()
            if tok and tok[0] in ['*', '+', '?']:
                op = self.advance()
                if op[0] == '*':
                    node = KleeneStar(node)
                elif op[0] == '+':
                    node = Plus(node)
                elif op[0] == '?':
                    node = Question(node)
            else:
                break
        return node

    def parse_basic_expr(self) -> Regex:
        tok = self.peek()
        if not tok:
            raise ValueError("Unexpected end of input")

        if tok[0] == 'LIT':
            self.advance()
            val = tok[1]
            if val.startswith('\\') and val != '\\n':
                # escaped literal
                return Literal(val[1:])
            elif val == '\\n':
                return Literal('\n')
            else:
                return Literal(val)
        elif tok[0] == 'CLASS':
            self.advance()
            return CharacterClass(tok[1])
        elif tok[0] == '(':
            # Parenthesized subexpression
            self.advance()
            node = self.parse_union_expr()
            self.expect(')', ')')
            return node
        else:
            raise ValueError(f"Unexpected token {tok}")

def parse_regex(regex: str) -> Regex:
    tokens = tokenize(regex)
    parser = Parser(tokens)
    ast = parser.parse()
    return ast

def main():
    test_regex = '(\n|[a-z])*'
    try:
        ast = parse_regex(test_regex)
        print("\nAST:", ast)
    except ValueError as e:
        print("\nError:", e)

if __name__ == "__main__":
    main()
