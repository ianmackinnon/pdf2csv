import os
import setuptools

path = os.path.abspath(os.path.dirname(__file__))
exec(open(os.path.join(path, 'pdf2csv/version.py')).read())

with open("README.md", "r") as fp:
    long_description = fp.read()

setuptools.setup(
    name = "pdf2csv",
    version=__version__,
    author="Ian Mackinnon",
    author_email="imackinnon@gmail.com",
    description="Extract tabular data from PDF files by detecting table border lines",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ianmackinnon/pdf2csv",
    keywords='pdf csv convert scrape extract',
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    install_requires=['pdfminer.six'],
    python_requires='>=3',
    scripts=["scripts/pdf2csv"],
    setup_requires=["pytest-runner"],
    tests_requires=["pytest"],
)
