#!/usr/bin/env python2

import argparse
import sys
import os.path

import astropy.io.fits as fits

from InitImg import InitImg

INPUT_PARAM_EXTNAME = 'IMAGE-OI INPUT PARAM'
OUTPUT_PARAM_EXTNAME = 'IMAGE-OI OUTPUT PARAM'


def parse_keyval(arg):
    key, value = arg.split('=')[:2]
    try:
        value = int(value)
    except ValueError:
        try:
            value = float(value)
        except ValueError:
            pass
    return key, value
    

def create(args):
    """Create new image reconstruction input file."""
    if os.path.exists(args.filename):
        sys.exit("Not creating '%s' as it already exists." % args.filename)


def edit(args):
    """Edit existing image reconstruction input file."""
    try:
        hdulist = fits.open(args.filename)
    except IOError, msg:
        sys.exit(msg)
    try:
        #inputParam = hdulist[INPUT_PARAM_EXTNAME]
        inputParam = hdulist[0]
    except KeyError:
        sys.exit("Specified file '%s' has no '%s' HDU to edit." %
                 (args.filename, INPUT_PARAM_EXTNAME))
    for p in args.params:
        key, value = parse_keyval(p)
        print '%s -> %s' % (key, value)
        inputParam.header[key] = value
    hdulist.writeto(args.filename, clobber=True)


def show(args):
    """List parameters from image reconstruction input file."""
    try:
        hdulist = fits.open(args.filename)
    except IOError, msg:
        sys.exit(msg)
    if INPUT_PARAM_EXTNAME in hdulist:
        inputParam = hdulist[INPUT_PARAM_EXTNAME]
        print '=== INPUT PARAMETERS ==='
        for p in inputParam.header:
            print p
    else:
        print "(No '%s' HDU)" % INPUT_PARAM_EXTNAME
    if OUTPUT_PARAM_EXTNAME in hdulist:
        outputParam = hdulist[OUTPUT_PARAM_EXTNAME]
        print '=== OUTPUT PARAMETERS ==='
        for p in outputParam.header:
            print p
    else:
        print "(No '%s' HDU)" % OUTPUT_PARAM_EXTNAME


def main():
    """image-oi-input.py main function."""

    # Create top-level parser for command line arguments
    parser = argparse.ArgumentParser(description=
                                     'Manage OI imaging input files')
    subparsers = parser.add_subparsers(help='sub-command help')

    # Create parser for the "create" command
    parser_create = subparsers.add_parser('create',
                                          help='create new imaging input file')
    parser_create.add_argument('filename',
                               help='FITS file to create')
    parser_create.add_argument('naxis1',
                               help='Image dimension (naxis2 == naxis1)')
    parser_create.set_defaults(func=create)

    # Create parser for the "edit" command
    parser_edit = subparsers.add_parser('edit',
                                        help='edit existing input file')
    parser_edit.add_argument('filename',
                             help='FITS file to edit')
    parser_edit.add_argument('params', nargs='*',
                             help='Replacement parameters e.g. MAXITER=200')
    parser_edit.set_defaults(func=edit)

    # Create parser for the "show" command
    parser_show = subparsers.add_parser('show',
                                        help='list parameters from input file')
    parser_show.add_argument('filename',
                             help='FITS file to interrogate')
    parser_show.set_defaults(func=show)

    # Parse the args and call function corresponding to the user's command
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
