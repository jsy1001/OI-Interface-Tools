from astropy.io import fits


class HDUListPlus(fits.HDUList):

    """Extension of fits.HDUList for lookup by HDUNAME/HDUVER keywords."""

    def __getitem__(self, index):
        """Lookup HDU by position, EXTNAME, (EXTNAME, EXTVER), HDUNAME, or
        (HDUNAME, HDUVER).

        The latter two options are extensions implemented by the
        HDUListPlus class.

        """
        try:
            return fits.HDUList.__getitem__(self, index)
        except KeyError:
            for hdu in self:
                name = None
                ver = None
                try:
                    name = hdu.header['HDUNAME']
                    ver = hdu.header['HDUVER']
                except:
                    pass
                if name == index or (name, ver) == index:
                    return hdu
            raise KeyError, "HDU '%s' not found." % index
