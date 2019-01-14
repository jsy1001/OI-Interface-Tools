"""Setup module for OI-Interface-Tools."""

from setuptools import setup, find_packages
import os.path

here = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(

    name='OI-Interface-Tools',

    use_scm_version=True,

    setup_requires=['setuptools_scm'],

    description='Tools for managing OI image reconstruction input files',

    long_description=long_description,

    long_description_content_type='text/markdown',

    url='https://github.com/jsy1001/OI-Interface-Tools',

    author='John Young',

    author_email='jsy1001@cam.ac.uk',

    classifiers=[
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python :: 3',
    ],

    packages=find_packages(exclude=['tests']),

    install_requires=['numpy', 'astropy>=1.3'],

    entry_points={
        'console_scripts': [
            'image-oi-tool=imageoi.tool.__main__:main',
            'imgen=imageoi.imgen.__main__:main',
        ],
    },

    project_urls={
        'Bug Reports': 'https://github.com/jsy1001/OI-Interface-Tools/issues',
    },
)
