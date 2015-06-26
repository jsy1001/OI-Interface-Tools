#!/usr/bin/env python2

"""Python script to manage OI imaging input files."""

from __future__ import division, print_function

import argparse
import sys
import os.path

from astropy.io import fits

from InitImg import InitImg, MAS_TO_DEG
from HDUListPlus import HDUListPlus

INIT_IMG_NAME = 'IMAGE-OI INITIAL IMAGE'
INPUT_PARAM_NAME = 'IMAGE-OI INPUT PARAM'
OUTPUT_PARAM_NAME = 'IMAGE-OI OUTPUT PARAM'
RESERVED_KEYWORDS = ['XTENSION', 'BITPIX', 'NAXIS', 'NAXIS1', 'NAXIS2',
                     'PCOUNT', 'GCOUNT', 'TFIELDS',
                     'EXTNAME', 'EXTVER', 'HDUNAME', 'HDUVER']
DEFAULT_PARAM = [('WAVE_MIN', 0.1e-6), ('WAVE_MAX', 50e-6),
                 ('USE_VIS', True), ('USE_VIS2', True), ('USE_T3', True),
                 ('MAXITER', 200), ('RGL_NAME', 'mem_prior'), ('RGL_WGT', 1e5)]


def writefile(filename, datafile, initImage, inputParam,
              outputParam=None, clobber=False):
    """Write new image reconstruction input/output file.

    Args:
      filename (str): Filename for result.
      datafile (str): OIFITS filename.
      initImage (InitImg): Initial image.
      inputParam (fits.Header): Input parameters.
      outputParam (fits.Header): Output parameters, optional.
      clobber (bool): Specifies whether existing file should be
                      overwritten, optional.

    """
    hdulist = fits.HDUList(initImage.makePrimaryHDU())

    with fits.open(datafile) as dataHDUList:

        # Copy OIFITS HDUs
        for hdu in dataHDUList[1:]:
            if hdu.header['EXTNAME'][:3] == 'OI_':
                hdulist.append(hdu)

        # Copy primary header keywords
        cards = dataHDUList[0].header.copy(True).items()
        hdulist[0].header.extend(cards)

        # Append parameter HDUs
        hdu = fits.BinTableHDU(header=inputParam)
        hdulist.append(hdu)
        if outputParam is not None:
            hdulist.append(fits.BinTableHDU(header=outputParam))

        hdulist.writeto(filename, clobber=clobber)


def create(args):
    """Create image reconstruction input file from OIFITS data."""
    if not args.overwrite and os.path.exists(args.inputfile):
        sys.exit("Not creating '%s' as it already exists." % args.inputfile)

    # Create initial image
    initImage = InitImg(INIT_IMG_NAME, args.naxis1, args.naxis1)
    initImage.setWCS(cdelt=[args.cdelt1 * MAS_TO_DEG,
                            args.cdelt1 * MAS_TO_DEG],
                     ctype=['RA', 'DEC'])
    if args.modeltype == 'dirac':
        initImage.addDirac(args.naxis1 / 2, args.naxis1 / 2, 1.0)
    elif args.modeltype == 'uniform':
        initImage.addUniformDisk(args.naxis1 / 2, args.naxis1 / 2, 1.0,
                                 args.modelwidth / args.cdelt1)
    elif args.modeltype == 'gaussian':
        initImage.addGaussian(args.naxis1 / 2, args.naxis1 / 2, 1.0,
                              args.modelwidth / args.cdelt1)

    # Create input parameters with defaults
    inputParam = fits.Header()
    inputParam['EXTNAME'] = INPUT_PARAM_NAME
    inputParam['INIT_IMG'] = INIT_IMG_NAME
    for key, value in DEFAULT_PARAM:
        inputParam[key] = value

    # Overwrite user-specified parameters
    for key, value in args.param:
        inputParam[key] = value

    writefile(args.inputfile, args.datafile, initImage, inputParam,
              clobber=args.overwrite)


def copyimage(args):
    """Copy image to existing image reconstruction input/output file.

    Retains existing WCS information. Any WCS information in the image
    file is ignored.

    """
    try:
        initImage = InitImg.fromInputFilename(args.inputfile)

        with fits.open(args.imagefile) as imageHDUList, \
                fits.open(args.inputfile) as inputHDUList:

            initImage.replaceImage(imageHDUList[0].data)
            initImage.normalise()

            inputParam = inputHDUList[INPUT_PARAM_NAME].header
            try:
                outputParam = inputHDUList[OUTPUT_PARAM_NAME].header
            except KeyError:
                outputParam = None

            writefile(args.inputfile, args.inputfile, initImage,
                      inputParam, outputParam, clobber=True)

    except IOError, msg:
        sys.exit(msg)


def edit(args):
    """Edit existing image reconstruction input/output file."""
    try:
        with fits.open(args.inputfile) as hdulist:
            try:
                inputParam = hdulist[INPUT_PARAM_NAME].header
            except KeyError:
                sys.exit("Specified file '%s' has no '%s' HDU to edit." %
                         (args.inputfile, INPUT_PARAM_NAME))
            for key, value in args.param:
                inputParam[key] = value
            hdulist.writeto(args.inputfile, clobber=True)

    except IOError, msg:
        sys.exit(msg)


def show_hdu(hdu):
    """List parameters from hdu."""
    print('=== %s ===' % hdu.header['EXTNAME'])
    for key in hdu.header:
        if key not in RESERVED_KEYWORDS:
            print('%-8s = %s' % (key, hdu.header[key]))
    print('---')


def show(args):
    """List parameters from image reconstruction input/output file."""
    try:
        with fits.open(args.inputfile) as hdulist:
            try:
                show_hdu(hdulist[INPUT_PARAM_NAME])
            except KeyError:
                print("(No '%s' HDU)" % INPUT_PARAM_NAME)
            try:
                show_hdu(hdulist[OUTPUT_PARAM_NAME])
            except KeyError:
                print("(No '%s' HDU)" % OUTPUT_PARAM_NAME)

    except IOError, msg:
        sys.exit(msg)


def check(args):
    """Check whether image reconstruction input/output file is valid."""
    try:
        with fits.open(args.inputfile) as hdulist:
            hdulist.__class__ = HDUListPlus

            # Check for illegal use of EXTNAME in primary header
            extname = None
            try:
                extname = hdulist[0].header['EXTNAME']
            except KeyError:
                pass
            if extname is not None:
                sys.exit("'%s' should not use EXTNAME in the primary header." %
                         args.inputfile)

            # Check OIFITS data present
            try:
                hdulist['OI_TARGET']
            except KeyError:
                sys.exit("'%s' has no OIFITS data." % args.inputfile)

            # :TODO: check mandatory input parameters present

        try:
            img = InitImg.fromInputFilename(args.inputfile)
            img.pixelSize
        except:
            sys.exit("Failed to read initial image from '%s'" % args.inputfile)
        # :TODO: check prior image present if referenced
        # :TODO: check images normalised?

    except IOError, msg:
        sys.exit(msg)


def parse_keyword(arg):
    """Parse command line key-value pair."""
    key, value = arg.split('=')[:2]
    try:
        value = int(value)
    except ValueError:
        try:
            value = float(value)
        except ValueError:
            pass
    return key, value


def create_parser():
    """Return new ArgumentParser instance for this script."""

    # Create top-level parser for command line arguments
    parser = argparse.ArgumentParser(description=
                                     'Manage OI imaging input files')
    subparsers = parser.add_subparsers(help='sub-command help')

    # Create parser for the "create" command
    parser_create = subparsers.add_parser('create',
                                          help='create new imaging input file')
    parser_create.add_argument('-o', '--overwrite', action='store_true',
                               help='Overwrite existing file')
    parser_create.add_argument('datafile',
                               help='Input OIFITS file')
    parser_create.add_argument('inputfile',
                               help='FITS file to create')
    parser_create.add_argument('naxis1', type=int,
                               help='Image dimension (naxis2 == naxis1)')
    parser_create.add_argument('cdelt1', type=float,
                               help='Pixel size /mas (cdelt2 == cdelt1)')
    parser_create.add_argument('-mt', '--modeltype', default='blank',
                               choices=['blank',
                                        'dirac', 'uniform', 'gaussian'],
                               help='Initial image model type')
    parser_create.add_argument('-mw', '--modelwidth', type=float, default=10.0,
                               help='Initial image model width /mas')
    # :TODO: prior image (use InitImg class)
    # Note dimensions and pixel size must match initial image
    parser_create.add_argument('param', nargs='*', type=parse_keyword,
                               help='Initial parameter e.g. MAXITER=200')
    parser_create.set_defaults(func=create)

    # Create parser for the "copyimage" command
    # :TODO: prior image
    parser_copyimage = subparsers.add_parser('copyimage', help=
                                             'copy initial image from file')
    parser_copyimage.add_argument('inputfile',
                                  help='FITS file to modify')
    parser_copyimage.add_argument('imagefile',
                                  help='FITS file containing initial image')
    parser_copyimage.set_defaults(func=copyimage)

    # Create parser for the "edit" command
    # :TODO: "set" better?
    parser_edit = subparsers.add_parser('edit',
                                        help='edit existing input file')
    parser_edit.add_argument('inputfile',
                             help='FITS file to modify')
    parser_edit.add_argument('param', nargs='*', type=parse_keyword,
                             help='Replacement parameter e.g. MAXITER=200')
    parser_edit.set_defaults(func=edit)

    # Create parser for the "show" command
    parser_show = subparsers.add_parser('show',
                                        help='list parameters from input file')
    parser_show.add_argument('inputfile',
                             help='FITS file to interrogate')
    parser_show.set_defaults(func=show)

    # Create parser for the "check" command
    parser_check = subparsers.add_parser('check',
                                         help='check input file is valid')
    parser_check.add_argument('inputfile',
                              help='FITS file to interrogate')
    parser_check.set_defaults(func=check)

    return parser


def main():
    """image-oi-input.py main function."""
    parser = create_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
