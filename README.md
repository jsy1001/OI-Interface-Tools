# OI Interface Tools

[![CI](https://github.com/jsy1001/OI-Interface-Tools/actions/workflows/ci.yml/badge.svg)](https://github.com/jsy1001/OI-Interface-Tools/actions/workflows/ci.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Software tools for managing input/output files for image reconstruction and model-fitting from optical interferometric data

A standard interface to image reconstruction algorithms is being developed at https://github.com/emmt/OI-Imaging-JRA . This repository contains tools for managing FITS files, used as input to and output from the algorithms, that follow this standard.

Currently this repository contains several Python modules plus two scripts:
- `image-oi-tool` creates, modifies, or lists parameters from image reconstruction input/output FITS files; and
- `imgen` generates simple model images in FITS format.

## Credits

This package was created with
[Cookiecutter](https://github.com/audreyr/cookiecutter) and the
`harps3-cookiecutter-pyproject` project template.
