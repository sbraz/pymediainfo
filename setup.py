from setuptools import setup, find_packages

setup(
    name='pymediainfo',
    version='2.1.4',
    author='Louis Sautier',
    author_email='sautier.louis@gmail.com',
    url='https://github.com/sbraz/pymediainfo',
    description="""A Python wrapper for the mediainfo library.""",
    packages=find_packages(),
    namespace_packages=[],
    include_package_data=True,
    zip_safe=False,
    license='MIT',
    tests_require=["nose"],
    test_suite="nose.collector"
)
