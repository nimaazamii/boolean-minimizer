"""boolmin: Boolean expression parsing, Quine-McCluskey/Petrick minimisation and Karnaugh maps."""
from .expr import ExprError, minterms_of, parse, truth_table
from .qm import Minimization, covers, implicant_to_term, kmap, literal_count, minimize, prime_implicants, to_sop


def simplify(expression: str, variables: list[str] | None = None) -> str:
    """Minimal sum-of-products form of a Boolean expression."""
    names, ms = minterms_of(expression, variables)
    if not names:
        return "1" if ms else "0"
    return to_sop(minimize(ms, n=len(names)), names)


__version__ = "0.1.0"
__all__ = ["ExprError", "Minimization", "covers", "implicant_to_term", "kmap", "literal_count", "minimize", "minterms_of",
           "parse", "prime_implicants", "simplify", "to_sop", "truth_table"]
