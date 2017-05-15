from setuptools import setup, find_packages, Extension
from distutils.util import get_platform
import os, sys
import numpy as np

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

# Generate meta-data for Git
from soundannotatordemo.config.generateMetaData import generateMetaData
generateMetaData()

ext_modules = []
include_dirs =[]


if __name__ == "__main__":
    setup(
        name='soundannotatordemo',
        version='1.1',
        url='http://www.soundappraisal.eu',
        description='Package with demo and application code accompanying the libsoundannotator libary for online sound classification ',
        long_description=read('README'),
        author='Ronald van Elburg, Arryon Tijsma',
        author_email='r.a.j.van.elburg@soundappraisal.eu',
        download_url='--tba--',
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Environment :: Console',
            'Intended Audience :: Science/Research/Education',
            'License :: Other/Proprietary License',
            'Natural Language :: English',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Topic :: Scientific/Engineering :: Computational Auditory Scene Analysis'
        ],
        install_requires=[
            'libsoundannotator',
        ],
        packages=find_packages(),
        ext_modules = None,
        ext_package = None,
        entry_points={
            'console_scripts': [
                'soundAnnotator =  soundannotatordemo.projects.simple.soundAnnotator:run',
                'inputtohdf =  soundannotatordemo.projects.input.inputtohdf:run'
            ],
        },
        test_suite='nose.collector',

        package_dir={
        },
        package_data={
        },
    )
