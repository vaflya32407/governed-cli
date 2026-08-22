"""governed-cli package."""

from importlib.metadata import PackageNotFoundError, version

__all__ = ["__version__"]

try:
    __version__ = version("governed-cli")
except PackageNotFoundError:  # pragma: no cover - fallback for local execution before install
    __version__ = "0.1.0"
