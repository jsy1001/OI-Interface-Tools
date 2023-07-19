import os
import tempfile
import unittest

from astropy.io import fits
import numpy as np

from imageoi.fitshelpers import HDUListPlus


class HDUListPlusTestCase(unittest.TestCase):
    def setUp(self):
        self.tempFits = tempfile.NamedTemporaryFile(
            suffix=".fits", mode="wb", delete=False
        )
        pri = fits.PrimaryHDU(data=np.zeros((64, 64)))
        ext = fits.BinTableHDU()
        self.extname = "test_extname"
        self.extver = 2
        self.hduname = "test_hduname"
        self.hduver = 2
        ext.header["EXTNAME"] = self.extname
        ext.header["EXTVER"] = self.extver
        ext.header["HDUNAME"] = self.hduname
        ext.header["HDUVER"] = self.hduver
        hdulist = fits.HDUList([pri, ext])
        hdulist.writeto(self.tempFits)

    def tearDown(self):
        self.tempFits.close()
        os.remove(self.tempFits.name)

    def test_invalid_pos(self):
        """Position out of range, should fail with IndexError"""
        with fits.open(self.tempFits.name) as hdulist:
            hdulist.__class__ = HDUListPlus
            with self.assertRaises(IndexError):
                hdulist[2]

    def test_invalid_key(self):
        """No match for key, should fail with KeyError"""
        with fits.open(self.tempFits.name) as hdulist:
            hdulist.__class__ = HDUListPlus
            with self.assertRaises(KeyError):
                hdulist["notpresent"]

    def test_lookup_pos(self):
        """Test HDU lookup by position"""
        with fits.open(self.tempFits.name) as hdulist:
            hdulist.__class__ = HDUListPlus
            hdulist[0]

    def test_lookup_extname(self):
        """Test HDU lookup by EXTNAME alone"""
        with fits.open(self.tempFits.name) as hdulist:
            hdulist.__class__ = HDUListPlus
            hdulist[self.extname]

    def test_lookup_extname_ver(self):
        """Test HDU lookup by (EXTNAME, EXTVER)"""
        with fits.open(self.tempFits.name) as hdulist:
            hdulist.__class__ = HDUListPlus
            hdulist[self.extname, self.extver]

    def test_lookup_hduname(self):
        """Test HDU lookup by HDUNAME alone"""
        with fits.open(self.tempFits.name) as hdulist:
            hdulist.__class__ = HDUListPlus
            hdulist[self.hduname]

    def test_lookup_hduname_ver(self):
        """Test HDU lookup by (HDUNAME, HDUVER)"""
        with fits.open(self.tempFits.name) as hdulist:
            hdulist.__class__ = HDUListPlus
            hdulist[self.hduname, self.hduver]


if __name__ == "__main__":
    unittest.main()
