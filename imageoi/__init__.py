"""The imageoi package."""

from pkg_resources import get_distribution, DistributionNotFound

try:
    __version__ = get_distribution("OI-Interface-Tools").version
except DistributionNotFound:
    # package is not installed
    pass
