from setuptools import setup, find_packages

setup(
    name='OI-Interface-Tools',

    version='0.1.0',

    description='Tools for managing OI image reconstruction input files',

    url='https://github.com/jsy1001/OI-Interface-Tools',

    author='John Young',
    author_email='jsy1001@cam.ac.uk',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python :: 3'
    ],

    project_urls={
        'Bug Reports': 'https://github.com/jsy1001/OI-Interface-Tools/issues'
    },

    packages=find_packages(exclude=['tests']),

    python_requires='>=3',

    entry_points={'console_scripts':
                  ['image-oi-tool = imageoi.tool.__main__:main']},
)
