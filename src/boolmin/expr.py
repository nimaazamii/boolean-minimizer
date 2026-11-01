"""Boolean expression parser. Operators: ~ or ! (NOT), & or * (AND), ^ (XOR), | or + (OR); parentheses; constants 0/1."""
from __future__ import annotations

import itertools
import re
from collections.abc import Callable

_TOKEN = re.compile(r"\s*(?:([A-Za-z_]\w*)|([01])|(.))")


class ExprError(ValueError):
    pass


def _tokenize(s: str) -> list[tuple[str, str]]:
    out, pos = [], 0
    while pos < len(s):
        m = _TOKEN.match(s, pos)
        if not m or m.end() == pos:
            break
        pos = m.end()
        if m.group(1):
            out.append(("var", m.group(1)))
        elif m.group(2):
            out.append(("const", m.group(2)))
        elif m.group(3):
            out.append(("op", m.group(3)))
    if s[pos:].strip():
        raise ExprError(f"cannot tokenize {s[pos:]!r}")
    return out


class _Parser:
    def __init__(self, toks: list[tuple[str, str]]) -> None:
        self.t, self.i, self.vars = toks, 0, []

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def take(self):
        self.i += 1
        return self.t[self.i - 1]

    def parse(self):
        node = self.or_()
        if self.i != len(self.t):
            raise ExprError(f"unexpected {self.peek()[1]!r}")
        return node

    def or_(self):
        node = self.xor()
        while self.peek() in (("op", "|"), ("op", "+")):
            self.take(); node = ("or", node, self.xor())
        return node

    def xor(self):
        node = self.and_()
        while self.peek() == ("op", "^"):
            self.take(); node = ("xor", node, self.and_())
        return node

    def and_(self):
        node = self.not_()
        while self.peek() in (("op", "&"), ("op", "*")):
            self.take(); node = ("and", node, self.not_())
        return node

    def not_(self):
        if self.peek() in (("op", "~"), ("op", "!")):
            self.take()
            return ("not", self.not_())
        return self.atom()

    def atom(self):
        kind, text = self.peek()
        if kind is None:
            raise ExprError("unexpected end of expression")
        if kind == "var":
            self.take()
            if text not in self.vars:
                self.vars.append(text)
            return ("var", text)
        if kind == "const":
            self.take()
            return ("const", int(text))
        if (kind, text) == ("op", "("):
            self.take()
            node = self.or_()
            if self.peek() != ("op", ")"):
                raise ExprError("missing ')'")
            self.take()
            return node
        raise ExprError(f"unexpected {text!r}")


def _eval(node, env: dict[str, int]) -> int:
    k = node[0]
    if k == "var":
        return env[node[1]]
    if k == "const":
        return node[1]
    if k == "not":
        return 1 - _eval(node[1], env)
    a, b = _eval(node[1], env), _eval(node[2], env)
    return a & b if k == "and" else a | b if k == "or" else a ^ b


def parse(expression: str, variables: list[str] | None = None) -> tuple[list[str], Callable[[dict[str, int]], int]]:
    """Return (variable names, evaluator). Variables default to sorted order of appearance."""
    p = _Parser(_tokenize(expression))
    tree = p.parse()
    names = list(variables) if variables is not None else sorted(p.vars)
    if variables is not None and not set(p.vars) <= set(variables):
        raise ExprError("expression uses variables not in the given list")
    return names, lambda env: _eval(tree, env)


def truth_table(expression: str, variables: list[str] | None = None) -> tuple[list[str], list[int]]:
    """Return (variables, output column) with the first variable as the most significant input bit."""
    names, f = parse(expression, variables)
    outs = [f(dict(zip(names, bits))) for bits in itertools.product((0, 1), repeat=len(names))]
    return names, outs


def minterms_of(expression: str, variables: list[str] | None = None) -> tuple[list[str], list[int]]:
    names, outs = truth_table(expression, variables)
    return names, [i for i, v in enumerate(outs) if v]
