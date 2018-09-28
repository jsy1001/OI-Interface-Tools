import unittest
import os
import tempfile

import numpy as np
from astropy.io import fits

from imageoi.fitshelpers import HDUListPlus
from imageoi.initimage import MAS_TO_DEG
from imageoi.imagingfile import DEFAULT_PARAM, INPUT_PARAM_NAME
from imageoi.tool.__main__ import create_parser


class ImageOiToolTestCase(unittest.TestCase):

    def setUp(self):
        self.parser = create_parser()
        self.tempResult = tempfile.NamedTemporaryFile(suffix='.fits',
                                                      mode='wb', delete=False)
        self.datafile = 'tests/Bin_Ary--MIRC_H.fits'

    def tearDown(self):
        self.tempResult.close()
        os.remove(self.tempResult.name)

    def create(self, inputfile, naxis1=64, pixelsize=0.25, param=[]):
        """Create a temporary input file to read as part of a test"""
        args = self.parser.parse_args(['create', '--overwrite',
                                       self.datafile, inputfile,
                                       str(naxis1), str(pixelsize)] + param)
        args.func(args)

    def test_version(self):
        """Test '--version' argument"""
        with self.assertRaises(SystemExit) as cm:
            self.parser.parse_args(['--version'])
            self.assertEqual(cm.exception.code, 0)

    def test_create_exists(self):
        """
        File exists and --overwrite not specified, should fail with SystemExit
        """
        args = self.parser.parse_args(['create',
                                       self.datafile, self.tempResult.name,
                                       '128', '0.5'])
        with self.assertRaises(SystemExit):
            args.func(args)

    def test_create(self):
        """Test create command"""
        naxis1 = 128
        pixelsize = 0.5
        args = self.parser.parse_args(['create', '--overwrite',
                                       self.datafile, self.tempResult.name,
                                       str(naxis1), str(pixelsize),
                                       'MAXITER=50'])
        args.func(args)
        with fits.open(self.tempResult.name) as hdulist:
            hdulist.__class__ = HDUListPlus
            param = hdulist[INPUT_PARAM_NAME].header
            imageHdu = hdulist[param['INIT_IMG']]
            self.assertEqual(param['NAXIS'], 2)
            self.assertEqual(imageHdu.header['NAXIS1'], naxis1)
            self.assertEqual(imageHdu.header['NAXIS2'], naxis1)
            self.assertAlmostEqual(imageHdu.header['CDELT1'],
                                   pixelsize * MAS_TO_DEG)
            self.assertAlmostEqual(imageHdu.header['CDELT2'],
                                   pixelsize * MAS_TO_DEG)
            for key, value in DEFAULT_PARAM:
                self.assertIsNotNone(param[key])
            self.assertEqual(param['MAXITER'], 50)

    def test_copyinit(self):
        """Test initial image copy from primary HDU"""
        naxis1 = 128
        self.create(self.tempResult.name, naxis1)
        tempImage = tempfile.NamedTemporaryFile(suffix='.fits', mode='wb',
                                                delete=False)
        pri = fits.PrimaryHDU(data=np.ones((naxis1, naxis1)))
        pri.writeto(tempImage)
        args = self.parser.parse_args(['copyinit', self.tempResult.name,
                                       tempImage.name])
        args.func(args)
        tempImage.close()
        os.remove(tempImage.name)

        # Test destination image
        with fits.open(self.tempResult.name) as hdulist:
            hdulist.__class__ = HDUListPlus
            param = hdulist[INPUT_PARAM_NAME].header
            self.assertTrue(np.all(hdulist[param['INIT_IMG']].data ==
                                   pri.data / np.sum(pri.data)))

    def test_copyprior(self):
        """Test prior image copy from primary HDU"""
        naxis1 = 128
        self.create(self.tempResult.name, naxis1)
        tempImage = tempfile.NamedTemporaryFile(suffix='.fits', mode='wb',
                                                delete=False)
        pri = fits.PrimaryHDU(data=np.ones((naxis1, naxis1)))
        pri.writeto(tempImage)
        args = self.parser.parse_args(['copyprior', self.tempResult.name,
                                       tempImage.name])
        args.func(args)
        tempImage.close()
        os.remove(tempImage.name)

        # Test destination image
        with fits.open(self.tempResult.name) as hdulist:
            hdulist.__class__ = HDUListPlus
            param = hdulist[INPUT_PARAM_NAME].header
            self.assertTrue(np.all(hdulist[param['RGL_PRIO']].data ==
                                   pri.data / np.sum(pri.data)))

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
