"""Python module to create initial images for OI image reconstruction.

A grey initial image is represented by the InitImg class.

"""

import astropy.io.fits as fits
import numpy as np


class InitImg(object):

    """OI image reconstruction initial image class.

    Args:
      naxis1 (int): First dimension of image.
      naxis2 (int): Second dimension of image.

    Attributes:
      image (ndarray): The image pixel data as a numpy array.

    Examples:
      The following creates a blank 64 by 64 image:

      >>> img = InitImg(64, 64)
      >>> type(img.image) == np.ndarray
      True
      >>> np.all(img.image == 0.0)
      True
      >>> img.isSquare()
      True

    """

    def __init__(self, naxis1, naxis2):
        self.naxis1 = naxis1
        self.naxis2 = naxis2
        self.image = np.zeros((naxis1, naxis2), np.float)

    def isSquare(self):
        """Does image have identical dimensions in both axes?"""
        return self.naxis1 == self.naxis2


if __name__ == "__main__":
    import doctest
    doctest.testmod()
