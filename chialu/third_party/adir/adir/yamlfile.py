"""The run file: yaml with `${VAR}` resolved from the environment,
duplicate keys rejected, the CHIA cluster keys separated from `adir:`."""
from __future__ import annotations

import os
import re
from pathlib import Path

import yaml

from .errors import BindError

CLUSTER_KEYS = ("cluster_name", "provider", "auth", "available_node_types",
                "aws_nodes", "head_start_ray_commands", "worker_start_ray_commands",
                "cache", "bypass", "docker", "setup_commands", "file_mounts",
                "initialization_commands", "max_workers", "upscaling_speed",
                "idle_timeout_minutes")
_VAR = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


class _Loader(yaml.SafeLoader):
    pass


def _no_duplicates(loader, node, deep=False):
    seen = set()
    for k, _ in node.value:
        key = loader.construct_object(k, deep=deep)
        if key in seen:
            raise BindError(str(key), "duplicate key")
        seen.add(key)
    return loader.construct_mapping(node, deep)


_Loader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_duplicates)


def resolve_env(value, missing: set, env=None):
    env = os.environ if env is None else env

    def sub(m):
        name = m.group(1)
        if name in env:
            return env[name]
        missing.add(name)
        return m.group(0)
    if isinstance(value, str):
        return _VAR.sub(sub, value)
    if isinstance(value, list):
        return [resolve_env(v, missing, env) for v in value]
    if isinstance(value, dict):
        return {k: resolve_env(v, missing, env) for k, v in value.items()}
    return value


def load(path, env=None):
    """(cluster keys, adir block, missing environment names)."""
    p = Path(path)
    if not p.is_file():
        raise BindError(str(path), "no such file")
    with open(p) as f:
        try:
            doc = yaml.load(f, Loader=_Loader)  # noqa: S506
        except yaml.YAMLError as e:
            raise BindError(str(path), f"yaml: {e}") from None
    if not isinstance(doc, dict):
        raise BindError(str(path), "the file is not a mapping")
    if "adir" not in doc or not isinstance(doc["adir"], dict):
        raise BindError(str(path), "no `adir:` block")
    missing: set = set()
    doc = resolve_env(doc, missing, env)
    cluster = {k: v for k, v in doc.items() if k != "adir"}
    return cluster, doc["adir"], missing


def check_keys(mapping: dict, known, path: str):
    if not isinstance(mapping, dict):
        raise BindError(path, "must be a mapping")
    unknown = set(mapping) - set(known)
    if unknown:
        raise BindError(path, f"unknown keys {sorted(unknown)} (known: {sorted(known)})")
