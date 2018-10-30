#!/usr/bin/env python
import os
from setuptools import setup, find_packages

with open("README.rst") as f:
    long_description = f.read()

bin_license = 'docs/License.html'
if os.path.exists(bin_license):
    data_files = [('docs', [bin_license])]
    bin_files = ['MediaInfo.dll', 'libmediainfo.*']
    # TODO set PEP425 tag
else:
    data_files = []
    bin_files = []

setup(
    name='pymediainfo',
    author='Louis Sautier',
    author_email='sautier.louis@gmail.com',
    url='https://github.com/sbraz/pymediainfo',
    description="""A Python wrapper for the mediainfo library.""",
    long_description=long_description,
    packages=find_packages(),
    namespace_packages=[],
    include_package_data=True,
    zip_safe=False,
    license='MIT',
    data_files=data_files,
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    install_requires=["setuptools"],
    tests_require=["pytest", "pytest-runner"],
    package_data={'pymediainfo': bin_files},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "License :: OSI Approved :: MIT License",
    ]
)
