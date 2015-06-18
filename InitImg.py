"""Python module to create initial images for OI image reconstruction.

A grey initial image is represented by the InitImg class.

Attributes:
  MAS_TO_RAD (float): Conversion factor from milliarcseconds to radians.

"""

from __future__ import division

from math import pi, exp, log
import os

import numpy as np
from astropy.io import fits
from astropy import wcs

MAS_TO_RAD = pi/180/3600/1000


class InitImg(object):

    """OI image reconstruction initial image class.

    Args:
      name (str): Name of image, written as FITS HDUNAME keyword.
      naxis1 (int): First (fast) dimension of image (FITS ordering).
      naxis2 (int): Second (slow) dimension of image (FITS ordering).

    Attributes:
      name (str): Name of image, written as FITS HDUNAME keyword.
      naxis1 (int): First (fast) dimension of image (FITS ordering).
      naxis2 (int): Second (slow) dimension of image (FITS ordering).
      image (ndarray): The image pixel data as a numpy array
                       of shape (naxis2, naxis1).

    Examples:
      The following creates a blank 64 by 32 image:

      >>> img = InitImg('test', 64, 32)
      >>> img.name
      'test'
      >>> type(img.image) == np.ndarray
      True
      >>> img.naxis1
      64
      >>> img.naxis2
      32
      >>> img.isSquare()
      False
      >>> img.image.shape
      (32, 64)
      >>> np.all(img.image == 0.0)
      True

    """

    def __init__(self, name, naxis1, naxis2):
        self.name = name
        self.naxis1 = naxis1
        self.naxis2 = naxis2
        self.image = np.zeros((naxis2, naxis1), np.float)  # axes are slow,fast
        self._wcs = wcs.WCS(naxis=2)

    def setWCS(self, **kwargs):
        """Set World Coordinate System attributes.

        Sets astropy.wcs.Wcsprm attributes supplied using
        kwargs. Important WCS attributes you might wish to set include
        cdelt, crpix, crval and cunit.

        Example:

        >>> img = InitImg('test', 64, 64)
        >>> img.setWCS(cdelt=[0.25 * MAS_TO_RAD, 0.25 * MAS_TO_RAD])

        """
        for key, value in kwargs.iteritems():
            setattr(self._wcs.wcs, key, value)

    def isSquare(self):
        """Does image have the same dimension in both axes?"""
        return self.naxis1 == self.naxis2

    def makePrimaryHDU(self):
        """Create a new PrimaryHDU instance from the current image.

        Examples:
          The following uses this method to create a FITS image file:

          >>> img = InitImg('test', 64, 64)
          >>> img.makePrimaryHDU().writeto('utest.fits')
          >>> hlist = fits.open('utest.fits')
          >>> np.all(hlist[0].data == img.image)
          True
          >>> os.remove('utest.fits')

        """
        hdu = fits.PrimaryHDU(data=self.image, header=self._wcs.to_header())
        hdu.header['HDUNAME'] = self.name
        # EXTNAME not allowed in primary header
        return hdu

    def makeImageHDU(self):
        """Create a new ImageHDU instance from the current image."""
        hdu = fits.ImageHDU(data=self.image, header=self._wcs.to_header())
        hdu.header['HDUNAME'] = self.name
        hdu.header['EXTNAME'] = self.name
        return hdu

    def normalise(self):
        """Normalise the current image to unit sum.

        Example:

        >>> img = InitImg('test', 64, 64)
        >>> img.addGaussian(12.0, 37.0, 0.5, 40)
        >>> img.normalise()
        >>> np.abs(np.sum(img.image) - 1.0) < 1e-6
        True

        """
        self.image /= np.sum(self.image)

    def addGaussian(self, x, y, flux, fwhm):
        """Add a circular Gaussian component to the current image.

        Args:
          x (float): Component position on first (fast) FITS axis.
          y (float): Component position on second (slow) FITS axis.
          flux (float): Integrated flux of component.
          fwhm (float): Full width at half maximum intensity.

        Example:

        >>> img = InitImg('test', 64, 64)
        >>> img.addGaussian(12.0, 37.0, 0.5, 5)
        >>> np.all(np.argmax(img.image, axis=1) == 12)
        True
        >>> np.all(np.argmax(img.image, axis=0) == 37)
        True
        >>> np.abs(np.sum(img.image) - 0.5) < 1e-6
        True

        """
        peak = flux * 4 * log(2) / (pi * fwhm**2)
        for iy in range(self.naxis2):
            for ix in range(self.naxis1):
                rsq = (ix - x)**2 + (iy - y)**2
                self.image[iy][ix] = peak * exp(-4 * log(2) * rsq / fwhm**2)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
