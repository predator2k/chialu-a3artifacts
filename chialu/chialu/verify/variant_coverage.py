"""Keep complete-product coverage separate from samples and solver timeouts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3
import importlib.metadata
import subprocess

from chialu.variants import canonical


def source_revision():
    """Invalidate verification records when a generator, a space or a golden changes."""
    root = Path(__file__).resolve().parents[1]
    checksum = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix in (".py", ".sv"):
            checksum.update(str(path.relative_to(root)).encode() + b"\0" + path.read_bytes() + b"\0")
    import adir
    for path in sorted(Path(adir.__file__).parent.rglob("*.py")):
        checksum.update(str(path.relative_to(Path(adir.__file__).parent)).encode() + b"\0" + path.read_bytes() + b"\0")
    for package in ("mpmath", "numpy"):
        try:
            version = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            version = "unavailable"
        checksum.update(f"{package}={version}".encode())
    for command in (("yosys", "-V"), ("verilator", "--version")):
        try:
            result = subprocess.run(command, capture_output=True, timeout=5)
            checksum.update(canonical(command).encode() + b"\0" + result.stdout + result.stderr)
        except (OSError, subprocess.TimeoutExpired):
            checksum.update(canonical(command).encode() + b" unavailable")
    return checksum.hexdigest()


class Coverage:
    def __init__(self, directory, revision=None):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.revision = revision or source_revision()
        self.db = sqlite3.connect(self.directory / "coverage.sqlite3")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS scopes (
                id TEXT PRIMARY KEY, revision TEXT NOT NULL, entry TEXT NOT NULL,
                geometry TEXT NOT NULL, total TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS points (
                scope TEXT NOT NULL, ordinal TEXT NOT NULL, status TEXT NOT NULL,
                result TEXT NOT NULL, PRIMARY KEY(scope, ordinal));
            CREATE TABLE IF NOT EXISTS evidence (
                revision TEXT NOT NULL, hash TEXT NOT NULL, result TEXT NOT NULL,
                PRIMARY KEY(revision, hash));
        """)

    def scope(self, entry, geometry):
        key = hashlib.sha256(canonical([self.revision, entry.id, geometry]).encode()).hexdigest()
        self.db.execute("INSERT OR IGNORE INTO scopes VALUES (?, ?, ?, ?, ?)",
                        (key, self.revision, entry.id, canonical(geometry), str(entry.product.count)))
        self.db.commit()
        return key

    def get(self, scope, ordinal):
        row = self.db.execute("SELECT result FROM points WHERE scope=? AND ordinal=?", (scope, str(ordinal))).fetchone()
        return json.loads(row[0]) if row else None

    def record(self, scope, ordinal, result):
        row = self.db.execute("SELECT total FROM scopes WHERE id=?", (scope,)).fetchone()
        if row is None or not 0 <= ordinal < int(row[0]):
            raise ValueError("coverage ordinal is outside the registered product")
        if result["status"] == "pass" and not (
                result.get("generation") == "pass" and result.get("golden") == "pass"):
            raise ValueError("passing coverage requires RTL generation and golden evidence")
        if result["status"] == "excluded":
            from chialu.variant_legality import reason
            expected = reason(result["family"], result["pins"], result["width"], result.get("kind"))
            if expected is None or result.get("legality") != expected:
                raise ValueError("an exclusion requires a matching documented legality rule")
        self.db.execute("INSERT OR REPLACE INTO points VALUES (?, ?, ?, ?)",
                        (scope, str(ordinal), result["status"], canonical(result)))
        self.db.commit()

    def evidence(self, key, result=None):
        if result is None:
            row = self.db.execute("SELECT result FROM evidence WHERE revision=? AND hash=?", (self.revision, key)).fetchone()
            return json.loads(row[0]) if row else None
        self.db.execute("INSERT OR REPLACE INTO evidence VALUES (?, ?, ?)", (self.revision, key, canonical(result)))
        self.db.commit()

    def report(self, scopes):
        rows = []
        for scope in scopes:
            entry, geometry, total = self.db.execute("SELECT entry, geometry, total FROM scopes WHERE id=?", (scope,)).fetchone()
            counts = dict(self.db.execute("SELECT status, COUNT(*) FROM points WHERE scope=? GROUP BY status", (scope,)))
            remaining = int(total) - counts.get("pass", 0) - counts.get("excluded", 0)
            fidelity_passed = sum(json.loads(result).get("fidelity_status") == "pass" for (result,) in self.db.execute(
                "SELECT result FROM points WHERE scope=? AND status='pass'", (scope,)))
            fidelity_remaining = int(total) - fidelity_passed - counts.get("excluded", 0)
            rows.append({"entry": entry, "geometry": json.loads(geometry), "declared": total, "counts": counts,
                         "unvisited": str(int(total) - sum(counts.values())), "uncovered": str(remaining),
                         "complete": remaining == 0, "fidelity_passed": fidelity_passed,
                         "fidelity_uncovered": str(fidelity_remaining), "fidelity_complete": fidelity_remaining == 0})
        return {"revision": self.revision, "scope": "functional verification of complete declared pin products", "entries": rows,
                "complete": bool(rows) and all(row["complete"] for row in rows),
                "fidelity_complete": bool(rows) and all(row["fidelity_complete"] for row in rows),
                "uncovered": str(sum(int(row["uncovered"]) for row in rows))}
