# https://raw.githubusercontent.com/pypa/sampleproject/master/setup.py
from setuptools import setup, find_packages  # Always prefer setuptools over distutils
from codecs import open  # To use a consistent encoding
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='gthumpy',

    version='0',

    description='Python GTK GUI to view my photo collection',
    long_description=long_description,

    url='https://github.com/guettli/gthumpy',

    # Author details
    author='Thomas Guettler',
    author_email='guettli.gthumpy@thomas-guettler.de',

    license='BSD',

    classifiers=[
        'Programming Language :: Python :: 2',
    ],

    entry_points={
        'console_scripts': [
            'gthumpy=gthumpy.editMetadata:main',
        ],
    },
    test_suite='tests',
)
