from setuptools import setup, find_packages


setup(
    name='pymediainfo',
    version='1.4.1',
    author='Patrick Altman',
    author_email='paltman@gmail.com',
    url='git@github.com/paltman/pymediainfo.git',
    description="""A Python wrapper for the mediainfo command line tool.""",
    packages=find_packages(),
    namespace_packages=[],
    include_package_data=True,
    zip_safe=False,
    license='MIT',
    install_requires=[
        'beautifulsoup4>=4.0.0',
        'six>=1.8.0',
        'lxml>=3.4.1',
    ],
)
