import unittest

from imageoi.imagingfile import ImagingFile, INPUT_PARAM_NAME, DEFAULT_PARAM


class ImagingFileTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_create_nodata(self):
        """Create a useless input file object without OIFITS data"""
        inp = ImagingFile()
        self.assertTrue(repr(inp).startswith("ImagingFile("))
        self.assertEqual(len(inp.datatables), 0)
        self.assertEqual(inp.inparam["EXTNAME"], INPUT_PARAM_NAME)
        self.assertIsNone(inp.initimg)
        self.assertIsNone(inp.priorimg)
        with self.assertRaises(KeyError):
            inp.inparam["INIT_IMG"]
            inp.inparam["RGL_PRIO"]
        self.assertIsNone(inp.inparam["TARGET"])
        self.assertIsInstance(inp.inparam["WAVE_MIN"], float)
        self.assertIsInstance(inp.inparam["WAVE_MAX"], float)
        self.assertIsInstance(inp.inparam["USE_VIS"], str)
        self.assertIsInstance(inp.inparam["USE_VIS2"], bool)
        self.assertIsInstance(inp.inparam["USE_T3"], str)
        usechoices = ("NONE", "ALL", "AMP", "PHI")
        self.assertIn(inp.inparam["USE_VIS"], usechoices)
        self.assertIn(inp.inparam["USE_T3"], usechoices)
        self.assertIsInstance(inp.inparam["MAXITER"], int)
        self.assertIsInstance(inp.inparam["RGL_NAME"], str)
        self.assertIsInstance(inp.inparam["AUTO_WGT"], bool)
        self.assertIsInstance(inp.inparam["RGL_WGT"], float)
        self.assertIsInstance(inp.inparam["FLUX"], float)
        self.assertIsInstance(inp.inparam["FLUXERR"], float)
        for key, value in DEFAULT_PARAM:
            self.assertTrue(value is None or inp.inparam[key] == value)


if __name__ == "__main__":
    unittest.main()
