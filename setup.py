#!/usr/bin/env python
import os

from setuptools import find_packages, setup, Distribution

with open("README.rst") as f:
    long_description = f.read()

# Add license if it exists
data_files = []
bin_licenses = ['docs/License.html', 'docs/LICENSE']
for bin_license in bin_licenses:
    if os.path.exists(bin_license):
        data_files.append(('docs', [bin_license]))

# Add libraries
bin_files = ['MediaInfo.dll', 'libmediainfo.*']
try:
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel

    class platform_bdist_wheel(_bdist_wheel):
        def finalize_options(self):
            _bdist_wheel.finalize_options(self)
            # Force the wheel to be marked as platform-specific
            self.root_is_pure = False

        def get_tag(self):
            python, abi, plat = _bdist_wheel.get_tag(self)
            # The python code works for any Python version,
            # not just the one we are running to build the wheel
            return 'py3', 'none', plat

    # https://stackoverflow.com/questions/76450587/python-wheel-that-includes-shared-library-is-built-as-pure-python-platform-indep
    class PlatformDistribution(Distribution):

        def __init__(self, *attrs):
            Distribution.__init__(self, *attrs)
            self.cmdclass['bdist_wheel'] = platform_bdist_wheel

        def is_pure(self):
            return False

        def has_ext_modules(self):
            return True

except ImportError:
    class PlatformDistribution(Distribution):
        def is_pure(self):
            return False

        def has_ext_modules(self):
            return True


setup(
    name='pymediainfo',
    author='Louis Sautier',
    author_email='sautier.louis@gmail.com',
    url='https://github.com/sbraz/pymediainfo',
    project_urls={
        "Documentation": "https://pymediainfo.readthedocs.io/",
        "Bugs": "https://github.com/sbraz/pymediainfo/issues",
    },
    description="""A Python wrapper for the mediainfo library.""",
    long_description=long_description,
    packages=find_packages(),
    namespace_packages=[],
    include_package_data=True,
    zip_safe=False,
    license='MIT',
    data_files=data_files,
    use_scm_version=True,
    python_requires=">=3.7",
    setup_requires=["setuptools_scm"],
    install_requires=["importlib_metadata; python_version < '3.8'"],
    package_data={'pymediainfo': bin_files},
    distclass=PlatformDistribution,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "License :: OSI Approved :: MIT License",
    ]
)
