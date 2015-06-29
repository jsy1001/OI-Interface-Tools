#!/usr/bin/env python2

"""Python script to manage OI imaging input files."""

from __future__ import division, print_function

import argparse
import sys
import os.path

from astropy.io import fits

from ImagingFile import ImagingFile
from GreyImg import GreyImg
from HDUListPlus import HDUListPlus

INIT_IMG_NAME = 'IMAGE-OI INITIAL IMAGE'


def create(args):
    """Create image reconstruction input file from OIFITS data."""
    if not args.overwrite and os.path.exists(args.inputfile):
        sys.exit("Not creating '%s' as it already exists." % args.inputfile)

    # Create input file object with default parameters
    result = ImagingFile(args.datafile)

    # Overwrite user-specified parameters
    for key, value in args.param:
        result.inparam[key] = value

    # Set initial image
    initimg = GreyImg(INIT_IMG_NAME, args.naxis1, args.naxis1, args.pixelsize)
    initimg.setwcs(ctype=['RA', 'DEC'])
    if args.modeltype == 'dirac':
        initimg.add_dirac(args.naxis1 / 2, args.naxis1 / 2, 1.0)
    elif args.modeltype == 'uniform':
        initimg.add_uniform_disk(args.naxis1 / 2, args.naxis1 / 2, 1.0,
                                 args.modelwidth / args.cdelt1)
    elif args.modeltype == 'gaussian':
        initimg.add_gaussian(args.naxis1 / 2, args.naxis1 / 2, 1.0,
                             args.modelwidth / args.cdelt1)
    result.initimg = initimg

    result.writeto(args.inputfile, clobber=args.overwrite)


def copyimage(args):
    """Copy image to existing image reconstruction input/output file.

    Retains existing WCS information. Any WCS information in the image
    file is ignored.

    """
    try:
        result = ImagingFile.fromfilename(args.inputfile)
        with fits.open(args.imagefile) as imghdulist:
            result.initimg.image = imghdulist[0].data
            result.initimg.normalise()
            result.writeto(args.inputfile, clobber=True)
    except IOError, msg:
        sys.exit(msg)


def edit(args):
    """Edit existing image reconstruction input/output file."""
    try:
        result = ImagingFile.fromfilename(args.inputfile)
        for key, value in args.param:
            result.inparam[key] = value
        result.writeto(args.inputfile, clobber=True)
    except IOError, msg:
        sys.exit(msg)


def show(args):
    """List parameters from image reconstruction input/output file."""
    try:
        toshow = ImagingFile.fromfilename(args.inputfile)
        print(toshow)
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
    parser_create.add_argument('pixelsize', type=float,
                               help='Pixel size /mas')
    parser_create.add_argument('-mt', '--modeltype', default='blank',
                               choices=['blank',
                                        'dirac', 'uniform', 'gaussian'],
                               help='Initial image model type')
    parser_create.add_argument('-mw', '--modelwidth', type=float, default=10.0,
                               help='Initial image model width /mas')
    # :TODO: prior image (use GreyImg class)
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

    return parser


def main():
    """image-oi-input.py main function."""
    parser = create_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
