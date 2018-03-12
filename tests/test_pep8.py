import unittest
import pep8
import os.path

from glob import glob


class TestCodeFormat(unittest.TestCase):

    def test_pep8_conformance(self):
        """Test that we conform to PEP8."""
        pep8style = pep8.StyleGuide(quiet=True)
        currdir = os.path.dirname(os.path.abspath(__file__))
        tocheck = os.path.join(currdir, '..', 'imageoi', '*.py')
        result = pep8style.check_files(glob(tocheck))
        self.assertEqual(result.total_errors, 0,
                         "Found code style errors (and warnings).")


if __name__ == '__main__':
    unittest.main()
