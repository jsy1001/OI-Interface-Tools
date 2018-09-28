"""Python script to generate simple model images."""

import argparse
import sys
import os.path

from imageoi import __version__
from imageoi.imagingfile import INIT_IMG_NAME
from imageoi.initimage import GreyImg


def generate(args):
    """Generate model image in FITS format."""
    if not args.overwrite and os.path.exists(args.imagefile):
        sys.exit("Not creating '%s' as it already exists." % args.imagefile)

    img = GreyImg(INIT_IMG_NAME, args.naxis1, args.naxis1, args.pixelsize)
    img.setwcs(ctype=['RA', 'DEC'])
    if args.modeltype == 'dirac':
        img.add_dirac(args.naxis1 / 2, args.naxis1 / 2, 1.0)
    elif args.modeltype == 'uniform':
        img.add_uniform_disk(args.naxis1 / 2, args.naxis1 / 2, 1.0,
                             args.modelwidth / args.pixelsize)
    elif args.modeltype == 'gaussian':
        img.add_gaussian(args.naxis1 / 2, args.naxis1 / 2, 1.0,
                         args.modelwidth / args.pixelsize)
    elif args.modeltype == 'ld':
        img.add_hestroffer_disk(args.naxis1 / 2, args.naxis1 / 2, 1.0,
                                args.modelwidth / args.pixelsize, args.ldalpha)
    img.make_primary_hdu().writeto(args.imagefile, overwrite=args.overwrite)


def create_parser():
    """Return new ArgumentParser instance for this script."""
    parser = argparse.ArgumentParser(description='Generate model image')
    parser.add_argument('-V', '--version',
                        action='version', version=__version__)
    parser.add_argument('-o', '--overwrite', action='store_true',
                        help='Overwrite existing file')
    parser.add_argument('imagefile',
                        help='FITS image to create')
    parser.add_argument('naxis1', type=int,
                        help='Image dimension (naxis2 == naxis1)')
    parser.add_argument('pixelsize', type=float,
                        help='Pixel size /mas')
    parser.add_argument('-mt', '--modeltype', default='blank',
                        choices=['blank', 'dirac', 'uniform', 'gaussian',
                                 'ld'],
                        help='Image model type')
    parser.add_argument('-mw', '--modelwidth', type=float, default=10.0,
                        help='Initial image model width /mas')
    parser.add_argument('--ldalpha', type=float, default=1.0,
                        help='Limb-darkening parameter for -mt ld')
    return parser


def main():
    """Main function."""
    parser = create_parser()
    args = parser.parse_args()
    try:
        generate(args)
    except AttributeError:
        parser.print_usage()


if __name__ == '__main__':
    main()
