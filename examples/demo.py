"""Minimisation examples; writes results/demo_output.txt.

    python examples/demo.py
"""
from __future__ import annotations

from pathlib import Path

from boolmin import kmap, minimize, simplify, to_sop

OUT = Path(__file__).resolve().parents[1] / "results"
OUT.mkdir(exist_ok=True)


def main() -> None:
    lines = []
    for expr in ("A&B | A&~B | ~A&B", "(A|B)&(A|~B)&(~A|C)", "A^B^C", "~(A&B)&(A|B)", "A&B&C | A&B&~C | A&~B&C | ~A&B&C"):
        lines.append(f"{expr:<40} ->  {simplify(expr)}")
    ms, dc = [4, 8, 10, 11, 12, 15], [9, 14]
    r = minimize(ms, dc, 4)
    lines += ["", f"f(A,B,C,D) = sum m{tuple(ms)} + d{tuple(dc)}", kmap(ms, 4, dc),
              f"prime implicants: {r.primes}", f"essential: {r.essential}", f"minimal cover: {to_sop(r)}"]
    text = "\n".join(lines) + "\n"
    (OUT / "demo_output.txt").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
