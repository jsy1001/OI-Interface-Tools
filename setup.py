#!/usr/bin/env python

"""Setup script for OI Interface Tools."""

from os import path

from setuptools import find_packages, setup


here = path.abspath(path.dirname(__file__))
with open(path.join(here, "README.md")) as readme_file:
    readme = readme_file.read()

requirements = ["numpy", "astropy"]

setup_requirements = ["setuptools_scm"]

test_requirements = []

setup(
    author="John Young",
    author_email="jsy1001@cam.ac.uk",
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    description="Tools for managing OI image reconstruction input files",
    install_requires=requirements,
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords="OI-Interface-Tools",
    name="OI-Interface-Tools",
    packages=find_packages(exclude=["tests"]),
    entry_points={
        "console_scripts": [
            "image-oi-tool=imageoi.tool.__main__:main",
            "imgen=imageoi.imgen.__main__:main",
        ],
    },
    use_scm_version=True,
    project_urls={
        "Bug Reports": "https://github.com/jsy1001/OI-Interface-Tools/issues",
    },
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    zip_safe=False,
)
