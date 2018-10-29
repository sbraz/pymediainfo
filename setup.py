#!/usr/bin/env python
import os
from setuptools import setup, find_packages
from subprocess import check_call

# If MEDIAINFO_BUNDLE is set, MediaInfoLib is built and bundled with the build.
# Set MEDIAINFO_BUNDLE to the project directory name (MSVC*) on Windows.
# Set it to an arbitrary value for other platforms.
bundle = os.environ.get('MEDIAINFO_BUNDLE')
if bundle:
    origdir = os.getcwd()
    dst = os.path.join(origdir, 'pymediainfo')

    if os.name == 'nt':
        os.chdir('Shared/Project/' + bundle)
        check_call(['msbuild', 'MediaInfoLib.sln'])
        # TODO
        for f in []:
            shutil.copy(f, dst)
    else:
        os.chdir('ZenLib/Project/GNU/Library')
        check_call(['sh', 'autogen.sh'])
        check_call(['./configure', '--enable-static=yes', '--prefix', dst])
        check_call(['make'])
        check_call(['make', 'install'])

        os.chdir(origdir + '/Shared/Project/GNU/Library')
        check_call(['sh', 'autogen.sh'])
        check_call(['./configure', '--enable-staticlibs', '--prefix', dst])
        check_call(['make'])
        check_call(['make', 'install'])

with open("README.rst") as f:
    long_description = f.read()

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
    data_files=[("docs", [
        "Shared/License.html",
        "ZenLib/License.txt",
    ])],
    use_scm_version=True,
    setup_requires=["setuptools_scm", "setuptools"],
    tests_require=["pytest", "pytest-runner"],
    package_data={'pymediainfo': ['*.dll', 'lib/libmediainfo.so.0*']},
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
