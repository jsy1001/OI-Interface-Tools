import doctest
import imageoi.initimage


def load_tests(loader, tests, ignore):
    """Load doctests."""
    tests.addTests(doctest.DocTestSuite(imageoi.initimage))
    return tests
