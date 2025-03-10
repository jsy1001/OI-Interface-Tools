"""Top-level package for OI Interface Tools."""

from importlib.metadata import PackageNotFoundError, version

__author__ = """John Young"""
__email__ = "jsy1001@cam.ac.uk"

try:
    __version__ = version("OI-Interface-Tools")
except PackageNotFoundError:
    # package is not installed
    pass
