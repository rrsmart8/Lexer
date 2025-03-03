from .Regex import Regex, parse_regex
from .NFA import NFA

class Lexer:
    def __init__(self, spec: list[tuple[str, str]]) -> None:
        self.spec = [(token, parse_regex(regex)) for token, regex in spec]

    def lex(self, word: str) -> list[tuple[str, str]] | None:
        i = 0
        tokens = []
        line = 0
        column = 0

        while i < len(word):
            longest_match = None
            longest_token = None
            longest_length = 0

            # Try matching each regex in the spec
            for token, regex in self.spec:
                nfa = regex.thompson()
                dfa = nfa.subset_construction()
                j = i
                current_state = dfa.q0

                # Simulate the DFA for the current regex
                while j < len(word) and (current_state, word[j]) in dfa.d:
                    current_state = dfa.d[(current_state, word[j])]
                    j += 1
                    if current_state in dfa.F:
                        match_length = j - i
                        if match_length > longest_length:
                            longest_match = word[i:j]
                            longest_token = token
                            longest_length = match_length

            # If no match is found, return an error
            if not longest_match:
                return "Error"
            
            # Add the matched token to the result and move the pointer
            tokens.append((longest_token, longest_match))
            i += longest_length


        return tokens

# Main
if __name__ == '__main__':
    spec = [("ones", "11+"), ("pair", "01|10"), ("other", "0|1")]
    lexer = Lexer(spec)
    test = "1001"
    
    result = lexer.lex(test)
    print(result)