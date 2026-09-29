"""Links of the target of ``activate`` and ``trial`` (docs/syntax.md section 1).

The code installed into a global function is resolved through that function's
links, so the names of the code are links of it. The names that only compute
the code, in the enclosing function, are not.
"""

import unittest

from semiroh.lang import FUNCTION_ROLE, LINKS_KIND
from semiroh.relations import relation_of
from semiroh.syntax import parse


def links(text: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}

    for value in parse(text).values.values():
        relation = relation_of(value)

        if relation is not None and relation.kind == LINKS_KIND:
            result[relation.roles[FUNCTION_ROLE].value] = sorted(set(relation.roles) - {FUNCTION_ROLE})

    return result


PRELUDE = """\
cell counter: int = 0

fn helper(x):
    x

fn f(x):
    label(l, x)

fn double(x):
    x + x

fn quad(x):
    double(double(x))

fn emit(n):
    quote(1)
"""


class InstalledCodeLinkTests(unittest.TestCase):
    def test_names_of_the_installed_code_are_links_of_the_target(self) -> None:
        self.assertEqual(
            links(PRELUDE + "\nfn install():\n    activate(f = fn(x): helper(x) + counter)\n")["f"],
            ["counter", "helper"],
        )
        self.assertEqual(
            links(PRELUDE + "\nfn try_it():\n    trial(quad(3), double = fn(x): helper(x))\n")["double"],
            ["helper"],
        )

    def test_a_node_edit_links_the_names_of_the_node_but_not_the_label(self) -> None:
        self.assertEqual(
            links(PRELUDE + "\nfn tune():\n    activate(f.l = quote(helper(x)))\n")["f"],
            ["helper"],
        )

    def test_a_parameter_of_the_installed_code_is_not_a_link(self) -> None:
        self.assertNotIn("f", links(PRELUDE + "\nfn install():\n    activate(f = fn(y): y + 1)\n"))

    def test_names_that_only_compute_the_code_are_not_links_of_the_target(self) -> None:
        for value in (
            'function(("x",), emit(3))',  # a call in the enclosing function
            "quote(unquote(emit(3)))",  # a call in a hole
            "fn(x): x * literal(counter)",  # a read in a hole
        ):
            with self.subTest(value=value):
                self.assertNotIn("f", links(PRELUDE + f"\nfn install():\n    activate(f = {value})\n"))


if __name__ == "__main__":
    unittest.main()
