"""Python script to manage OI imaging input files."""

import argparse
import os.path
import sys

from astropy.io import fits

from imageoi import __version__
from imageoi.imagingfile import INIT_IMG_NAME, ImagingFile, PRIOR_IMG_NAME
from imageoi.initimage import GreyImg


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
    initimg.setwcs(ctype=["RA", "DEC"])
    if args.modeltype == "dirac":
        initimg.add_dirac(args.naxis1 / 2, args.naxis1 / 2, 1.0)
    elif args.modeltype == "uniform":
        initimg.add_uniform_disk(
            args.naxis1 / 2, args.naxis1 / 2, 1.0, args.modelwidth / args.pixelsize
        )
    elif args.modeltype == "gaussian":
        initimg.add_gaussian(
            args.naxis1 / 2, args.naxis1 / 2, 1.0, args.modelwidth / args.pixelsize
        )
    result.initimg = initimg

    result.writeto(args.inputfile, overwrite=args.overwrite)


def copyinit(args):
    """Copy FITS image to image reconstruction input file as initial image.

    Retains existing WCS information. Any WCS information in the image
    file is ignored.

    """
    try:
        result = ImagingFile.fromfilename(args.inputfile)
        with fits.open(args.imagefile) as imghdulist:
            if result.initimg is None:
                sys.exit(
                    ("Input file '%s' missing initial image " % args.inputfile)
                    + "hence pixelsize not defined"
                )
            result.initimg.image = imghdulist[0].data
            result.initimg.normalise()
            result.writeto(args.inputfile, overwrite=True)
    except IOError as e:
        sys.exit(e)


def copyprior(args):
    """Copy FITS image to image reconstruction input file as prior image.

    Retains existing WCS information. Any WCS information in the image
    file is ignored.

    """
    try:
        result = ImagingFile.fromfilename(args.inputfile)
        with fits.open(args.imagefile) as imghdulist:
            if result.initimg is None:
                sys.exit(
                    ("Input file '%s' missing initial image " % args.inputfile)
                    + "hence pixelsize not defined"
                )
            # Note optional prior image may not be set
            if result.priorimg is None:
                assert result.initimg is not None
                result.priorimg = GreyImg(
                    PRIOR_IMG_NAME,
                    result.initimg.naxis1,
                    result.initimg.naxis2,
                    result.initimg.pixelsize,
                )
            result.priorimg.image = imghdulist[0].data
            result.priorimg.normalise()
            result.writeto(args.inputfile, overwrite=True)
    except IOError as e:
        sys.exit(e)


def edit(args):
    """Edit existing image reconstruction input/output file."""
    try:
        result = ImagingFile.fromfilename(args.inputfile)
        for key, value in args.param:
            result.inparam[key] = value
        result.writeto(args.inputfile, overwrite=True)
    except IOError as e:
        sys.exit(e)


def show(args):
    """List parameters from image reconstruction input/output file."""
    try:
        toshow = ImagingFile.fromfilename(args.inputfile)
        print(toshow)
    except IOError as e:
        sys.exit(e)


def parse_keyword(arg):
    """Parse command line key-value pair."""
    key, value = arg.split("=")[:2]
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
    parser = argparse.ArgumentParser(description="Manage OI imaging input files")
    parser.add_argument("-V", "--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(help="sub-command help")

    # Create parser for the "create" command
    parser_create = subparsers.add_parser(
        "create", help="create new imaging input file"
    )
    parser_create.add_argument(
        "-o", "--overwrite", action="store_true", help="Overwrite existing file"
    )
    parser_create.add_argument("datafile", help="Input OIFITS file")
    parser_create.add_argument("inputfile", help="FITS file to create")
    parser_create.add_argument(
        "naxis1", type=int, help="Image dimension (naxis2 == naxis1)"
    )
    parser_create.add_argument("pixelsize", type=float, help="Pixel size /mas")
    parser_create.add_argument(
        "-mt",
        "--modeltype",
        default="blank",
        choices=["blank", "dirac", "uniform", "gaussian"],
        help="Initial image model type",
    )
    parser_create.add_argument(
        "-mw",
        "--modelwidth",
        type=float,
        default=10.0,
        help="Initial image model width /mas",
    )
    # TODO: prior image (use GreyImg class)
    # Note dimensions and pixel size must match initial image
    parser_create.add_argument(
        "param",
        nargs="*",
        type=parse_keyword,
        help="Initial parameter e.g. MAXITER=200",
    )
    parser_create.set_defaults(func=create)

    # Create parser for the "copyinit" command
    parser_copyinit = subparsers.add_parser(
        "copyinit", help="copy initial image from file"
    )
    parser_copyinit.add_argument("inputfile", help="FITS file to modify")
    parser_copyinit.add_argument(
        "imagefile", help="FITS file with initial image in primary HDU"
    )
    parser_copyinit.set_defaults(func=copyinit)

    # Create parser for the "copyprior" command
    parser_copyprior = subparsers.add_parser(
        "copyprior", help="copy prior image from file"
    )
    parser_copyprior.add_argument("inputfile", help="FITS file to modify")
    parser_copyprior.add_argument(
        "imagefile", help="FITS file with prior image in primary HDU"
    )
    parser_copyprior.set_defaults(func=copyprior)

    # Create parser for the "edit" command
    # TODO: "set" better than "edit"?
    parser_edit = subparsers.add_parser("edit", help="edit existing input file")
    parser_edit.add_argument("inputfile", help="FITS file to modify")
    parser_edit.add_argument(
        "param",
        nargs="*",
        type=parse_keyword,
        help="Replacement parameter e.g. MAXITER=200",
    )
    parser_edit.set_defaults(func=edit)

    # Create parser for the "show" command
    parser_show = subparsers.add_parser("show", help="list parameters from input file")
    parser_show.add_argument("inputfile", help="FITS file to interrogate")
    parser_show.set_defaults(func=show)

    return parser


def main():
    """Run the application."""
    parser = create_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except AttributeError:
        parser.print_usage()


if __name__ == "__main__":
    main()
