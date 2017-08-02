# copied from https://github.com/pypa/sampleproject/blob/master/setup.py
from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name = 'rdparse',
    version='0.0.1',
    description='A quick and dirty recursive descent parser written in Python 3',
    long_description=long_description,
    url="https://github.com/dougabugg/python-recursive-descent-parser",
    author="Douglas Rezabek",
    author_email="dougabugg (at) gmail.com",
    license="MIT",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
    ],
    keywords="recursive descent parsing parse parser frontend",
    packages=find_packages(),
    python_requires='>=3',
)