"""Quine-McCluskey minimisation with Petrick's method for an exact minimum sum-of-products."""
from __future__ import annotations

import itertools
from dataclasses import dataclass


def _bits(m: int, n: int) -> str:
    return format(m, f"0{n}b") if n else ""


def _combine(a: str, b: str) -> str | None:
    diff = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    if len(diff) == 1 and "-" not in (a[diff[0]], b[diff[0]]):
        return a[: diff[0]] + "-" + a[diff[0] + 1:]
    return None


def prime_implicants(minterms: list[int], dont_cares: list[int], n: int) -> list[str]:
    """All prime implicants as strings over {0, 1, -} (most significant variable first)."""
    current = {_bits(m, n) for m in set(minterms) | set(dont_cares)}
    primes: set[str] = set()
    while current:
        used, nxt = set(), set()
        for a, b in itertools.combinations(sorted(current), 2):
            c = _combine(a, b)
            if c:
                nxt.add(c); used.update((a, b))
        primes |= current - used
        current = nxt
    return sorted(primes)


def covers(implicant: str, minterm: int) -> bool:
    bits = _bits(minterm, len(implicant))
    return all(i in ("-", b) for i, b in zip(implicant, bits))


def literal_count(implicant: str) -> int:
    return sum(c != "-" for c in implicant)


@dataclass
class Minimization:
    n_vars: int
    minterms: list[int]
    dont_cares: list[int]
    primes: list[str]
    essential: list[str]
    cover: list[str]                 # selected implicants (minimum number of terms, then literals)

    def evaluate(self, value: int) -> int:
        return int(any(covers(i, value) for i in self.cover))


def minimize(minterms: list[int], dont_cares: list[int] | None = None, n: int | None = None) -> Minimization:
    dont_cares = sorted(set(dont_cares or []))
    minterms = sorted(set(minterms))
    if set(minterms) & set(dont_cares):
        raise ValueError("a minterm cannot also be a don't-care")
    top = max(minterms + dont_cares, default=0)
    n = n if n is not None else max(1, top.bit_length())
    if any(not 0 <= m < 2 ** n for m in minterms + dont_cares):
        raise ValueError("minterm out of range for the number of variables")
    if not minterms:
        return Minimization(n, [], dont_cares, [], [], [])
    primes = prime_implicants(minterms, dont_cares, n)
    table = {m: [p for p in primes if covers(p, m)] for m in minterms}
    essential = sorted({ps[0] for ps in table.values() if len(ps) == 1})
    remaining = [m for m in minterms if not any(covers(e, m) for e in essential)]
    chosen = list(essential)
    if remaining:
        # Petrick: product of sums over the uncovered minterms, expanded with absorption
        products: set[frozenset[str]] = {frozenset()}
        for m in remaining:
            new: set[frozenset[str]] = set()
            for prod in products:
                for p in table[m]:
                    new.add(prod | {p})
            products = {p for p in new if not any(q < p for q in new)}
        best = min(products, key=lambda s: (len(s), sum(literal_count(p) for p in s), sorted(s)))
        chosen += sorted(best)
    return Minimization(n, minterms, dont_cares, primes, essential, sorted(chosen))


def implicant_to_term(implicant: str, names: list[str]) -> str:
    lits = [(("~" if c == "0" else "") + names[i]) for i, c in enumerate(implicant) if c != "-"]
    return "&".join(lits) if lits else "1"


def to_sop(result: Minimization, names: list[str] | None = None) -> str:
    names = names or [chr(ord("A") + i) for i in range(result.n_vars)]
    if not result.cover:
        return "0"
    ordered = sorted(result.cover, key=lambda s: s.replace("-", "2"))      # terms in variable order
    return " | ".join(implicant_to_term(i, names) for i in ordered)


def kmap(minterms: list[int], n: int, dont_cares: list[int] | None = None, names: list[str] | None = None) -> str:
    """Text Karnaugh map for 2-4 variables (cells show 1, 0 or x)."""
    if n not in (2, 3, 4):
        raise ValueError("kmap supports 2 to 4 variables")
    names = names or [chr(ord("A") + i) for i in range(n)]
    gray = {1: ["0", "1"], 2: ["00", "01", "11", "10"]}
    row_bits, col_bits = n // 2, n - n // 2
    rows, cols = gray[row_bits], gray[col_bits]
    dc, mt = set(dont_cares or []), set(minterms)
    head = f"{''.join(names[:row_bits])}\\{''.join(names[row_bits:])}"
    lines = [f"{head:>6} " + " ".join(f"{c:>3}" for c in cols)]
    for r in rows:
        cells = []
        for c in cols:
            m = int(r + c, 2)
            cells.append("  1" if m in mt else "  x" if m in dc else "  0")
        lines.append(f"{r:>6} " + " ".join(cells))
    return "\n".join(lines)
