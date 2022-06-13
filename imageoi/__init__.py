"""Top-level package for OI Interface Tools."""

from pkg_resources import DistributionNotFound, get_distribution

__author__ = """John Young"""
__email__ = "jsy1001@cam.ac.uk"

try:
    __version__ = get_distribution("OI-Interface-Tools").version
except DistributionNotFound:
    # package is not installed
    pass
