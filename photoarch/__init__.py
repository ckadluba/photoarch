from importlib.metadata import PackageNotFoundError, version

from .main import cli, main as run

try:
    __version__ = version("photoarch")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = ["run", "cli", "__version__"]
