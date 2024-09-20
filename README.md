# dicomsync

[![CI](https://github.com/sjoerdk/dicomsync/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/sjoerdk/dicomsync/actions/workflows/build.yml?query=branch%3Amain)
[![PyPI](https://img.shields.io/pypi/v/dicomsync)](https://pypi.org/project/dicomsync/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/dicomsync)](https://pypi.org/project/dicomsync/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)

Synchronize medical imaging studies between storage modalities

* Adds control, logging and error handling to copying medical imaging data
* Queries and copies to make sure imaging studies exist on both sides
* Supports DICOM file folders and XNAT pre-archive currently


## Installation
```
pip install dicomsync
```

## Usage

See /examples folder

## Development
To set up for development of dicomsync:
* git clone from github
* Install dependencies:
```
poetry install
```
* Add pre-commit hooks:
```
pre-commit install 
```
* To check code before committing:
```
pre-commit run
```

## Design notes
Choices and intentions for this library. Guideline for development.

The goal of dicomsync is to make it easier to transfer medical imaging studies between
different places. Some practical examples:
* Avoiding duplicate uploads. Make it easy to do a `sync` operation multiple times
(after errors) without worry.
* Logging. Starting and leaving a multi-day upload, coming back and knowing what happened.

The main objects are `ImagingStudy` and `Place`. dicomsync works with imaging studies 
that can exists in different places. Initial places can be XNAT, Local folder, 
local zipfile. Each place tends to have its own ImagingStudy subclass

### First version simplifications
Rabbit holes avoided in the first version
* No universal intermediate data structures. It would be great to have a universal
dicomsync internal data structure. For ImagingStudy subtype you define 
a `to_dicomsync()` and `from_dicomsync()` methods. However this is way to involved for now.
We will stick with `to_specific_place()` methods for each individual place.
