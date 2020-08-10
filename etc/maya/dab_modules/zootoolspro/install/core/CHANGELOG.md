## v1.1.0 (2019-09-15)


**Added**

- Updated CLI Commands to use subParsers which provides better validation, grouping and less code.
- Providing example on creating a Rez package for zootoolspro.
- setup CLI Command option for supporting copying .git folder.
- Descriptors can now support uninstalling.
- docstring updates.
- Added CHANGELOG.md


**Bug Fixes**
- fix importlib importError on py2.
- package.delete method no longer errors due to the use of os.rmdir, now uses shutil.rmtree.

## v1.1.1 (2019-09-15)

**Bug Fixes**
- Fix bundlePackages using old install package command args.


## v1.1.2 (2019-09-15)

**Bug Fixes**
- Preferences default path using double forward slash.
- Maya module scripts directory not being detected on linux.
- ReleasePackage command not install package when specified 

## v1.1.4 (2019-10-27)

**Bug Fixes**
- Removed Git dependency to bundle zootools packages.

## v1.1.5 (2019-10-27)

**Bug Fixes**
- Import Naming fix when running custom package startup.

## v1.1.6 (2019-11-14)

**Bug Fixes**

- Removed redundant packages.
- Zootools fails to load when dynamically loading packages into the environment.
- Fixed maya plugin log display a false positive.

## v1.1.7 (2019-11-15)

**Bug Fixes**

- Fixed IOError when running setupcommand when backup folder already exists.


## v1.1.8 (2019-11-16)

**Bug Fixes**

- Fix typeError when running setup command
- Removed windows specific error when running setup command

## v1.1.9 (2019-12-01)

**Bug Fixes**

- typeError when loading json

## v1.1.10 (2019-12-02)

**Bug Fixes**

 - zoo_cmd syntax command not found.
 
 
## v1.1.11 (2019-12-15)

**Bug Fixes**

 - standardized commands.
 
## v1.1.12 (2020-01-12)

**Bug Fixes**

 - Fix regression where packageInstall command name was changed.
 - Support for git descriptor ssh.
 
## v1.1.13 (2020-02-09)

**Bug Fixes**
 - Fix string_types check argument error.
 - Fix package class not maintaining original data as a cache.
 - Adding Author, email, description to zoo_package.json.
 - Refactor artistpalette boot to be in artist palette repo instead of plugin.
 
 **Added**
  - Provide the ability to return all repo commits after a certain tag.
  - Added displayName and description to package.py.
  
## v1.1.14 (2020-02-23)

**Bug Fixes**
 - Maya Extension Plugin to avoid loading menu when running through mayabatch or mayapy.
 
## v1.1.15 (2020-03-01)

**Added**
 - Added support for build version as part of the api and setup commands.
 
 ## v1.1.17 (2020-03-22)

**Added**
 - config property to set admin mode.
 - Descriptor can now be serialized to dict.
 - ported reload function from zoo_core.
 
 **Bug Fixes**
 - releasePackage command enforces version argument.
 - Fix python namespacing

## 1.1.18 (2020-04-11)

**Added**
 - Added createPackage command.