"""F-11 regression tests: dependency manifests must be single-source and consistent.

Verifies (Phase 2, Priority 5 — F-11):
1. No package is declared twice (with potentially conflicting constraints) in a manifest.
2. Test/lint tooling is declared only in `requirements-dev.txt`, which extends the runtime
   manifest (`-r requirements.txt`).
3. No two competing PostgreSQL drivers are declared.
4. Every file referenced by the Dockerfile (`COPY` sources and `-r` targets) exists in the
   build context, and every manifest referenced by the Makefile exists.

These checks are static on purpose: a real `docker build` / `pip install` is not part of the
authorised verification scope, but the class of defect F-11 reported is caught here.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND = REPO_ROOT / "backend"
RUNTIME = BACKEND / "requirements.txt"
DEV = BACKEND / "requirements-dev.txt"
DOCKERFILE = BACKEND / "Dockerfile"
MAKEFILE = REPO_ROOT / "Makefile"

_NAME_RE = re.compile(r"^([A-Za-z0-9_.\-]+)")


def _normalize(name: str) -> str:
    return name.strip().lower().replace("_", "-")


def _parse_requirements(path: Path) -> tuple[list[str], list[str]]:
    """Return (package_names, includes) for a requirements file (comments stripped)."""
    names: list[str] = []
    includes: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("-r ") or line.startswith("--requirement "):
            includes.append(line.split(maxsplit=1)[1].strip())
            continue
        if line.startswith("-"):
            continue
        # Drop environment markers / extras before reading the package name.
        candidate = re.split(r"[<>=!~;\[]", line, maxsplit=1)[0]
        match = _NAME_RE.match(candidate.strip())
        if match:
            names.append(_normalize(match.group(1)))
    return names, includes


def _duplicates(names: list[str]) -> list[str]:
    seen: set[str] = set()
    dupes: set[str] = set()
    for name in names:
        if name in seen:
            dupes.add(name)
        seen.add(name)
    return sorted(dupes)


def test_runtime_manifest_has_no_duplicate_packages() -> None:
    names, _ = _parse_requirements(RUNTIME)
    assert not _duplicates(names), f"duplicate packages in requirements.txt: {_duplicates(names)}"


def test_dev_manifest_extends_runtime_and_has_no_duplicates() -> None:
    names, includes = _parse_requirements(DEV)
    assert "requirements.txt" in includes, "requirements-dev.txt must extend requirements.txt"
    assert not _duplicates(names), f"duplicate packages in requirements-dev.txt: {_duplicates(names)}"


def test_dev_manifest_does_not_redeclare_runtime_packages() -> None:
    runtime_names, _ = _parse_requirements(RUNTIME)
    dev_names, _ = _parse_requirements(DEV)
    overlap = sorted(set(runtime_names) & set(dev_names))
    assert not overlap, f"runtime packages re-declared in requirements-dev.txt: {overlap}"


def test_only_one_postgres_driver_is_declared() -> None:
    runtime_names, _ = _parse_requirements(RUNTIME)
    drivers = {"psycopg2-binary", "psycopg", "psycopg2"} & set(runtime_names)
    assert drivers == {"psycopg2-binary"}, (
        "exactly one synchronous PostgreSQL driver is expected (psycopg2-binary, "
        f"matching migrations/env.py); found {sorted(drivers) or 'none'}"
    )


def test_dockerfile_references_existing_files() -> None:
    text = DOCKERFILE.read_text(encoding="utf-8")
    referenced: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("COPY "):
            tokens = stripped.split()[1:]
            # Drop an optional --from=... flag and the destination argument.
            sources = [token for token in tokens if not token.startswith("--")]
            referenced.update(sources[:-1])
        for target in re.findall(r"-r\s+(\S+)", stripped):
            referenced.add(target)
    assert referenced, "expected the Dockerfile to reference at least one manifest"
    missing = sorted(name for name in referenced if not (BACKEND / name).exists())
    assert not missing, f"Dockerfile references missing files in the build context: {missing}"


def test_makefile_references_existing_manifests() -> None:
    text = MAKEFILE.read_text(encoding="utf-8")
    referenced = set(re.findall(r"([\w./\-]*requirements[\w./\-]*\.txt)", text))
    assert referenced, "expected the Makefile to reference at least one requirements file"
    missing = sorted(name for name in referenced if not (REPO_ROOT / name).exists())
    assert not missing, f"Makefile references missing requirements files: {missing}"
