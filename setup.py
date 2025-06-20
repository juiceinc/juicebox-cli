import os
import re
from codecs import open
from os import path
from setuptools import setup, find_packages

from juicebox_cli import __version__

here = path.abspath(path.dirname(__file__))


# Get the long description from the README file
def get_version(package):
    """Return package version as listed in `__version__` in `init.py`."""
    with open(os.path.join(package, "__init__.py")) as f:
        return re.search("__version__ = ['\"]([^'\"]+)['\"]", f.read())[1]
    return None


import pathlib

long_description = pathlib.Path("README.rst").read_text()

requirements = ["boto3>=1.28.0", "click>=8.0", "requests>=2.30.0"]

# Have setuptools generate the entry point
# wrapper scripts.
entry_points = {
    "console_scripts": [
        "juice=juicebox_cli.cli:cli",
    ],
}

setup(
    name="juicebox-cli",
    version="3.0.0",
    description="Juicebox CLI",
    long_description=long_description,
    author="Juice Analytics",
    author_email="casey.wireman@juiceanalytics.com",
    packages=find_packages(exclude=["contrib", "docs", "tests*"]),
    install_requires=requirements,
    entry_points=entry_points,
    url="https://github.com/juiceinc/juicebox_cli",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business",
        "Topic :: Internet",
        "Topic :: Communications :: File Sharing",
    ],
)
