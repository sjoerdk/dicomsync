# History

## V1.3.0 (2025-11-03)
* Drops python 3.9
* Adds python 3.12
* Updates XNAT
 
## V1.2.0 (2025-10-09)
* Fixes bugs in duplicate finding
* Fixes bugs query matching for study root folders
* Moves to uv package management, removes poetry and tox

## V1.0.1 (2025-05-23)
* Fixes readme for pypi

## V1.0.0 (2025-05-23)
Major breaking reworking resulting in version 1.
* Adds Domain concept: Domain holds Places under string key names and can find any StudyQuery
* Completes 'find' and 'send' functions which use StudyQuery (<place>:patient/study with wildcards).
* Cleans up object responsibilities. ImagingStudy no longer holds any data except a key. Place can give info on its ImagingStudies.
* Breaks loading of older settings files due to Place structure rewrite
* Simplifies CLI functions by using domain.
* Removes awkward SerializableXNATProjectPreArchive. Makes regular XNATProjectPreArchive serializable
* Add additional medium verbosity level: DEBUG level dicomsync without ultra-verbose urlib3 clutter
* Adds xnat server testing with mock pyxnat responses.


## v0.2.0 (2024-09-20)
* Adds some CLI methods

## v0.1.1 (2024-01-28)
* Fixes xnat study key matching (keys are now lower case)

## v0.1.0 (2024-01-20)

* Initial version
