"""Python module to create and edit input files for OI image reconstruction.

An input/output file is represented by an instance of the ImagingFile
class.

Attributes:
  INIT_IMG_NAME (str): HDUNAME of initial image.
  PRIOR_IMG_NAME (str): HDUNAME of prior image.
  INPUT_PARAM_NAME (str): EXTNAME of input parameters HDU.
  OUTPUT_PARAM_NAME (str): EXTNAME of output parameters HDU.
  RESERVED_KEYWORDS (list): FITS keywords that aren't imaging parameters.
  DEFAULT_PARAM = (list of tuples (keyword, value)): Default input parameters.
  PARAM_COMMENTS = (dict): Default comments for input parameters.

"""

from astropy.io import fits

from imageoi.GreyImg import GreyImg

INIT_IMG_NAME = 'IMAGE-OI INITIAL IMAGE'
PRIOR_IMG_NAME = 'IMAGE-OI PRIOR IMAGE'
INPUT_PARAM_NAME = 'IMAGE-OI INPUT PARAM'
OUTPUT_PARAM_NAME = 'IMAGE-OI OUTPUT PARAM'
RESERVED_KEYWORDS = ['XTENSION', 'BITPIX', 'NAXIS', 'NAXIS1', 'NAXIS2',
                     'PCOUNT', 'GCOUNT', 'TFIELDS',
                     'EXTNAME', 'EXTVER', 'HDUNAME', 'HDUVER']
DEFAULT_PARAM = [('TARGET', None), ('WAVE_MIN', 0.1e-6), ('WAVE_MAX', 50e-6),
                 ('USE_VIS', 'ALL'), ('USE_VIS2', True), ('USE_T3', 'ALL'),
                 ('MAXITER', 200), ('RGL_NAME', 'mem_prior'),
                 ('AUTO_WGT', False), ('RGL_WGT', 1e5),
                 ('FLUX', 1.0), ('FLUXERR', 0.0)]
PARAM_COMMENTS = {'TARGET': 'Identifier of target to select',
                  'WAVE_MIN': '[m] Minimum wavelength to select',
                  'WAVE_MAX': '[m] Maximum wavelength to select',
                  'USE_VIS': 'Complex visibility data to use if any',
                  'USE_VIS2': 'Use squared visibility data if any',
                  'USE_T3': 'Triple product data to use if any',
                  'INIT_IMG': 'HDUNAME of initial image',
                  'MAXITER': 'Maximum number of iterations to run',
                  'RGL_NAME': 'Name of the regularization method',
                  'AUTO_WGT': 'Automatic regularization weight',
                  'RGL_WGT': 'Weight of the regularization',
                  'RGL_PRIO': 'HDUNAME of prior image',
                  'FLUX': 'Assumed total flux',
                  'FLUXERR': 'Error bar for total flux'}


def mergeheaders(headers):
    """Merge multiple FITS headers.

    Args:
      headers (list of fits.Header objects): Headers to merge.

    Raises:
      ValueError: The keywords (except COMMENT and HISTORY) do not all have
                  unique values.

    Returns:
      fits.Header object containing the merged headers.

    Example:

      The following merges two headers:

      >>> from astropy.io import fits
      >>> from imageoi.ImagingFile import INIT_IMG_NAME, mergeheaders
      >>> a = fits.Header()
      >>> a['TELESCOP'] = 'CHARA'
      >>> a['HISTORY'] = 'a first history line'
      >>> a['HISTORY'] = 'a second history line'
      >>> b = fits.Header()
      >>> b['TELESCOP'] = 'CHARA'
      >>> b['HDUNAME'] = INIT_IMG_NAME
      >>> b['HISTORY'] = 'b only history line'
      >>> c = mergeheaders([a, b])
      >>> c['TELESCOP']
      'CHARA'
      >>> c['HDUNAME'] == INIT_IMG_NAME
      True
      >>> len(c['HISTORY'])
      3

      Attempting to merge headers that have distinct values for the same
      keyword results in a ValueError:

      >>> a = fits.Header()
      >>> a['TELESCOP'] = 'CHARA'
      >>> b = fits.Header()
      >>> b['TELESCOP'] = 'IOTA'
      >>> mergeheaders([a, b])  # doctest: +ELLIPSIS
      Traceback (most recent call last):
          ...
      ValueError: Cannot merge: non-identical values for 'TELESCOP'...

    """
    ret = fits.Header()
    for hdr in headers:
        for key in hdr:
            if key not in ['COMMENT', 'HISTORY']:
                try:
                    current = ret[key]
                    if current != hdr[key]:
                        raise ValueError("Cannot merge: non-identical " +
                                         "values for '%s' keyword (%r, %r)" %
                                         (key, current, hdr[key]))
                except KeyError:
                    ret[key] = hdr[key]

        try:
            for value in hdr['COMMENT']:
                ret['COMMENT'] = value
        except KeyError:
            pass  # no comments in hdr
        try:
            for value in hdr['HISTORY']:
                ret['HISTORY'] = value
        except KeyError:
            pass  # no history in hdr
    return ret


def _reprheader(header):
    if header is None:
        return repr(header)
    ret = "["
    for key in header:
        if key not in ['COMMENT', 'HISTORY']:
            ret += "%s=%r, " % (key, header[key])
    ret = ret.rstrip(' ,') + "]"
    return ret


class ImagingFile(object):
    """OI image reconstruction input/output file class.

    Args:
      datafilename (str): Input OIFITS filename.

    Attributes:
      dataheader (fits.Header): Descriptive header cards from OIFITS file.
      datatables (list): HDUs from OIFITS file.
      inparam (fits.Header): Scalar input parameters.
      outparam (fits.Header or None): Scalar output parameters.
      initimg (GreyImg or None): Initial image object.
      priorimg (GreyImg or None): Prior image object.

    Examples:

      The following creates a (useless) input file object without OIFITS data.

      >>> from imageoi.ImagingFile import ImagingFile
      >>> from imageoi.ImagingFile import INPUT_PARAM_NAME, DEFAULT_PARAM
      >>> inp = ImagingFile()
      >>> assert repr(inp).startswith('ImagingFile(')
      >>> len(inp.datatables)
      0
      >>> inp.inparam['EXTNAME'] == INPUT_PARAM_NAME
      True
      >>> inp.inparam['INIT_IMG']
      Traceback (most recent call last):
          ...
      KeyError: "Keyword 'INIT_IMG' not found."
      >>> for key, value in DEFAULT_PARAM:
      ...     assert value is None or inp.inparam[key] == value
      >>> inp.initimg
      >>> inp.priorimg

      The following creates an input file object from OIFITS data.

      >>> import os.path
      >>> from imageoi.ImagingFile import ImagingFile
      >>> filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
      ...                         '..', 'tests', 'Bin_Ary--MIRC_H.fits')
      >>> inp = ImagingFile(filename)
      >>> len(inp.datatables)
      5
      >>> inp.writeto('utest1.fits', True)
      >>> import os
      >>> os.remove('utest1.fits')

      The following creates an imaging file object from an existing file:

      >>> from imageoi.ImagingFile import ImagingFile
      >>> exists = ImagingFile()
      >>> exists.writeto('utest2.fits', True)
      >>> inp = ImagingFile.fromfilename('utest2.fits')
      >>> import os
      >>> os.remove('utest2.fits')
      >>> assert len(inp.datatables) == len(exists.datatables)
      >>> for key in exists.inparam:
      ...     assert inp.inparam[key] == exists.inparam[key]

      The following sets the initial image:

      >>> from astropy.io import fits
      >>> from imageoi.GreyImg import GreyImg
      >>> from imageoi.ImagingFile import ImagingFile, INIT_IMG_NAME
      >>> inp = ImagingFile()
      >>> inp.initimg = GreyImg(INIT_IMG_NAME, 64, 64, 0.25)
      >>> assert inp.priorimg is None
      >>> assert inp.inparam['INIT_IMG'] == INIT_IMG_NAME
      >>> inp.writeto('utest3.fits', True)
      >>> with fits.open('utest3.fits') as hdulist:
      ...     len(hdulist)
      2
      >>> import os
      >>> os.remove('utest3.fits')

      The following sets the prior image. There should be 3 HDUs in
      the resulting FITS file: the empty primary HDU, an image HDU
      containing the prior image, and a binary table containing the
      input parameters:

      >>> from astropy.io import fits
      >>> from imageoi.GreyImg import GreyImg
      >>> from imageoi.ImagingFile import ImagingFile, PRIOR_IMG_NAME
      >>> inp = ImagingFile()
      >>> inp.priorimg = GreyImg(PRIOR_IMG_NAME, 64, 64, 0.25)
      >>> assert inp.inparam['RGL_PRIO'] == PRIOR_IMG_NAME
      >>> inp.writeto('utest4.fits', True)
      >>> with fits.open('utest4.fits') as hdulist:
      ...     len(hdulist)
      3
      >>> import os
      >>> os.remove('utest4.fits')

    """

    def __init__(self, datafilename=None):
        self.dataheader = fits.Header()
        self.datatables = []
        self.inparam = fits.Header()
        self.inparam['EXTNAME'] = INPUT_PARAM_NAME
        for key, value in DEFAULT_PARAM:
            self.inparam[key] = value
        self.outparam = None
        self._initimg = None
        self._priorimg = None
        if datafilename is not None:
            with fits.open(datafilename) as hdulist:
                # Copy from primary header
                cards = hdulist[0].header.copy(True).items()
                for card in cards:
                    if card[0] not in RESERVED_KEYWORDS:
                        self.dataheader.append(card)
                # Copy OIFITS binary tables
                for hdu in hdulist[1:]:
                    if hdu.header['EXTNAME'].startswith('OI_'):
                        self.datatables.append(hdu.copy())

    @classmethod
    def fromfilename(cls, filename):
        """Initialise ImagingFile from an imaging input/output file."""
        self = cls(filename)
        with fits.open(filename) as hdulist:
            self.inparam = hdulist[INPUT_PARAM_NAME].header
            # Read optional content
            try:
                self.outparam = hdulist[OUTPUT_PARAM_NAME].header
            except KeyError:
                pass
            try:
                self.initimg = GreyImg.frominputfilename(filename)
            except KeyError:
                pass
            try:
                self.priorimg = GreyImg.frominputfilename(filename, 'RGL_PRIO')
            except KeyError:
                pass
        return self

    @property
    def initimg(self):
        """Return initial image object."""
        return self._initimg

    @initimg.setter
    def initimg(self, img):
        """Set initial image object.

        Adds reference to image's HDUNAME to input parameters.

        """
        self._initimg = img
        self.inparam['INIT_IMG'] = img.name

    @property
    def priorimg(self):
        """Return prior image object."""
        return self._priorimg

    @priorimg.setter
    def priorimg(self, img):
        """Set prior image object.

        Adds reference to image's HDUNAME to input parameters.

        """
        self._priorimg = img
        self.inparam['RGL_PRIO'] = img.name

    def __repr__(self):
        ret = "ImagingFile("
        ret += ("dataheader=%s, datatables=%r, " %
                (_reprheader(self.dataheader), self.datatables))
        ret += ("inparam=%s, outparam=%s, " %
                (_reprheader(self.inparam), _reprheader(self.outparam)))
        ret += ("initimg=%r, priorimg=%r" %
                (self.initimg, self.priorimg))
        ret += ")"
        return ret

    def __str__(self):
        ret = "=== %s ===\n" % INPUT_PARAM_NAME
        for key in self.inparam:
            if key not in RESERVED_KEYWORDS:
                ret += "%-8s = %s\n" % (key, self.inparam[key])
        ret += "---\n"
        if self.outparam is not None:
            ret += "=== %s ===\n" % OUTPUT_PARAM_NAME
            for key in self.outparam:
                if key not in RESERVED_KEYWORDS:
                    ret += "%-8s = %s\n" % (key, self.outparam[key])
            ret += "---\n"
        return ret

    def _set_param_comments(self):
        for key in self.inparam:
            try:
                if self.inparam.comments[key] == '':
                    self.inparam.comments[key] = PARAM_COMMENTS[key]
            except KeyError:
                pass
        # :TODO: set comments for output parameters

    def writeto(self, filename, overwrite=False):
        """Write object's data to file.

        Sets comments for standard input parameters.

        Args:
          filename (str): Filename for result.
          overwrite (bool): Specifies whether existing file should be
                            overwritten, optional.
        """
        self._set_param_comments()
        if self.initimg is not None:
            hdulist = fits.HDUList(self.initimg.make_primary_hdu())
        else:
            hdulist = fits.HDUList(fits.PrimaryHDU())
        if self.priorimg is not None:
            hdulist.append(self.priorimg.make_image_hdu())

        # Add OIFITS data
        hdulist[0].header = mergeheaders([hdulist[0].header, self.dataheader])
        for hdu in self.datatables:
            hdulist.append(hdu)

        # Append parameter HDUs
        hdulist.append(fits.BinTableHDU(header=self.inparam))
        if self.outparam is not None:
            hdulist.append(fits.BinTableHDU(header=self.outparam))

        hdulist.writeto(filename, overwrite=overwrite)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
