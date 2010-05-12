from setuptools import setup, find_packages

import pymediainfo

setup(
    name='pymediainfo',
    version = pymediainfo.__version__,
    author='Patrick Altman',
    author_email='paltman@gmail.com',
    url='git@github.com/paltman/pymediainfo.git',
    description="""A Python wrapper for the mediainfo command line tool.""",
    packages=find_packages(),
    namespace_packages = [],
    include_package_data = True,
    zip_safe=False,
    license='MIT',
    install_requires=['simplejson',]
)
