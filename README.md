# boolean-minimizer

Boolean expression parser and **exact two-level minimiser**: Quine-McCluskey prime-implicant generation followed by essential-implicant selection and
**Petrick's method** for a minimum sum-of-products (fewest terms, then fewest literals), with don't-cares and a text Karnaugh map.

## Installation and quick start
```bash
git clone https://github.com/nimaazamii/boolean-minimizer.git
cd boolean-minimizer
pip install -e ".[dev]"
pytest -q
```

```python
from boolmin import simplify, minimize, to_sop, kmap
print(simplify("A&B | A&~B | ~A&B"))
print(simplify("(A|B)&(A|~B)&(~A|C)"))
r = minimize([0, 1, 2, 5, 6, 7], n=3)          # cyclic function: two equally good covers exist
print(len(r.primes), "prime implicants,", len(r.cover), "terms in the minimum cover")
```
Output:
```
A | B
A&C
6 prime implicants, 3 terms in the minimum cover
```
Expression syntax: `~`/`!` NOT, `&`/`*` AND, `^` XOR, `|`/`+` OR, parentheses, constants `0`/`1`; precedence NOT > AND > XOR > OR.

## Verification (`pytest -q`, 11 tests)
* Prime implicants equal a **brute-force definition** (all cubes contained in on-set + don't-cares that cannot be enlarged) on 60 random functions of up to 4 variables.
* On 80 random functions (2-5 variables, with don't-cares) the selected cover is correct on every input that is not a don't-care, and its term and literal counts equal the **exhaustive optimum** over all subsets of prime implicants.
* Parser: truth tables, precedence, De Morgan equivalences, syntax errors; K-map layout uses Gray code.

## Example output (`python examples/demo.py`, saved in `results/demo_output.txt`)
```
A&B | A&~B | ~A&B                        ->  A | B
(A|B)&(A|~B)&(~A|C)                      ->  A&C
A^B^C                                    ->  ~A&~B&C | ~A&B&~C | A&~B&~C | A&B&C
~(A&B)&(A|B)                             ->  ~A&B | A&~B
A&B&C | A&B&~C | A&~B&C | ~A&B&C         ->  A&B | A&C | B&C

f(A,B,C,D) = sum m(4, 8, 10, 11, 12, 15) + d(9, 14)
 AB\CD  00  01  11  10
    00   0   0   0   0
    01   1   0   0   0
    11   1   0   1   x
    10   1   x   1   1
prime implicants: ['-100', '1--0', '1-1-', '10--']
essential: ['-100', '1-1-']
minimal cover: A&C | A&~D | B&~C&~D
```

## Limitations and future work
Two-level (sum-of-products) minimisation only; Petrick's expansion is exponential in the number of non-essential prime implicants (fine up to roughly 8 variables, not for large circuits; heuristics such as Espresso would be needed).
Multi-output functions, product-of-sums output and gate-level netlist generation are not implemented.

## References
* McCluskey (1956) Minimization of Boolean functions. Bell System Technical Journal 35(6); Quine (1952); Petrick (1956).

## License
MIT, see `LICENSE`.
