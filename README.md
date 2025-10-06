# dicomsync

[![CI](https://github.com/sjoerdk/dicomsync/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/sjoerdk/dicomsync/actions/workflows/build.yml?query=branch%3Amain)
[![PyPI](https://img.shields.io/pypi/v/dicomsync)](https://pypi.org/project/dicomsync/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/dicomsync)](https://pypi.org/project/dicomsync/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)

Synchronize medical imaging studies between storage modalities

![dicomsync logo](docs/resources/dicomsync.png)

* Copy and query medical imaging studies via CLI or python
* Avoids copying duplicate studies by querying
* Supports DICOM file folders, zipped studies and XNAT pre-archive


## Installation
```
pip install dicomsync
```

## Usage
An example of sending some dicom to some place.

## TLDR;
```bash
$ dicomsync init
$ dicomsync place add dicom_root my_studies /tmp/dicom_root   # add dicom place
$ dicomsync find my_studies:patient1*                         # show studies
$ dicomsync place add zipped_root zipped /tmp/dicom_zipped    # add zipped place 
$ dicomsync send my_studies:* zipped                          # send matching studies

$ dicomsync place add xnat_pre_archive the_xnat_project https://xnat.health-ri.nl <xnat_project_name> <xnat_username>
$  export 'XNAT_PASS=<xnat_password>'                         # set xnat password 
```

### Creating and querying a place 
Say you have some folders containing dicom files in patient/study structure:
```
/tmp/dicom_root + patient1 + study1 + file1.dcm
                |          |        | file2.dcm
                |          |        | file3.dcm
                |          |
                |          + study2 + file1.dcm
                |          |        | file2.dcm
                |          |
                |          + study3 + file1.dcm
                |                   | file2.dcm
                |  
                + patient2 + study1 + file1.dcm
                                    | file3.dcm
```

Add this location to dicomsync as a `place` called _my_studies_
```bash
$ dicomsync init
$ dicomsync place add dicom_root my_studies /tmp/dicom_root

# you can now see this as a place
$ dicomsync place list
key         place
----------  --------------------------------
my_studies  Root folder at '/tmp/dicom_root'

```

You can show all patients and studies _my_studies_ by using the `find` command:
```bash
$ dicomsync find my_studies:*
found 4:
my_studies:patient2/study1
my_studies:patient1/study3
my_studies:patient1/study2
my_studies:patient1/study1
```

The find query format is `<place>:<patient>/<study>`. You can use an astrisk `*` as a 
wildcard that matches any characters:
```bash
# All studies for patient1
$ dicomsync find my_studies:patient1*
found 3:
my_studies:patient1/study3
my_studies:patient1/study2
my_studies:patient1/study1

# only studies called study1 for any patient:
(base2) sjoerd@xps159500:/tmp$ dicomsync find my_studies:*study1
found 2:
my_studies:patient2/study1
my_studies:patient1/study1

# only a single study
$ dicomsync find my_studies:patient1/study2
found 1:
my_studies:patient1/study2
```

### Sending studies
This follows on from the usage example above: we have a `dicom_root` place called 
_my_studies_.

Now we create a second place and send some studies to it. This will be a `zipped_root`.
A folder that saves studies in the format `/<patient>/<study>.zip`

```bash
dicomsync place add zipped_root zipped /tmp/dicom_zipped

# there are now two places
dicomsync place list
key         place
----------  -----------------------------------------------
my_studies  Root folder at '/tmp/dicom_root'
zipped      Zipped DICOM Root folder at '/tmp/dicom_zipped'
```

Now we send a single study `my_studies:patient1/study2` to `zipped` using the `send` command:
```bash
$ dicomsync send my_studies:patient1/study2 zipped
dicomsync.cli.send INFO: Sending all studies matching StudyQuery 'my_studies:patient1/study2' to 'zipped'
dicomsync.cli.send INFO: found 1 studies matching StudyQuery 'my_studies:patient1/study2'.
dicomsync.cli.send INFO: Found '0' duplicate studies.Sending the rest: patient1/study2 (DICOMStudyFolder)
dicomsync.cli.send INFO: processing patient1/study2 (DICOMStudyFolder)
dicomsync.local INFO: Creating zip archive for /tmp/dicom_root/patient1/study2 in /tmp/dicom_zipped/patient1/study2.zip
```

The study has been sent. You can use `'*:*'` to find all studies in all places:
```bash
$ dicomsync find '*:*'
found 5:
my_studies:patient2/study1
my_studies:patient1/study3
my_studies:patient1/study2
my_studies:patient1/study1
zipped:patient1/study2
```

If you try to send the same study again, it will not be sent as it already exists:
```bash
$ dicomsync send my_studies:patient1/study2 zipped
2025-10-06 13:22:22 dicomsync.cli.send INFO: Sending all studies matching StudyQuery 'my_studies:patient1/study2' to 'zipped'
2025-10-06 13:22:22 dicomsync.cli.send INFO: found 1 studies matching StudyQuery 'my_studies:patient1/study2'.
2025-10-06 13:22:22 dicomsync.cli.send INFO: Found 1 duplicate studies.
2025-10-06 13:22:22 dicomsync.cli.send INFO: All studies were duplicates. Not sending anything.
```

You can send all studies. Duplicates will not be sent:
```bash
$ dicomsync send my_studies:* zipped
2025-10-06 13:23:42 dicomsync.cli.send INFO: Sending all studies matching StudyQuery 'my_studies:*/*' to 'zipped'
2025-10-06 13:23:42 dicomsync.cli.send INFO: found 4 studies matching StudyQuery 'my_studies:*/*'.
2025-10-06 13:23:42 dicomsync.cli.send INFO: Found '1' duplicate studies.Sending the rest: patient2/study1 (DICOMStudyFolder)
patient1/study3 (DICOMStudyFolder)
patient1/study1 (DICOMStudyFolder)
2025-10-06 13:23:42 dicomsync.cli.send INFO: processing patient2/study1 (DICOMStudyFolder)
2025-10-06 13:23:42 dicomsync.local INFO: Creating zip archive for /tmp/dicom_root/patient2/study1 in /tmp/dicom_zipped/patient2/study1.zip
2025-10-06 13:23:42 dicomsync.cli.send INFO: processing patient1/study3 (DICOMStudyFolder)
2025-10-06 13:23:42 dicomsync.local INFO: Creating zip archive for /tmp/dicom_root/patient1/study3 in /tmp/dicom_zipped/patient1/study3.zip
2025-10-06 13:23:42 dicomsync.cli.send INFO: processing patient1/study1 (DICOMStudyFolder)
2025-10-06 13:23:42 dicomsync.local INFO: Creating zip archive for /tmp/dicom_root/patient1/study1 in /tmp/dicom_zipped/patient1/study1.zip
```

### XNAT place
To add an XNAT pre-archive as a place:

```bash
$ dicomsync place add xnat_pre_archive the_xnat_project https://xnat.health-ri.nl <xnat_project_name> <xnat_username>
# set your xnat password in environment. Note the extra space in front of the command to avoid logging the command 
$  export 'XNAT_PASS=<xnat_password>' 
```


### Using dicomsync in scripts 
See the `/examples` folder for examples 

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
* Avoiding duplicate uploads. Make it easy to do a `send` operation multiple times
(after errors) without worry. Operations should be idempotent by default and minimize
work by default.
* Logging. Starting and leaving a multi-day upload, coming back and knowing what happened.

The main objects are `ImagingStudy` and `Place`. dicomsync works with imaging studies 
that can exists in different places. Initial places can be XNAT, Local folder, 
local zipfile. Each place tends to have its own ImagingStudy subclass

### First version simplifications
Rabbit holes avoided in the first version
* No universal intermediate data structures. It would be great to have a universal
dicomsync internal data structure. For ImagingStudy subtype you define 
a `to_dicomsync()` and `from_dicomsync()` methods. However, this is way too involved for now.
We will stick with `to_specific_place()` methods for each individual place.
