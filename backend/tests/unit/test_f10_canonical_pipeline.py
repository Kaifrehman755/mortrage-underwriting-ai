"""F-10 regression tests: exactly one canonical valuation engine and ORM tree.

Verifies (Phase 2, Priority 5 — F-10):
1. The canonical-pipeline decision is documented.
2. The live entry points reference the canonical engine (``app.property.valuation``).
3. No live entry point imports the non-canonical engine (``app.valuation``) — so exactly one
   engine is wired at a time.
4. Alembic targets the canonical ORM tree (``app.database.models``).
5. No live entry point imports the deprecated legacy tree (``app.models``).
6. Importing the legacy package emits a ``DeprecationWarning``.

Evidence method: an AST scan of the importing modules' source, not a runtime import, so the test
also covers modules that are not otherwise imported during the suite.
"""

from __future__ import annotations

import ast
import importlib
import sys
import warnings
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND = REPO_ROOT / "backend"
DECISION_DOC = REPO_ROOT / "docs" / "architecture" / "canonical_pipeline.md"

CANONICAL_ENGINE = "app.property.valuation"
NON_CANONICAL_ENGINE = "app.valuation"
CANONICAL_ORM = "app.database.models"
LEGACY_ORM = "app.models"

LIVE_ENTRY_POINTS = [
    BACKEND / "app" / "main.py",
    BACKEND / "app" / "agents" / "property_agent.py",
    BACKEND / "app" / "property" / "__init__.py",
    REPO_ROOT / "migrations" / "env.py",
    *sorted((BACKEND / "app" / "api").glob("*.py")),
]


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def _matches(modules: set[str], target: str) -> bool:
    return any(module == target or module.startswith(f"{target}.") for module in modules)


def test_canonical_decision_is_documented() -> None:
    assert DECISION_DOC.exists(), "F-10 requires the canonical designation to be documented"
    text = DECISION_DOC.read_text(encoding="utf-8")
    for required in ("app/property", "app/valuation", "app/database/models", "app/models"):
        assert required in text, f"decision record does not mention {required}"


def test_live_entry_points_use_canonical_engine() -> None:
    agent_modules = _imported_modules(BACKEND / "app" / "agents" / "property_agent.py")
    assert _matches(agent_modules, CANONICAL_ENGINE), (
        "PropertyAgent must use the canonical engine"
    )


def test_no_live_entry_point_imports_the_non_canonical_engine() -> None:
    offenders = [
        str(path.relative_to(REPO_ROOT))
        for path in LIVE_ENTRY_POINTS
        if _matches(_imported_modules(path), NON_CANONICAL_ENGINE)
    ]
    assert not offenders, f"live entry points must not import {NON_CANONICAL_ENGINE}: {offenders}"


def test_exactly_one_valuation_engine_is_live() -> None:
    live_engines = set()
    for path in LIVE_ENTRY_POINTS:
        modules = _imported_modules(path)
        for engine in (CANONICAL_ENGINE, NON_CANONICAL_ENGINE):
            if _matches(modules, engine):
                live_engines.add(engine)
    assert live_engines == {CANONICAL_ENGINE}, f"unexpected live engines: {live_engines}"


def test_migrations_target_the_canonical_orm_tree() -> None:
    env_modules = _imported_modules(REPO_ROOT / "migrations" / "env.py")
    assert _matches(env_modules, CANONICAL_ORM), (
        "migrations/env.py must target the canonical ORM tree"
    )


def test_no_live_entry_point_imports_the_legacy_orm_tree() -> None:
    offenders = [
        str(path.relative_to(REPO_ROOT))
        for path in LIVE_ENTRY_POINTS
        if _matches(_imported_modules(path), LEGACY_ORM)
    ]
    assert not offenders, f"live entry points must not import the legacy tree: {offenders}"


def test_legacy_models_package_warns_on_import() -> None:
    sys.modules.pop(LEGACY_ORM, None)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        module = importlib.import_module(LEGACY_ORM)
    assert module is not None
    assert any(issubclass(record.category, DeprecationWarning) for record in caught), (
        "importing app.models must emit a DeprecationWarning (F-10 marker)"
    )
