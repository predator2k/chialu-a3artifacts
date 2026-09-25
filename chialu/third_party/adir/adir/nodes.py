"""Node resolution and execution (design section 6.1). A node is a
CHIA node: a `@ChiaFunction` of a domain library, a node type CHIA
ships, or ADIR's own `adir.declaration` and `adir.instance`. A node
takes keyword inputs and returns a dict. The local executor calls the
underlying function directly and caches by content; under a ray
cluster the ChiaFunction's remote entry is used."""
from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import re
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from .errors import BindError
from .registry import underlying

BUILTIN = ("adir.declaration", "adir.instance")


@dataclass
class NodeSpec:
    name: str
    fn: Optional[Callable]              # None for a builtin
    params: Optional[set]               # None: accepts any keyword
    required: set
    outputs: Optional[list]             # documented outputs, or None
    resources: dict
    cache_id: Optional[Callable] = None  # kwargs -> a string folded into the cache key
    transient: list = field(default_factory=list)   # outputs the graph passes on but no record keeps

    def accepts(self, key: str) -> bool:
        return self.params is None or key in self.params


def _outputs_from_doc(fn) -> Optional[list]:
    doc = inspect.getdoc(fn) or ""
    for line in doc.splitlines():
        s = line.strip()
        if s.lower().startswith("outputs:"):
            body = s.split(":", 1)[1]
            return [x.strip().strip(".") for x in body.split(",") if x.strip()]
    return None


def _catalog_lookup(name: str):
    """A node type of CHIA's catalog, when CHIA exposes one."""
    cat = os.environ.get("ADIR_NODE_CATALOG")
    modules = [cat] if cat else []
    modules += ["chia.nodes", "chia.catalog"]
    for modname in modules:
        try:
            mod = importlib.import_module(modname)
        except Exception:  # noqa: BLE001
            continue
        for getter in ("get", "lookup", "resolve"):
            g = getattr(mod, getter, None)
            if callable(g):
                try:
                    fn = g(name)
                except Exception:  # noqa: BLE001
                    fn = None
                if fn is not None:
                    return fn
        fn = getattr(mod, name, None)
        if callable(fn):
            return fn
    return None


def resolve_node(name: str, path: str = "") -> NodeSpec:
    if name in BUILTIN:
        return NodeSpec(name, None, None, set(), None, {})
    fn = None
    if "." in name:
        modname, attr = name.rsplit(".", 1)
        try:
            mod = importlib.import_module(modname)
            fn = getattr(mod, attr, None)
        except ModuleNotFoundError as e:
            if not (e.name and modname.startswith(e.name)):
                raise BindError(path, f"importing {modname}: {e}") from e
        except Exception as e:  # noqa: BLE001
            raise BindError(path, f"importing {modname}: {e}") from e
    if fn is None:
        fn = _catalog_lookup(name)
    if fn is None or not callable(fn):
        raise BindError(path, f"node {name!r} is neither an importable function nor a "
                              f"node of CHIA's catalog")
    base = underlying(fn)
    params, required = None, set()
    try:
        sig = inspect.signature(base)
        if not any(p.kind is p.VAR_KEYWORD for p in sig.parameters.values()):
            params = {n for n, p in sig.parameters.items()
                      if p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)}
            required = {n for n, p in sig.parameters.items()
                        if p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
                        and p.default is p.empty}
    except (TypeError, ValueError):
        pass
    outputs = getattr(fn, "adir_outputs", None) or getattr(base, "adir_outputs", None) \
        or _outputs_from_doc(base)
    resources = dict(getattr(fn, "adir_resources", None) or getattr(base, "adir_resources", None)
                     or getattr(fn, "resources", None) or {})
    cache_id = getattr(fn, "adir_cache_id", None) or getattr(base, "adir_cache_id", None)
    transient = list(getattr(fn, "adir_transient", None) or getattr(base, "adir_transient", None) or [])
    return NodeSpec(name, fn, params, required, outputs, resources, cache_id, transient)


CLUSTER = {"connected": False}   # set by adir.cli.connect: nodes and agent calls go through ray only then


def ray_get(ref):
    """The value of a task reference: CHIA's `get` where CHIA is
    importable (its cache wraps a reference in a callback object that
    plain ray.get refuses), else ray.get."""
    try:
        from chia.base.ChiaFunction import get  # type: ignore
        return get(ref)
    except ImportError:
        import ray  # type: ignore
        return ray.get(ref)


def ray_remote_of(fn):
    """The callable that submits `fn` as a ray task (`chia_remote`, else ray's `remote`), or None.
    ADIR_RAY_SCHEDULING (e.g. SPREAD) sets the task's `scheduling_strategy` where the function takes
    `.options(...)`: ray's default packs tasks onto the submitting node while it has room, leaving the
    cluster's other nodes idle. A wrapper without `.options` (a node-pinned one) is left as it is."""
    strategy = os.environ.get("ADIR_RAY_SCHEDULING", "").strip()
    opts = getattr(fn, "options", None)
    if strategy and callable(opts) and (hasattr(fn, "chia_remote") or hasattr(fn, "remote")):
        fn = opts(scheduling_strategy=strategy)
    return getattr(fn, "chia_remote", None) or getattr(fn, "remote", None)


def content_key(name: str, kwargs: dict, extra: str = "") -> str:
    """The cache key of one node call: the node's name, its keyword
    arguments and `extra`. `extra` is what the arguments do not carry,
    which for a synthesis node is the flow it runs under: the liberty
    files, the resolved ABC script and the tool versions. Without it a
    changed liberty or an upgraded yosys serves the old measurement."""
    h = hashlib.sha256()
    h.update(name.encode())
    h.update(json.dumps(kwargs, sort_keys=True, default=_stable).encode())
    if extra:
        h.update(b"|")
        h.update(str(extra).encode())
    return h.hexdigest()


_TRANSIENT_RE = re.compile(r"\b(timed out|timeout|out of memory|killed|connection reset|"
                           r"resource temporarily unavailable)\b", re.I)

# Ray's own failures: the task's owner, worker, actor or node died, an object was lost, the GCS or the raylet
# could not be reached. None says anything about the candidate, so none may become its hard failure: the call
# is submitted again, and past the retries the graph raises InfrastructureError, which the evaluator entry
# answers by evaluating the candidate again.
_INFRA_NAMES = ("OwnerDiedError", "WorkerCrashedError", "ActorDiedError", "ActorUnavailableError",
                "NodeDiedError", "LocalRayletDiedError", "ObjectLostError", "ObjectFetchTimedOutError",
                "ObjectReconstructionFailed", "ReferenceCountingAssertionError", "RaySystemError",
                "RpcError", "PlasmaObjectNotAvailable", "OutOfDiskError")
_INFRA_RE = re.compile("|".join(_INFRA_NAMES) + r"|failed to connect to (the )?gcs|gcs (server|client)\b.{0,80}"
                       r"(unavailable|disconnect|timed out|failed)|lost connection to (the )?gcs|"
                       r"statuscode\.unavailable|raylet (died|is dead)|the worker died unexpectedly", re.I)


class InfrastructureError(RuntimeError):
    """A node call ray could not complete for reasons of its own, retries exhausted."""


def is_infra_error(e: BaseException) -> bool:
    """Whether `e` (or what it wraps: a RayTaskError's cause, the exception chain) is a ray
    infrastructure failure rather than the node's own error."""
    seen = 0
    cur = e
    while cur is not None and seen < 8:
        if isinstance(cur, InfrastructureError):
            return True
        names = " ".join(c.__name__ for c in type(cur).__mro__)
        if any(n in names for n in _INFRA_NAMES):
            return True
        if type(cur).__module__.startswith("ray") or "RayTaskError" in names:
            head = str(cur).strip().splitlines()[:1]
            if head and _INFRA_RE.search(head[0]):
                return True
        seen += 1
        cur = getattr(cur, "cause", None) or cur.__cause__ or cur.__context__
    return False


def infra_detail(out) -> bool:
    """A failed node output whose message is a ray infrastructure failure (a node that caught one)."""
    if not isinstance(out, dict) or (out.get("ok") is not False and out.get("pass") is not False
                                     and out.get("status") != "fail"):
        return False
    return any(isinstance(out.get(k), str) and _INFRA_RE.search(out[k]) for k in ("detail", "error", "phase"))


def _transient(out: dict) -> bool:
    """A failure the inputs do not explain: a timeout, an exhausted
    machine, a dropped connection. Caching one makes it permanent for
    that text, so the run never measures the candidate again."""
    if out.get("ok") is not False and out.get("pass") is not False and out.get("status") != "fail":
        return False
    for k in ("detail", "phase", "error"):
        v = out.get(k)
        if isinstance(v, str) and (_TRANSIENT_RE.search(v) or _INFRA_RE.search(v)):
            return True
    return False


def _stable(v):
    if hasattr(v, "to_json"):
        return v.to_json()
    return str(v)


class Executor:
    """Runs a node: through ray when the function has a remote entry and
    ray is initialized, else locally. Caches by content under
    `cache_dir` when given, and through CHIA's cache actor when one is
    started (the content key is the call's `_chia_tag`, so a repeated
    call of a function the run file marks `cache: true` is a hit across
    runs). `submit` runs a node on a worker thread, so the graph runner
    overlaps the nodes with no unmet dependency."""

    def __init__(self, cache_dir: Optional[Path] = None, use_ray: Optional[bool] = None,
                 workers: int = 8):
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.use_ray = use_ray
        self.workers = max(1, int(workers))
        self.calls = 0
        self.hits = 0
        self._pool = None
        self._member_pool = None
        self._chia_cache = None
        self._chia_cache_checked = False

    def _ray_ok(self):
        if self.use_ray is False:
            return False
        if self.use_ray is None:
            # a CHIA node called in-process joins the cluster on its own, so
            # ray's state is no sign that ADIR connected (`adir run --local`)
            return CLUSTER["connected"]
        try:
            import ray  # type: ignore
            return ray.is_initialized()
        except Exception:  # noqa: BLE001
            return False

    def _cache_actor(self):
        if self._chia_cache_checked:
            return self._chia_cache
        self._chia_cache_checked = True
        if self._ray_ok():
            try:
                from chia.base.cache import get_active_cache  # type: ignore
                self._chia_cache = get_active_cache()
            except Exception:  # noqa: BLE001
                self._chia_cache = None
        return self._chia_cache

    def submit(self, fn, *args):
        """A concurrent.futures.Future of `fn(*args)` on a worker thread."""
        from concurrent.futures import ThreadPoolExecutor
        if self._pool is None:
            self._pool = ThreadPoolExecutor(max_workers=self.workers, thread_name_prefix="adir-node")
        return self._pool.submit(fn, *args)

    def submit_member(self, fn, *args):
        """A future on a pool `submit` does not share. One member of a
        mapped node is submitted from inside a call that is itself running
        on the outer pool, and one pool for both would let saturated outer
        calls wait on members that can never be scheduled."""
        from concurrent.futures import ThreadPoolExecutor
        if self._member_pool is None:
            self._member_pool = ThreadPoolExecutor(max_workers=self.workers,
                                                   thread_name_prefix="adir-member")
        return self._member_pool.submit(fn, *args)

    def _ray_call(self, name: str, remote, call_kwargs: dict):
        """`remote(**call_kwargs)`'s value, submitted again (ADIR_RAY_INFRA_RETRIES attempts in all, default 3,
        a growing pause between) while ray itself fails; InfrastructureError past the last."""
        import time as _time
        tries = max(1, int(os.environ.get("ADIR_RAY_INFRA_RETRIES") or 3))
        pause = float(os.environ.get("ADIR_RAY_INFRA_BACKOFF_S") or 10)
        last = None
        for attempt in range(tries):
            if attempt:
                _time.sleep(pause * attempt)
            try:
                out = ray_get(remote(**call_kwargs))
            except Exception as e:  # noqa: BLE001
                if not is_infra_error(e):
                    raise
                last = f"{type(e).__name__}: {str(e).strip().splitlines()[0] if str(e).strip() else ''}"
                continue
            if infra_detail(out):
                last = str(out.get("detail") or out.get("error") or "")[:500]
                continue
            return out
        raise InfrastructureError(f"{name}: ray failed {tries} time(s): {last}")

    def run(self, spec: NodeSpec, kwargs: dict) -> dict:
        extra = ""
        if spec.cache_id is not None:
            try:
                extra = str(spec.cache_id(kwargs) or "")
            except Exception:  # noqa: BLE001 - a node that cannot name its flow caches on the arguments
                extra = ""
        key = content_key(spec.name, kwargs, extra)
        if self.cache_dir:
            f = self.cache_dir / f"{key}.json"
            if f.is_file():
                self.hits += 1
                return json.loads(f.read_text())
        actor = self._cache_actor()
        if actor is not None:
            try:
                import ray  # type: ignore
                hit, value = ray.get(actor.read.remote(key))
                if hit and isinstance(value, dict):
                    self.hits += 1
                    if self.cache_dir:
                        (self.cache_dir / f"{key}.json").write_text(json.dumps(value, default=_stable))
                    return value
            except Exception:  # noqa: BLE001
                pass
        self.calls += 1
        fn = spec.fn
        out = None
        if self._ray_ok():
            remote = ray_remote_of(fn)
            if callable(remote):
                call_kwargs = dict(kwargs)
                if actor is not None:
                    call_kwargs["_chia_tag"] = key
                out = self._ray_call(spec.name, remote, call_kwargs)
        if out is None:
            base = underlying(fn)
            out = base(**kwargs)
        if not isinstance(out, dict):
            raise RuntimeError(f"node {spec.name} returned {type(out).__name__}, not a dict")
        out = json.loads(json.dumps(out, default=_stable))
        if self.cache_dir and not _transient(out):
            (self.cache_dir / f"{key}.json").write_text(json.dumps(out))
        return out
