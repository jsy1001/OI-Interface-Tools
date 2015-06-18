import unittest
import os
import tempfile

import numpy as np
from astropy.io import fits

from InitImg import MAS_TO_RAD
from HDUListPlus import HDUListPlus
from image_oi_input import create_parser, INPUT_PARAM_NAME, DEFAULT_PARAM


class ImageOiInputTestCase(unittest.TestCase):

    def setUp(self):
        self.parser = create_parser()
        self.tempResult = tempfile.NamedTemporaryFile(suffix='.fits',
                                                      delete=False)

    def tearDown(self):
        self.tempResult.close()
        os.remove(self.tempResult.name)

    def create(self, inputfile, naxis1=64, cdelt1=0.25, param=[]):
        """Create a temporary input file to read as part of a test"""
        args = self.parser.parse_args(['create', '--overwrite', inputfile,
                                       str(naxis1), str(cdelt1)] + param)
        args.func(args)

    def test_create_exists(self):
        """
        File exists and --overwrite not specified, should fail with SystemExit
        """
        args = self.parser.parse_args(['create', self.tempResult.name,
                                       '128', '0.5'])
        with self.assertRaises(SystemExit):
            args.func(args)

    def test_create(self):
        """Test create command"""
        naxis1 = 128
        cdelt1 = 0.5
        args = self.parser.parse_args(['create', '--overwrite',
                                       self.tempResult.name,
                                       str(naxis1), str(cdelt1), 'MAXITER=50'])
        args.func(args)
        with fits.open(self.tempResult.name) as hdulist:
            hdulist.__class__ = HDUListPlus
            param = hdulist[INPUT_PARAM_NAME].header
            imageHdu = hdulist[param['INIT_IMG']]
            self.assertEqual(param['NAXIS'], 2)
            self.assertEqual(imageHdu.header['NAXIS1'], naxis1)
            self.assertEqual(imageHdu.header['NAXIS2'], naxis1)
            self.assertAlmostEqual(imageHdu.header['CDELT1'],
                                   cdelt1 * MAS_TO_RAD)
            self.assertAlmostEqual(imageHdu.header['CDELT2'],
                                   cdelt1 * MAS_TO_RAD)
            for key, value in DEFAULT_PARAM:
                self.assertIsNotNone(param[key])
            self.assertEqual(param['MAXITER'], 50)

    def test_copyimage(self):
        """Test image copy from a second imaging input file"""
        naxis1 = 128
        self.create(self.tempResult.name, naxis1)
        tempImage = tempfile.NamedTemporaryFile(suffix='.fits', delete=False)
        self.create(tempImage.name, naxis1)
        args = self.parser.parse_args(['copyimage', self.tempResult.name,
                                       tempImage.name])
        args.func(args)
        tempImage.close()
        os.remove(tempImage.name)

    def test_copyimage_primary(self):
        """Test image copy from primary HDU (fallback behaviour)"""
        naxis1 = 128
        self.create(self.tempResult.name, naxis1)
        tempImage = tempfile.NamedTemporaryFile(suffix='.fits', delete=False)
        fits.PrimaryHDU(data=np.zeros((naxis1, naxis1))).writeto(tempImage)
        args = self.parser.parse_args(['copyimage', self.tempResult.name,
                                       tempImage.name])
        args.func(args)
        tempImage.close()
        os.remove(tempImage.name)

    def test_edit(self):
        """Test edit command"""
        self.create(self.tempResult.name, param=['MYKEY1=99.12'])
        args = self.parser.parse_args(['edit', self.tempResult.name,
                                       'MYKEY1=0.467', 'MYKEY2=foo'])
        args.func(args)
        with fits.open(self.tempResult.name) as hdulist:
            param = hdulist[INPUT_PARAM_NAME].header
            self.assertAlmostEqual(param['MYKEY1'], 0.467)
            self.assertEqual(param['MYKEY2'], 'foo')

    def test_show(self):
        """Test show command"""
        self.create(self.tempResult.name)
        args = self.parser.parse_args(['show', self.tempResult.name])
        args.func(args)


if __name__ == '__main__':
    unittest.main()
