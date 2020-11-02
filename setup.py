"""Setup script for HLM PV IMPORT"""

import os.path

import setuptools

# The directory containing this file
HERE = os.path.abspath(os.path.dirname(__file__))

# The text of the README file
with open(os.path.join(HERE, "README.md")) as fid:
    README = fid.read()

# This call to setup() does all the work
setuptools.setup(
    name="HLM_PV_Import",
    version="0.0.1",
    author="M.S.",
    author_email="",
    description="Updates the Helium Recovery DB with PV data.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/ISISNeutronMuon/HLM_PV_Import",
    license="",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Operating System :: Microsoft :: Windows :: Windows 10",

    ],
    packages=setuptools.find_packages(),
    include_package_data=True,
    entry_points={"console_scripts": ["HLM_PV_Import=HLM_PV_Import.__main__:main"]},
    python_requires=">=3.8.1"
)
