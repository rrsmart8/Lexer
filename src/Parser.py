from dataclasses import dataclass
from typing import Any, List, Union


@dataclass
class Var:
    name: str

    def __str__(self):
        return f'Var "{self.name}"'

@dataclass
class Val:
    value: int

    def __str__(self):
        return f'Val {self.value}'

@dataclass
class Plus:
    left: Any
    right: Any

    def __str__(self):
        return f'Plus ({self.left}) ({self.right})'

@dataclass
class Minus:
    left: Any
    right: Any

    def __str__(self):
        return f'Minus ({self.left}) ({self.right})'

@dataclass
class Mult:
    left: Any
    right: Any

    def __str__(self):
        return f'Mult ({self.left}) ({self.right})'

@dataclass
class Lambda:
    var: Var
    expr: Any

    def __str__(self):
        return f'Lambda ({self.var}) -> {self.expr}'

@dataclass
class Parant:
    expr: Any

    def __str__(self):
        return f'Parant ({self.expr})'

class Parser:
    def __init__(self):
        self.tokens: List[str] = []
        self.pos: int = 0

    def parse(self, input_str: str) -> Any:
        """
        Parses the input string and returns the root of the AST.
        """
        self.tokens = self.tokenize(input_str)
        self.pos = 0

        ast = self.expression()
        return ast

    def tokenize(self, input_str: str) -> List[str]:
        """
        Converts the input string into a list of tokens.
        Tokens can be:
        - Operators: '+', '-', '*'
        - Parentheses: '(', ')'
        - Lambda: '\\'
        - Variables: single alphabetic characters
        - Integer Literals: multi-digit numbers
        """
        tokens = []
        i = 0
        while i < len(input_str):
            char = input_str[i]
            if char.isspace():
                i += 1
            elif char in {'+', '-', '*', '(', ')', '\\', '.'}:
                tokens.append(char)
                i += 1
            elif char.isdigit():
                num = char
                i += 1
                while i < len(input_str) and input_str[i].isdigit():
                    num += input_str[i]
                    i += 1
                tokens.append(num)
            elif char.isalpha():
                tokens.append(char)
                i += 1
            else:
                raise ValueError(f"Invalid character '{char}' at position {i}")
        return tokens

    def peek(self) -> str:
        """
        Returns the current token without consuming it.
        """
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return ''

    def consume(self) -> str:
        """
        Consumes and returns the current token.
        """
        token = self.peek()
        if self.pos < len(self.tokens):
            self.pos += 1
        return token

    def expression(self) -> Any:
        """
        Parses an expression.
        Grammar:
            expression = lambda | additive
        """
        if self.peek() == '\\':
            return self.lambda_expr()
        else:
            return self.additive()

    def lambda_expr(self) -> Any:
        """
        Parses a lambda expression.
        Grammar:
            lambda = '\' VAR '.' expression
        """
        self.consume()  # Consume '\\'
        var_token = self.consume()
        var = Var(var_token)
        self.consume()  # Consume '.'
        expr = self.expression()
        return Lambda(var, expr)

    def additive(self) -> Any:
        """
        Parses an additive expression.
        Grammar:
            additive = multiplicative (('+' | '-') multiplicative)*
        """
        node = self.multiplicative()
        while self.peek() in {'+', '-'}:
            op = self.consume()
            right = self.multiplicative()
            if op == '+':
                node = Plus(node, right)
            else:
                node = Minus(node, right)
        return node

    def multiplicative(self) -> Any:
        """
        Parses a multiplicative expression.
        Grammar:
            multiplicative = primary ('*' primary)*
        """
        node = self.primary()
        while self.peek() == '*':
            self.consume()
            right = self.primary()
            node = Mult(node, right)
        return node

    def primary(self) -> Any:
        """
        Parses a primary expression.
        Grammar:
            primary = VAR | VAL | '(' expression ')'
        """
        token = self.peek()
        if token == '(':
            self.consume()
            node = self.expression()
            self.consume()
            return Parant(node)
        elif token.isdigit():
            self.consume()
            return Val(int(token))
        elif token.isalpha():
            self.consume()
            return Var(token)
        else:
            print("Error")
