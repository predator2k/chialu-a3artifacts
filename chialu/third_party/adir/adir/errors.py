"""Errors and the UNDECIDED value."""
from __future__ import annotations


class BindError(ValueError):
    """A bind-time error, named by the yaml path of the offending key."""

    def __init__(self, *args):
        if len(args) == 1:
            path, msg = "", str(args[0])
        else:
            path, msg = args[0], args[1]
        self.path = path
        self.msg = msg
        super().__init__(f"{path}: {msg}" if path else msg)


class _Undecided:
    """A value a node did not produce: the node failed, was skipped by a
    `when` condition, or was cancelled by a hard failure. It never
    satisfies a constraint and propagates through every expression."""
    __slots__ = ()

    def __repr__(self):
        return "UNDECIDED"

    def __bool__(self):
        return False


UNDECIDED = _Undecided()


def is_undecided(v) -> bool:
    return v is UNDECIDED
