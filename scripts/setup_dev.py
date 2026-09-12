"""Development environment verification and storage directory initialization script."""

import sys
from pathlib import Path

# Base directories to ensure exist
REQUIRED_DIRS = [
    Path("storage/uploads"),
    Path("storage/processed"),
    Path("storage/reports"),
    Path("data/sample_documents"),
    Path("data/regulatory_docs"),
    Path("data/test_cases"),
    Path("data/ground_truth"),
]


def ensure_directories():
    """Create all required local storage and data directories if missing."""
    print("[DIR] Checking required directories...")
    for directory in REQUIRED_DIRS:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"  + {directory}")


def check_python_version():
    """Verify minimum Python version."""
    print("\n[PYTHON] Checking Python runtime...")
    major, minor = sys.version_info[:2]
    print(f"  Detected Python version: {major}.{minor}")
    if major < 3 or (major == 3 and minor < 11):
        print("  [!] Python 3.11+ is recommended.")
        return False
    print("  [OK] Python version meets requirements (3.11+).")
    return True


def check_env_file():
    """Check if .env exists; if not, create it from .env.example."""
    print("\n[ENV] Checking environment configuration...")
    env_file = Path(".env")
    example_file = Path(".env.example")

    if not env_file.exists():
        if example_file.exists():
            env_file.write_text(example_file.read_text(encoding="utf-8"), encoding="utf-8")
            print("  [OK] Created .env from .env.example template.")
        else:
            print("  [!] .env.example not found.")
    else:
        print("  [OK] .env file already exists.")


def main():
    print("=" * 60)
    print(" Mortgage Underwriting AI - Environment Setup Assistant")
    print("=" * 60)
    ensure_directories()
    check_python_version()
    check_env_file()
    print("\n[SUCCESS] Setup check completed successfully!\n")


if __name__ == "__main__":
    main()
