from setuptools import setup, find_packages


setup(
    name='pymediainfo',
    version='1.4.1',
    author='Patrick Altman',
    author_email='paltman@gmail.com',
    url='https://github.com/sbraz/pymediainfo',
    description="""A Python wrapper for the mediainfo library.""",
    packages=find_packages(),
    namespace_packages=[],
    include_package_data=True,
    zip_safe=False,
    license='MIT',
    install_requires=[
        'six>=1.8.0',
    ],
)
