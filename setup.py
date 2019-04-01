#!/usr/bin/env python
import os
from setuptools import setup, find_packages

with open("README.rst") as f:
    long_description = f.read()

data_files = []
bin_files = []
cmdclass = {}

bin_license = 'docs/License.html'
if os.path.exists(bin_license):
    data_files.append(('docs', [bin_license]))
    bin_files.extend(['MediaInfo.dll', 'libmediainfo.*'])
    try:
        from wheel.bdist_wheel import bdist_wheel

        class platform_bdist_wheel(bdist_wheel):
            def finalize_options(self):
                bdist_wheel.finalize_options(self)
                # Force the wheel to be marked as platform-specific
                self.root_is_pure = False
            def get_tag(self):
                python, abi, plat = bdist_wheel.get_tag(self)
                # The python code works for any Python version,
                # not just the one we are running to build the wheel
                return 'py2.py3', 'none', plat

        cmdclass['bdist_wheel'] = platform_bdist_wheel
    except ImportError:
        pass

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
    cmdclass=cmdclass,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
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
