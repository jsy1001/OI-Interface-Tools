import unittest
import os
import tempfile

from astropy.io import fits

from imageoi.initimage import MAS_TO_DEG
from imageoi.imgen.__main__ import create_parser, generate


class ImgenTestCase(unittest.TestCase):

    def setUp(self):
        self.parser = create_parser()
        self.tempResult = tempfile.NamedTemporaryFile(suffix='.fits',
                                                      delete=False)

    def tearDown(self):
        self.tempResult.close()
        os.remove(self.tempResult.name)

    def test_version(self):
        """Test '--version' argument"""
        with self.assertRaises(SystemExit) as cm:
            self.parser.parse_args(['--version'])
            self.assertEqual(cm.exception.code, 0)

    def test_generate_exists(self):
        """
        File exists and --overwrite not specified, should fail with SystemExit
        """
        args = self.parser.parse_args([self.tempResult.name, '128', '0.5'])
        with self.assertRaises(SystemExit):
            generate(args)

    def test_generate(self):
        """Test image generation"""
        naxis1 = 128
        pixelsize = 0.5
        args = self.parser.parse_args(['--overwrite', self.tempResult.name,
                                       str(naxis1), str(pixelsize)])
        generate(args)
        with fits.open(self.tempResult.name) as hdulist:
            imageHdu = hdulist[0]
            self.assertEqual(imageHdu.header['NAXIS1'], naxis1)
            self.assertEqual(imageHdu.header['NAXIS2'], naxis1)
            self.assertAlmostEqual(imageHdu.header['CDELT1'],
                                   pixelsize * MAS_TO_DEG)
            self.assertAlmostEqual(imageHdu.header['CDELT2'],
                                   pixelsize * MAS_TO_DEG)

    def test_ld(self):
        """Test Hestroffer limb-darkened disk"""
        naxis1 = 128
        pixelsize = 0.5
        args = self.parser.parse_args(['--overwrite', self.tempResult.name,
                                       str(naxis1), str(pixelsize), '-mt=ld'])
        generate(args)
        args = self.parser.parse_args(['--overwrite', self.tempResult.name,
                                       str(naxis1), str(pixelsize), '-mt=ld',
                                       '-mw=10.5'])
        generate(args)
        args = self.parser.parse_args(['--overwrite', self.tempResult.name,
                                       str(naxis1), str(pixelsize), '-mt=ld',
                                       '-mw=13.2', '--ldalpha=2.0'])
        generate(args)


if __name__ == '__main__':
    unittest.main()
