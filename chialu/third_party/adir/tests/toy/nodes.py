"""Pure-Python nodes of the toy domain."""
from adir import node


@node(outputs=["pass", "detail"])
def check(text):
    ok = "return" in text and "syntax_error" not in text
    return {"pass": ok, "detail": "ok" if ok else "no return statement"}


@node(outputs=["ok", "area", "delay", "per_lane", "blob"], transient=["blob"])
def measure(text, lanes, style="x", scale=1):
    body = text.split("def compute")[-1]
    area = len(body) * scale + (5 if style == "y" else 0)
    # `blob` stands for a compiled artifact: the graph carries it to the nodes that
    # read it and the record keeps its size alone
    return {"ok": True, "area": area, "delay": 90 + 2 * lanes,
            "per_lane": {f"l{i}": area / lanes for i in range(lanes)}, "blob": "b" * 4096}


@node(outputs=["cycles", "ok"])
def curve(text, cap):
    # `ok` is a boolean per member: what `min` over the mapping aggregates, which is
    # the shape a `when` and a hard row take over a mapped check
    return {"cycles": 1000 // cap + len(text) % 7, "ok": "syntax_error" not in text}


@node(outputs=["built", "detail"])
def build_check(text):
    """A gate a `rollback` node stands on: the edit did not survive."""
    ok = "does_not_build" not in text
    return {"built": ok, "detail": "ok" if ok else "does_not_build in the text"}


@node(outputs=["seen"])
def after_curve(text, cap):
    """A mapped node whose members take different times, for the tail rule."""
    import time as _t
    _t.sleep(0.4 if cap == 4 else 0.01)
    return {"seen": cap}


@node(outputs=["score", "blob_bytes"])
def slow(text, blob=""):
    return {"score": {"mean": 1.0, "lo": 0.9, "hi": 1.1, "n": 5}, "blob_bytes": len(blob)}


def failing(text):
    raise RuntimeError("boom")


def numeric_measure(k, style, lanes):
    return {"ok": True, "area": 100 + 3 * k + (7 if style == "y" else 0) - 2 * lanes,
            "delay": 50 + k}
