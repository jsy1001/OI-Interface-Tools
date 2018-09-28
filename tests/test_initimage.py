import doctest
import imageoi.initimage


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(imageoi.initimage))
    return tests
