"""Coverage sampling (activation_path): a (variable, member) pair that an `inactive_when` clause closes
whatever the path draws is refused up front instead of sampled a few times and dropped, and the draws of
the kept paths and of sample_declaration are unchanged."""
from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from adir.backends.numeric import activation_path, sample_declaration  # noqa: E402
from adir.domains import Enum, Range  # noqa: E402
from adir.variables import Variable, _topological  # noqa: E402


def _inst(modulus_members):
    """family -> {modulus, modulus_value}; modulus_value is inactive under `eac` unless modulus is `generic`
    (the adder spaces' end_around_carry); `modulus_members` is modulus's (narrowed) domain."""
    vs = [Variable("family", Enum(("plain", "eac")), {"search"}),
          Variable("modulus", Enum(("m1", "m2", "generic")), {"search"}, when=("family", ("eac",))),
          Variable("modulus_value", Range(3, 40), {"search"}, when=("family", ("eac",)),
                   inactive_when=((("family", ("eac",)), ("modulus", ("m1", "m2"))),))]
    doms = {"family": vs[0].domain, "modulus": Enum(tuple(modulus_members)), "modulus_value": vs[2].domain}
    bindings = {v.name: SimpleNamespace(time="search", domain=doms[v.name], variable=v) for v in vs}
    order = _topological(vs)
    return SimpleNamespace(bindings=bindings, variable_order=lambda: list(order))


class ActivationPath(unittest.TestCase):
    def test_closed_pair_refused(self):
        inst = _inst(("m1", "m2"))              # narrowed: `generic` cannot occur
        self.assertIsNone(activation_path(inst, "modulus_value", 7, random.Random(0)))
        self.assertIsNotNone(activation_path(inst, "modulus", "m1", random.Random(0)))

    def test_open_pair_kept_and_reached(self):
        inst = _inst(("m1", "m2", "generic"))
        rng = random.Random(3)
        path = activation_path(inst, "modulus_value", 7, rng)
        self.assertEqual(path, {"modulus_value": 7, "family": "eac"})
        hit = sum(sample_declaration(inst, rng, path).get("modulus_value") == 7 for _ in range(60))
        self.assertGreater(hit, 0)

    def test_refusal_leaves_the_draws(self):
        """The check runs after the walk: a refused path consumes what a kept one does, and
        sample_declaration's draws do not depend on it."""
        a, b = random.Random(11), random.Random(11)
        activation_path(_inst(("m1", "m2")), "modulus_value", 7, a)
        activation_path(_inst(("m1", "m2", "generic")), "modulus_value", 7, b)
        self.assertEqual(a.getstate(), b.getstate())
        inst = _inst(("m1", "m2", "generic"))
        r1, r2 = random.Random(5), random.Random(5)
        self.assertEqual([sample_declaration(inst, r1) for _ in range(50)],
                         [sample_declaration(inst, r2) for _ in range(50)])


if __name__ == "__main__":
    unittest.main()
