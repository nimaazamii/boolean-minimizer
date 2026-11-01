import itertools
import random
import unittest

from boolmin import (ExprError, covers, kmap, literal_count, minimize, minterms_of, parse, prime_implicants, simplify,
                     to_sop, truth_table)


def brute_force_primes(minterms, dcs, n):
    """Implicants (cubes entirely inside on-set + dc-set) that cannot be enlarged."""
    allowed = set(minterms) | set(dcs)
    cubes = []
    for pattern in itertools.product("01-", repeat=n):
        p = "".join(pattern)
        cells = [m for m in range(2 ** n) if covers(p, m)]
        if cells and all(c in allowed for c in cells):
            cubes.append((p, set(cells)))
    return sorted(p for p, cells in cubes if not any(cells < other for _, other in cubes))


def brute_force_min_terms(minterms, primes):
    for k in range(1, len(primes) + 1):
        for combo in itertools.combinations(primes, k):
            if all(any(covers(p, m) for p in combo) for m in minterms):
                return k, min(sum(literal_count(p) for p in c) for c in itertools.combinations(primes, k)
                              if all(any(covers(q, m) for q in c) for m in minterms))
    return 0, 0


class TestExpressions(unittest.TestCase):
    def test_truth_tables(self):
        self.assertEqual(truth_table("A&B"), (["A", "B"], [0, 0, 0, 1]))
        self.assertEqual(truth_table("A|B")[1], [0, 1, 1, 1])
        self.assertEqual(truth_table("A^B")[1], [0, 1, 1, 0])
        self.assertEqual(truth_table("~A")[1], [1, 0])
        self.assertEqual(truth_table("A+B*C")[1], truth_table("A|(B&C)")[1])

    def test_precedence_and_de_morgan(self):
        self.assertEqual(truth_table("~A&B")[1], truth_table("(~A)&B")[1])
        self.assertEqual(truth_table("A|B&C^D")[1], truth_table("A|((B&C)^D)")[1])
        self.assertEqual(truth_table("~(A&B)", ["A", "B"])[1], truth_table("~A|~B", ["A", "B"])[1])
        self.assertEqual(truth_table("!!A")[1], truth_table("A")[1])

    def test_errors(self):
        for bad in ("A&", "(A|B", "A B", "A $ B", "", "&A"):
            with self.assertRaises(ExprError, msg=bad):
                parse(bad)
        with self.assertRaises(ExprError):
            parse("A&B", ["A"])

    def test_variable_order_and_constants(self):
        names, outs = truth_table("C&~A", ["C", "B", "A"])
        self.assertEqual((names, outs), (["C", "B", "A"], [0, 0, 0, 0, 1, 0, 1, 0]))
        self.assertEqual(simplify("A|~A"), "1")
        self.assertEqual(minterms_of("1&1", [])[1], [0])


class TestQuineMcCluskey(unittest.TestCase):
    def test_classic_examples(self):
        r = minimize([0, 1, 2, 5, 6, 7], n=3)                          # cyclic function: needs 3 two-literal terms
        self.assertEqual(len(r.cover), 3)
        self.assertEqual(len(r.primes), 6)
        self.assertEqual(r.essential, [])
        r = minimize([4, 8, 10, 11, 12, 15], [9, 14], 4)                # textbook example with don't-cares
        terms, lits = brute_force_min_terms(r.minterms, r.primes)
        self.assertEqual((len(r.cover), sum(literal_count(p) for p in r.cover)), (terms, lits))
        for m in r.minterms:
            self.assertEqual(r.evaluate(m), 1)
        for m in set(range(16)) - set(r.minterms) - set(r.dont_cares):
            self.assertEqual(r.evaluate(m), 0)

    def test_simplify_known_identities(self):
        self.assertEqual(simplify("A&B | A&~B"), "A")
        self.assertEqual(simplify("(A|B)&(A|~B)"), "A")
        self.assertEqual(simplify("A | ~A&B"), "A | B")
        self.assertEqual(simplify("A&~A"), "0")
        self.assertEqual(simplify("A|~A"), "1")
        self.assertEqual(len(simplify("A^B").split("|")), 2)
        self.assertEqual(truth_table(simplify("A^B"), ["A", "B"])[1], [0, 1, 1, 0])

    def test_prime_implicants_match_brute_force_definition(self):
        rng = random.Random(0)
        for _ in range(60):
            n = rng.randint(1, 4)
            cells = list(range(2 ** n)); rng.shuffle(cells)
            k, d = rng.randint(1, len(cells)), rng.randint(0, 3)
            ms, dcs = sorted(cells[:k]), sorted(cells[k:k + d])
            self.assertEqual(prime_implicants(ms, dcs, n), brute_force_primes(ms, dcs, n))

    def test_cover_is_correct_and_minimal_on_random_functions(self):
        rng = random.Random(1)
        for _ in range(80):
            n = rng.randint(2, 5)
            cells = list(range(2 ** n)); rng.shuffle(cells)
            k, d = rng.randint(1, len(cells) - 1), rng.randint(0, 4)
            ms, dcs = sorted(cells[:k]), sorted(cells[k:k + d])
            r = minimize(ms, dcs, n)
            for m in range(2 ** n):                                   # correct on every input that is not a don't-care
                if m in dcs:
                    continue
                self.assertEqual(r.evaluate(m), int(m in ms), (n, ms, dcs, r.cover))
            if len(r.primes) <= 14:
                terms, lits = brute_force_min_terms(ms, r.primes)
                self.assertEqual(len(r.cover), terms)
                self.assertEqual(sum(literal_count(p) for p in r.cover), lits)

    def test_expression_roundtrip_equivalence(self):
        rng = random.Random(2)
        names = ["A", "B", "C", "D"]
        for _ in range(40):
            outs = [rng.randint(0, 1) for _ in range(16)]
            ms = [i for i, v in enumerate(outs) if v]
            sop = simplify(" | ".join("&".join(("" if (m >> (3 - i)) & 1 else "~") + nm for i, nm in enumerate(names)) for m in ms) or "0", names)
            self.assertEqual(truth_table(sop, names)[1], outs)

    def test_edge_cases_and_validation(self):
        self.assertEqual(minimize([]).cover, [])
        self.assertEqual(to_sop(minimize([])), "0")
        self.assertEqual(to_sop(minimize([0, 1], n=1)), "1")
        with self.assertRaises(ValueError):
            minimize([1], [1], 2)
        with self.assertRaises(ValueError):
            minimize([9], n=3)


class TestKmap(unittest.TestCase):
    def test_four_variable_layout_uses_gray_code(self):
        text = kmap([0, 5, 15], 4, dont_cares=[1])
        lines = text.splitlines()
        self.assertEqual(len(lines), 5)
        self.assertEqual(lines[0].split()[1:], ["00", "01", "11", "10"])
        self.assertEqual([l.split()[0] for l in lines[1:]], ["00", "01", "11", "10"])
        self.assertEqual(lines[1].split()[1:], ["1", "x", "0", "0"])        # row 00: m0=1, m1=x
        self.assertEqual(lines[2].split()[1:], ["0", "1", "0", "0"])        # row 01: m5=1
        self.assertEqual(lines[3].split()[1:], ["0", "0", "1", "0"])        # row 11: m15=1
        with self.assertRaises(ValueError):
            kmap([0], 5)


if __name__ == "__main__":
    unittest.main()
