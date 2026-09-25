"""Reject an unsuccessful compilation even when its exit code wraps."""
from pathlib import Path
import re


def compile_failure(artifact, returncode, diagnostics):
    """Return a failure reason, or None for a fresh nonempty artifact.

    The caller must remove any previous artifact before invoking the
    compiler. A compiler that returns the error count modulo 256 can exit
    zero after failing, so an exit code of zero does not by itself
    establish successful compilation; the diagnostics and the artifact
    decide.
    """
    artifact = Path(artifact)
    if returncode:
        return diagnostics.strip() or f'the compiler exited with status {returncode}'
    if re.search(r'(?mi)(?:^|:\s+)(?:syntax error\b|error\s*:|%Error)|^\s*[1-9][0-9]* errors? during elaboration', diagnostics):
        return diagnostics.strip()
    if not artifact.is_file() or artifact.stat().st_size == 0:
        return 'the compiler returned zero without a nonempty artifact'
    return None


def passing_bench_line(line):
    """Recognize native PASS or the complete seed bench's counted PASS."""
    if line == 'PASS' or line.startswith('PASS '):
        return True
    match = re.fullmatch(r'CONFORMANCE PASS ([0-9]+)/([0-9]+)', line)
    return bool(match and int(match[1]) == int(match[2]) and int(match[1]) > 0)
