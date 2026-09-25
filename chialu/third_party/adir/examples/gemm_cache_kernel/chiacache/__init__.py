"""chiacache: GEMM kernels for a fixed cache configuration as an ADIR
domain library (examples/cacheflex_kernel). `chiacache.domain` registers
the Kernel template, its line kinds, its prompt and tactic sources;
`chiacache.nodes` holds the CHIA nodes (a static check, the build, the
conformance run, the cache simulation under cachegrind)."""
from chiacache.domain import KERNEL  # noqa: F401

__all__ = ["KERNEL"]
