#!/usr/bin/env python2

from __future__ import division, print_function

import argparse
import sys
import os.path

import numpy as np
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


def create(args):
    """Create new image reconstruction input file."""
    if not args.overwrite and os.path.exists(args.inputfile):
        sys.exit("Not creating '%s' as it already exists." % args.inputfile)

    # Create initial image
    img = InitImg(INIT_IMG_NAME, args.naxis1, args.naxis1)
    img.setWCS(cdelt=[args.cdelt1 * MAS_TO_DEG, args.cdelt1 * MAS_TO_DEG],
               ctype=['RA', 'DEC'])
    if args.modeltype == 'dirac':
        img.addDirac(args.naxis1 / 2, args.naxis1 / 2, 1.0)
    elif args.modeltype == 'uniform':
        img.addUniformDisk(args.naxis1 / 2, args.naxis1 / 2, 1.0,
                           args.modelwidth / args.cdelt1)
    elif args.modeltype == 'gaussian':
        img.addGaussian(args.naxis1 / 2, args.naxis1 / 2, 1.0,
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

    # Write out copy of input OIFITS with new HDUs added
    with fits.open(args.datafile) as hdulist:
        hdulist[0] = img.makePrimaryHDU()
        # :TODO: copy primary header keywords from datafile?
        hdulist.append(fits.BinTableHDU(header=inputParam))
        hdulist.writeto(args.inputfile, clobber=args.overwrite)


def copyimage(args):
    """Copy image to existing image reconstruction input/output file."""

    # Open files
    try:
        with fits.open(args.imagefile) as sourceHduList, \
             fits.open(args.inputfile) as destHduList:

            # Find source and destination image HDUs
            destHduList.__class__ = HDUListPlus
            try:
                sourceParam = sourceHduList[INPUT_PARAM_NAME].header
                sourceImageHdu = sourceHduList[sourceParam['INIT_IMG']]
            except KeyError:
                # Fallback to primary HDU
                sourceImageHdu = sourceHduList[0]
            destParam = destHduList[INPUT_PARAM_NAME].header
            destImageHdu = destHduList[destParam['INIT_IMG']]

            # Check dimensions match
            if sourceImageHdu.data.shape != destImageHdu.data.shape:
                sys.exit("Image dimensions %s do not match destination %s" %
                         (sourceImageHdu.data.shape, destImageHdu.data.shape))

            # Copy image and normalise
            total = np.sum(sourceImageHdu.data)
            if np.fabs(total) > 0:
                destImageHdu.data = sourceImageHdu.data / total
            else:
                destImageHdu.data = sourceImageHdu.data
            destHduList.writeto(args.inputfile, clobber=True)

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
    for p in hdu.header:
        if p not in RESERVED_KEYWORDS:
            print('%-8s = %s' % (p, hdu.header[p]))
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
            try:
                hdulist['OI_TARGET']
            except KeyError:
                sys.exit("'%s' has no OIFITS data." % args.inputfile)
            # :TODO: check mandatory input parameters present
        try:
            img = InitImg.fromInputFilename(args.inputfile)
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
