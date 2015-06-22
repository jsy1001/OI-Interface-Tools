"""Python module to create initial images for OI image reconstruction.

A grey initial image is represented by the InitImg class.

Attributes:
  MAS_TO_DEG (float): Conversion factor from milliarcseconds to degrees.

"""

from __future__ import division

from math import pi, exp, log
import os

import numpy as np
from astropy.io import fits
from astropy import wcs

from HDUListPlus import HDUListPlus

MAS_TO_DEG = 1/3600/1000
INPUT_PARAM_NAME = 'IMAGE-OI INPUT PARAM'


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

      The following creates an InitImg instance from an existing
      FITS file (itself made from an InitImg):

      >>> img1 = InitImg('test', 64, 32)
      >>> img1.makePrimaryHDU().writeto('tmp.fits')
      >>> img2 = InitImg.fromImageFilename('tmp.fits')
      >>> assert img1.name == img2.name
      >>> assert img1.naxis1 == img2.naxis1
      >>> assert img1.naxis2 == img2.naxis2
      >>> assert np.all(img1.image == img2.image)
      >>> os.remove('tmp.fits')

    """

    def __init__(self, name, naxis1, naxis2):
        self.name = name
        self.naxis1 = naxis1
        self.naxis2 = naxis2
        self.image = np.zeros((naxis2, naxis1), np.float)  # axes are slow,fast
        self._wcs = wcs.WCS(naxis=2)

    @classmethod
    def fromImageFilename(cls, filename):
        """Initialize InitImg from a FITS image file."""
        with fits.open(filename) as hdulist:
            imageHdu = hdulist[0]
            try:
                name = imageHdu.header['HDUNAME']
            except KeyError:
                name = os.path.split(os.path.basename(filename))[0]
            naxis1 = imageHdu.data.shape[1]
            naxis2 = imageHdu.data.shape[0]
            self = cls(name, naxis1, naxis2)
            self.image = imageHdu.data
            # :TODO: set WCS keywords from file?
            return self

    @classmethod
    def fromInputFilename(cls, filename):
        """Initialize InitImg from an image reconstruction input file."""
        with fits.open(filename) as hdulist:
            hdulist.__class__ = HDUListPlus
            param = hdulist[INPUT_PARAM_NAME].header
            imageHdu = hdulist[param['INIT_IMG']]
            if (type(imageHdu) is not fits.ImageHDU and
                    type(imageHdu) is not fits.PrimaryHDU):
                msg = "HDU referenced by INIT_IMG is not an image HDU."
                raise TypeError(msg)
            name = imageHdu.header['HDUNAME']
            naxis1 = imageHdu.data.shape[1]
            naxis2 = imageHdu.data.shape[0]
            self = cls(name, naxis1, naxis2)
            self.image = imageHdu.data
            # :TODO: set WCS keywords from file?
            return self

    def setWCS(self, **kwargs):
        """Set World Coordinate System attributes.

        Sets astropy.wcs.Wcsprm attributes supplied using
        kwargs. Important WCS attributes you might wish to set include
        cdelt, crpix, crval and cunit.

        Example:

        >>> img = InitImg('test', 64, 64)
        >>> img.setWCS(cdelt=[0.25 * MAS_TO_DEG, 0.25 * MAS_TO_DEG])

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

    def addDirac(self, x, y, flux):
        """Add a delta function component to the current image.

        Args:
          x (float): Component position on first (fast) FITS axis.
          y (float): Component position on second (slow) FITS axis.
          flux (float): Integrated flux of component.

        Example:

        >>> img = InitImg('test', 64, 64)
        >>> img.addDirac(12.0, 37.0, 0.5)
        >>> max1 = np.zeros((64,))
        >>> max1[37] = 12
        >>> np.all(np.argmax(img.image, axis=1) == max1)
        True
        >>> max0 = np.zeros((64,))
        >>> max0[12] = 37
        >>> np.all(np.argmax(img.image, axis=0) == max0)
        True
        >>> img.addDirac(13.5, 42.8, 0.25)
        >>> np.abs(np.sum(img.image) - 0.75) < 1e-6
        True

        """
        self.image[np.rint(y)][np.rint(x)] += flux

    def addUniformDisk(self, x, y, flux, diameter):
        """Add a circular uniform disk component to the current image.

        Args:
          x (float): Component position on first (fast) FITS axis.
          y (float): Component position on second (slow) FITS axis.
          flux (float): Integrated flux of component.
          diameter (float): Disk diameter.

        Example:

        >>> img = InitImg('test', 64, 64)
        >>> img.addUniformDisk(12.0, 37.0, 0.5, 11)
        >>> img.addUniformDisk(13.5, 42.8, 0.25, 11)
        >>> np.abs(np.sum(img.image) - 0.75) < 1e-2
        True

        """
        radius = diameter / 2
        area = pi * radius**2
        for iy in range(self.naxis2):
            for ix in range(self.naxis1):
                r = np.sqrt((ix - x)**2 + (iy - y)**2)
                if r <= radius:
                    self.image[iy][ix] += flux / area

    def addGaussian(self, x, y, flux, fwhm):
        """Add a circular Gaussian component to the current image.

        Args:
          x (float): Component position on first (fast) FITS axis.
          y (float): Component position on second (slow) FITS axis.
          flux (float): Integrated flux of component (to infinite limits).
          fwhm (float): Full width at half maximum intensity.

        Example:

        >>> img = InitImg('test', 64, 64)
        >>> img.addGaussian(12.0, 37.0, 0.5, 5)
        >>> np.all(np.argmax(img.image, axis=1) == 12)
        True
        >>> np.all(np.argmax(img.image, axis=0) == 37)
        True
        >>> img.addGaussian(11.2, 23.6, 0.25, 5)
        >>> np.abs(np.sum(img.image) - 0.75) < 1e-6
        True

        """
        peak = flux * 4 * log(2) / (pi * fwhm**2)
        for iy in range(self.naxis2):
            for ix in range(self.naxis1):
                rsq = (ix - x)**2 + (iy - y)**2
                self.image[iy][ix] += peak * exp(-4 * log(2) * rsq / fwhm**2)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
