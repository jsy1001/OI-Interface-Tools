"""Python module to create input images for OI image reconstruction.

A grey initial or prior image is represented by an instance of the
GreyImg class.

Attributes:
  MAS_TO_DEG (float): Conversion factor from milliarcseconds to degrees.
  INPUT_PARAM_NAME (str): EXTNAME of input parameters HDU.
  OUTPUT_PARAM_NAME (str): EXTNAME of output parameters HDU.

"""

from math import pi, exp, log

import numpy as np
from astropy.io import fits
from astropy import wcs

from imageoi.HDUListPlus import HDUListPlus

MAS_TO_DEG = 1/3600/1000
INPUT_PARAM_NAME = 'IMAGE-OI INPUT PARAM'
OUTPUT_PARAM_NAME = 'IMAGE-OI OUTPUT PARAM'


class GreyImg(object):
    """OI image reconstruction greyscale image class.

    Args:
      name (str): Name of image, written as FITS HDUNAME keyword.
      naxis1 (int): First (fast) dimension of image (FITS ordering).
      naxis2 (int): Second (slow) dimension of image (FITS ordering).
      pixelsize (float): Image pixel size in milliarcseconds.
      wcsheader: FITS header keywords to initialize internal
                 astropy.wcs.WCS object, optional.

    Raises:
      ValueError: CDELT1 in wcsheader inconsistent with pixelsize argument.

    Attributes:
      name (str): Name of image, written as FITS HDUNAME keyword.
      naxis1 (int): First (fast) dimension of image (FITS ordering).
      naxis2 (int): Second (slow) dimension of image (FITS ordering).
      pixelsize (float): Image pixel size in milliarcseconds.
      image (ndarray): The image pixel data as a numpy array
                       of shape (naxis2, naxis1).

    Examples:
      The following creates a blank 64 by 32 image:

      >>> import numpy as np
      >>> from imageoi.GreyImg import GreyImg
      >>> img = GreyImg('test', 64, 32, 0.25)
      >>> assert repr(img).startswith('GreyImg(')
      >>> img.name
      'test'
      >>> type(img.image) == np.ndarray
      True
      >>> img.naxis1
      64
      >>> img.naxis2
      32
      >>> img.pixelsize
      0.25
      >>> img.issquare()
      False
      >>> img.image.shape
      (32, 64)
      >>> np.all(img.image == 0.0)
      True

    """

    def __init__(self, name, naxis1, naxis2, pixelsize, wcsheader=None):
        self.name = name
        self.naxis1 = naxis1
        self.naxis2 = naxis2
        # note _image axes are slow, fast
        self._image = np.zeros((naxis2, naxis1), np.float)
        if (wcsheader is not None and
                wcsheader['CDELT1'] != pixelsize * MAS_TO_DEG):
            raise ValueError("CDELT1 inconsistent with pixelsize argument")
        self._wcs = wcs.WCS(header=wcsheader, naxis=2)
        self._wcs.wcs.cdelt = [pixelsize * MAS_TO_DEG,
                               pixelsize * MAS_TO_DEG]

    @classmethod
    def _fromimagehdu(cls, imghdu):
        """Initialise GreyImg from a FITS primary or image HDU.

        Args:
          imghdu (fits.PrimaryHDU or fits.ImageHDU): FITS HDU to read.

        Raises:
          KeyError: WCS keywords giving pixelsize are missing.
          ValueError: Image does not have square pixels.

        """
        name = imghdu.header['HDUNAME']
        naxis1 = imghdu.data.shape[1]
        naxis2 = imghdu.data.shape[0]
        try:
            cdelt1 = imghdu.header['CDELT1']
            cdelt2 = imghdu.header['CDELT2']
        except KeyError:
            raise KeyError("CDELT1/2 keywords missing, pixelsize unknown")
        if cdelt1 != cdelt2:
            raise ValueError("Image pixels are not square " +
                             "(CDELT1=%f, CDELT2=%f)" % (cdelt1, cdelt2))
        self = cls(name, naxis1, naxis2, cdelt1 / MAS_TO_DEG, imghdu.header)
        self.image = imghdu.data
        return self

    @classmethod
    def frominputfilename(cls, filename, hdunamekey='INIT_IMG'):
        """Initialise GreyImg from an image reconstruction input file.

        Args:
           filename (str): FITS file to read.
           hdunamekey (str): Input parameter keyword giving HDUNAME of image.

        Raises:
          TypeError: HDU referenced by INIT_IMG parameter is not an image HDU.
          KeyError: WCS keywords giving pixelsize are missing.
          ValueError: Image does not have square pixels.

        """
        with fits.open(filename) as hdulist:
            hdulist.__class__ = HDUListPlus
            param = hdulist[INPUT_PARAM_NAME].header
            imghdu = hdulist[param[hdunamekey]]
            if not isinstance(imghdu, (fits.PrimaryHDU, fits.ImageHDU)):
                raise TypeError("Not an image HDU: '%s' referenced by %s" %
                                (param[hdunamekey], hdunamekey))
            return cls._fromimagehdu(imghdu)

    @classmethod
    def fromoutputfilename(cls, filename, hdunamekey='LAST_IMG'):
        """Initialise GreyImg from an image reconstruction output file.

        Args:
           filename (str): FITS file to read.
           hdunamekey (str): Output parameter keyword giving HDUNAME of image.

        Raises:
          TypeError: HDU referenced by LAST_IMG parameter is not an image HDU.
          KeyError: WCS keywords giving pixelsize are missing.
          ValueError: Image does not have square pixels.

        """
        with fits.open(filename) as hdulist:
            hdulist.__class__ = HDUListPlus
            param = hdulist[OUTPUT_PARAM_NAME].header
            imghdu = hdulist[param[hdunamekey]]
            if not isinstance(imghdu, (fits.PrimaryHDU, fits.ImageHDU)):
                raise TypeError("Not an image HDU: '%s' referenced by %s" %
                                (param[hdunamekey], hdunamekey))
            return cls._fromimagehdu(imghdu)

    def setwcs(self, **kwargs):
        """Set World Coordinate System attributes.

        Sets astropy.wcs.Wcsprm attributes supplied using
        kwargs. Important WCS attributes you might wish to set include
        ctype, crpix, crval and cunit. Note that the cdelt attribute
        is set when the GreyImg object is constructed.

        Example:

        >>> from astropy.io import fits
        >>> from imageoi.GreyImg import GreyImg
        >>> img = GreyImg('test', 64, 64, 0.25)
        >>> img.setwcs(ctype=['RA', 'DEC'])
        >>> img.make_primary_hdu().writeto('utest.fits', overwrite=True)
        >>> hdulist = fits.open('utest.fits')
        >>> hdulist[0].header['CTYPE1']
        'RA'
        >>> hdulist[0].header['CTYPE2']
        'DEC'
        >>> hdulist.close()
        >>> import os
        >>> os.remove('utest.fits')

        """
        for key, value in kwargs.items():
            setattr(self._wcs.wcs, key, value)

    @property
    def image(self):
        """Return image pixel data as a numpy array."""
        return self._image

    @image.setter
    def image(self, data):
        """Set image pixel data.

        Args:
          data (ndarray): Replacement image.

        Raises:
          ValueError: shape of data doesn't match existing image dimensions.

        Example:

        >>> import numpy as np
        >>> from imageoi.GreyImg import GreyImg
        >>> img = GreyImg('test', 64, 64, 0.25)
        >>> img.image = np.zeros((64, 64))

        """
        if data.shape != self._image.shape:
            raise ValueError("Shape doesn't match existing image dims: " +
                             "expected %s but got %s" %
                             (self._image.shape, data.shape))
        self._image = np.array(data)

    @property
    def pixelsize(self):
        """Return pixel size in mas."""
        assert self._wcs.wcs.cdelt[0] == self._wcs.wcs.cdelt[1]
        return self._wcs.wcs.cdelt[0] / MAS_TO_DEG

    def __repr__(self):
        ret = "GreyImg("
        ret += ("name=%r, naxis1=%r, naxis2=%r, pixelsize=%r" %
                (self.name, self.naxis1, self.naxis2, self.pixelsize))
        ret += ")"
        return ret

    def issquare(self):
        """Check whether image has the same dimension in both axes."""
        return self.naxis1 == self.naxis2

    def make_primary_hdu(self):
        """Create a new fits.PrimaryHDU instance from the current image.

        Examples:
          The following uses this method to create a FITS image file:

          >>> from astropy.io import fits
          >>> from imageoi.GreyImg import GreyImg
          >>> img = GreyImg('test', 64, 64, 0.25)
          >>> img.make_primary_hdu().writeto('utest.fits', overwrite=True)
          >>> hdulist = fits.open('utest.fits')
          >>> len(hdulist)
          1
          >>> hdulist[0].header['HDUNAME']
          'test'
          >>> hdulist[0].header['EXTNAME']
          Traceback (most recent call last):
              ...
          KeyError: "Keyword 'EXTNAME' not found."
          >>> np.all(hdulist[0].data == img.image)
          True
          >>> hdulist.close()
          >>> import os
          >>> os.remove('utest.fits')

        """
        hdu = fits.PrimaryHDU(data=self.image, header=self._wcs.to_header())
        hdu.header['HDUNAME'] = self.name
        # EXTNAME not allowed in primary header
        return hdu

    def make_image_hdu(self):
        """Create a new fits.ImageHDU instance from the current image.

        Examples:

          The following uses this method to create a FITS file
          containing two HDUs, a dummy primary HDU and a 64 by 64
          image HDU:

          >>> import numpy as np
          >>> from astropy.io import fits
          >>> from imageoi.GreyImg import GreyImg
          >>> img = GreyImg('test', 64, 64, 0.25)
          >>> hdulist = fits.HDUList(fits.PrimaryHDU())
          >>> hdulist.append(img.make_image_hdu())
          >>> hdulist.writeto('utest.fits', overwrite=True)
          >>> hdulist = fits.open('utest.fits')
          >>> len(hdulist)
          2
          >>> hdulist[1].header['HDUNAME']
          'test'
          >>> hdulist[1].header['EXTNAME']
          'test'
          >>> np.all(hdulist[1].data == img.image)
          True
          >>> hdulist.close()
          >>> import os
          >>> os.remove('utest.fits')

        """
        hdu = fits.ImageHDU(data=self.image, header=self._wcs.to_header())
        hdu.header['HDUNAME'] = self.name
        hdu.header['EXTNAME'] = self.name
        return hdu

    def normalise(self):
        """Normalise the current image to unit sum.

        Example:

        >>> import numpy as np
        >>> from imageoi.GreyImg import GreyImg
        >>> img = GreyImg('test', 64, 64, 0.25)
        >>> img.add_gaussian(12.0, 37.0, 0.5, 40)
        >>> img.normalise()
        >>> np.abs(np.sum(img.image) - 1.0) < 1e-6
        True

        """
        total = np.sum(self.image)
        if np.fabs(total) > 0:
            self.image /= total

    def add_dirac(self, xpos, ypos, flux):
        """Add a delta function component to the current image.

        Args:
          xpos (float): Component position on first (fast) FITS axis /pix.
          ypos (float): Component position on second (slow) FITS axis /pix.
          flux (float): Integrated flux of component.

        Example:

        >>> import numpy as np
        >>> from imageoi.GreyImg import GreyImg
        >>> img = GreyImg('test', 64, 64, 0.25)
        >>> img.add_dirac(12.0, 37.0, 0.5)
        >>> max1 = np.zeros((64,))
        >>> max1[37] = 12
        >>> np.all(np.argmax(img.image, axis=1) == max1)
        True
        >>> max0 = np.zeros((64,))
        >>> max0[12] = 37
        >>> np.all(np.argmax(img.image, axis=0) == max0)
        True
        >>> img.add_dirac(13.5, 42.8, 0.25)
        >>> np.abs(np.sum(img.image) - 0.75) < 1e-6
        True

        """
        self.image[int(np.rint(ypos))][int(np.rint(xpos))] += flux

    def add_uniform_disk(self, xpos, ypos, flux, diameter):
        """Add a circular uniform disk component to the current image.

        Args:
          xpos (float): Component position on first (fast) FITS axis /pix.
          ypos (float): Component position on second (slow) FITS axis /pix.
          flux (float): Integrated flux of component.
          diameter (float): Disk diameter /pix.

        Example:

        >>> import numpy as np
        >>> from imageoi.GreyImg import GreyImg
        >>> img = GreyImg('test', 64, 64, 0.25)
        >>> img.add_uniform_disk(12.0, 37.0, 0.5, 11)
        >>> img.add_uniform_disk(13.5, 42.8, 0.25, 11)
        >>> np.abs(np.sum(img.image) - 0.75) < 1e-2
        True

        """
        radius = diameter / 2
        area = pi * radius**2
        for iy in range(self.naxis2):
            for ix in range(self.naxis1):
                r = np.sqrt((ix - xpos)**2 + (iy - ypos)**2)
                if r <= radius:
                    self.image[iy][ix] += flux / area

    def add_gaussian(self, xpos, ypos, flux, fwhm):
        """Add a circular Gaussian component to the current image.

        Args:
          xpos (float): Component position on first (fast) FITS axis /pix.
          ypos (float): Component position on second (slow) FITS axis /pix.
          flux (float): Integrated flux of component (to infinite limits).
          fwhm (float): Full width at half maximum intensity /pix.

        Example:

        >>> import numpy as np
        >>> from imageoi.GreyImg import GreyImg
        >>> img = GreyImg('test', 64, 64, 0.25)
        >>> img.add_gaussian(12.0, 37.0, 0.5, 5)
        >>> np.all(np.argmax(img.image, axis=1) == 12)
        True
        >>> np.all(np.argmax(img.image, axis=0) == 37)
        True
        >>> img.add_gaussian(11.2, 23.6, 0.25, 5)
        >>> np.abs(np.sum(img.image) - 0.75) < 1e-6
        True

        """
        peak = flux * 4 * log(2) / (pi * fwhm**2)
        for iy in range(self.naxis2):
            for ix in range(self.naxis1):
                rsq = (ix - xpos)**2 + (iy - ypos)**2
                self.image[iy][ix] += peak * exp(-4 * log(2) * rsq / fwhm**2)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
