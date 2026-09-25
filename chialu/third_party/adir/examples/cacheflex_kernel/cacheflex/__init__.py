"""cacheflex: the CacheFlex artifact (github.com/JingqunZhang/cacheflex-ae)
as an ADIR domain library. The searched object is the loop nest that
drives the artifact's fixed SVE/SPM GEMM microkernel, with the K and M
tile sizes as searched variables; the nodes cross-compile through the
artifact's SPM encoder, check the loop nest under QEMU, and measure a
cell on the artifact's gem5 fork."""
from cacheflex.domain import SPM_GEMM  # noqa: F401

__all__ = ["SPM_GEMM"]
