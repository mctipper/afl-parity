"""Single source of truth for the project's on-disk locations."""

from pathlib import Path

# hop count is from this file's own location, so don't move it deeper
# afl_parity -> src -> repository root
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

OUTPUT_DIR: Path = PROJECT_ROOT / "output"
LOGS_DIR: Path = PROJECT_ROOT / ".logs"

__all__ = ["PROJECT_ROOT", "OUTPUT_DIR", "LOGS_DIR"]
