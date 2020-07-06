
# ASC Media Hash List (ASC MHL)

> The software in this repository aids the ongoing specification process of the ASC MHL format by the Advanced Data Management Subcommittee of the ASC Motion Imaging Technology Council at the [American Society of Cinematographers](https://theasc.com) (ASC). 
> 
> This software is work in progress and is not intended to be used in production (yet).
> 
> In case you are looking for the current, original specification of MHL, please take a look at [https://mediahashlist.org](https://mediahashlist.org).

Ensuring file integrity when backing up and verifying files during production and post production is of utmost importance. The ASC MHL is used to create a chain of custody by tracking each and every copy made between the media’s initial download on set, all the way through to final archival.

The ASC MHL uses common checksum methods for hashing files and folders, but standardizes what information is gathered, where the checksum is placed, and documents these hashes together with essential file metadata in an XML format that is human readable.

This repository holds all information about the document format,  a reference implementation, and tools.

## ASC MHL Format Specification

The ASC MHL consists of a 

* definition of naming conventions for the ascmhl folder and the file names of its content
* XML schema for the ASC MHL files
* definition for the chain file

The schema definition can be found in the `./xsd` folder.

## `mhllib` Reference Implementation 

The implementation of a reference library aims to be used in applications and tools dealing with ASC MHL files. The library takes responsibility of dealing with complex use cases of nesting and assembling of information.

The reference library covers

* reading ascmhl folders and their contents
* parsing and writing of ASC MHL XML files
* parsing and writing ASC MHL chain files
* dealing with nested mhl folders

ASC MHL supports the hash formats

* xxHash (32-bit, 64-bit, and latest 128-bit/XXH3)
* MD5
* SHA1, SHA256
* C4

The source code for `mhllib` can be found in the `./mhl` folder.

## The `ascmhl` Tool

The `ascmhl` tool is a command line tool based on `mhllib` that allows to perform typical activities for the use cases of ASC MHL.

The ASC MHL tool implementation can

* create and extend ASC MHL history for given files and entire file hierarchies in a file system,
* output information about recorded history (summary of history or detailed information about single files), and
* verify files and entire file hierarchies.

The source code for the `ascmhl` tool can be found in the ``./ascmhl.py` file.

Typical scenarios, sample CLI output, and generated ASC MHL files can be found in the ``examples/scenarios`` folder.


## Getting started

The `mhllib` as well as the `ascmhl.py` tool require a few dependencies that need to be installed first. 

For installing system dependencies on macOS [Homebrew](https://brew.sh) is recommended.

### System requirements

```shell
$ ./asc-mhl.py --help
$ ./asc-mhl.py verify --help

Make sure you have Python 3 installed:

```shell
$ brew install python3
$ brew postinstall python3
```

Download the source code and install dependencies using a [Virtual Environment](https://docs.python.org/3/tutorial/venv.html):

```shell
$ git clone https://github.com/ascmitc/mhl.git
$ cd mhl
$ python3 -m venv env
$ source env/bin/activate
$ pip3 install -r requirements.txt
```

> As of now, this process has only been tested on macOS 10.13.

## Running `ascmhl.py`

The asc-mhl toll can be used to work with 

* entire file hierarchies (commands `seal`, `check`, and `diff`), 
* asc-mhl history folders (command `info`), and 
* on single files or lists of files (commands `record`, `verify`, `dirhash`, and `history`).

Additional utility commands:
* for validating MHL (command `validate`)

Implementation status 2020-07-03:

* __Implemented__: `seal`, `check`, `record`, `dirhash`, `validate`
* __Not implemented yet__: `diff`, `info`, `verify`, `history`

_The commands are also marked below with their current implementation status._


### Working with file hierarchies

The most common commands when using the `mhl-too.py` in data management scenarios are the `seal` and the `check` commands. 

Sealing a folder / drive with the `seal` command traverses through a folder hierarchy, hashes all found files and compares ("verifies") the hashes against the records in the `asc-mhl` folder (if present). The command creates a new generation (or an initial one) for the content of an entire folder at the given folder level. It can be used to document all files in a folder or drive with all verified or newly created file hashes of the moment the `seal` command ran.

Checking a folder / drive with the `check` command traverses through the content of a folder, hashes all found files and compares ("verifies") the hashes against the records in the `asc-mhl` folder. The `check` command behaves like a `seal` command, but doesn't write new generations. It can be used to verify the content of a received drive with existing asc-mhl information.

The `diff` command also traverses through the content of a folder / drive.  The `diff` command thus behaves like the `check` command, but the `diff` command does not hash any files (e.g. doesn't do file verification) and thus is much faster in execution. It can be used to print all files that are existent in the file system and are not registered in the `asc-mhl` folder yet, and all files that are registered in the `asc-mhl` folder but that are missing in the file system.


#### The `seal` command _implemented_

The `seal` command traverses through a folder hierarchy (such as a folder with media files, a camera card, or an entire drive). The command hashes all files and the hashes are compared against records in the `asc-mhl` folder.

The command detects, prints error, and exits with a non-0 exit code if it finds files that are registered in the `asc-mhl` folder but that are missing in the file system. 

Files that are existent in the file system but are not registered in the `asc-mhl` folder yet, are registered as new entries in the newly created generation(s).

The `seal` command takes the root path of the file hierarchy as the parameter:

```
$ mhl seal /path/to/folder/
```

It works on folders with or without an `asc-mhl` folder within the given folder hierarchy, and creates a new `asc-mhl` folder at the given folder level if none is present before.

`asc-mhl` folders further down the file hierarchy are read, handled, and referenced in top-level `asc-mhl` folders. Existing `asc-mhl` folders further down the folder structure will also get a new generation added.

Implementation:

* _read (recursive) mhl history (mhllib)_
* _traverse folder_
 	* _hash each file_
	* _if `asc-mhl` folder exists, compare ("verify") hash (mhllib)_
	* _on error (including mismatching hashes):_
		* _print error_
	 	* _continue_
 	* _add files to new generation if not present yet_
* _compare found files in file system with records in ascmhl folder and warn if files are missing that are recorded in the ascmhl folder_
* _create new generation(s) (mhllib)_


#### The `check` command _implemented_

The `check` command traverses through the content of a folder, hashes all found files and compares ("verifies") the hashes against the records in the `asc-mhl` folder.

The command detects, prints errors, and exits with a non-0 exit code for

* all files that are existent in the file system but are not registered in the `asc-mhl` folder yet, and
* all files that are registered in the `asc-mhl` folder but that are missing in the file system. 

It is run with the root path of the file hierarchy as the parameter.

```
$ mhl check /path/to/folder/
```

If no `asc-mhl` folder is found on the root level, an error is thrown.

`asc-mhl` folders further down the file hierarchy are also read, and its recorded hashes are used for verification.

Implementation:

* _error if no mhl folder found on root level_
* _read (recursive) mhl history (mhllib)_
* _traverse folder_
	* _hash each file_
	* _compare ("verify") hash (mhllib)_
	* _on error (including mismatching hashes):_
		* _print error_
	 	* _continue_
* _compare found files in file system with records in ascmhl folder and warn if files are missing that are recorded in the ascmhl folder_
* _end with exit !=0 if at least one of the files has failed, a file was missing, or new files have been found_


#### The `diff` command _not implemented yet_

The `diff` command is very similar to the `check` command, only that it doesn't create hashes and doesn't verify them. It can be used to quickly check if a folder structure has new files that have not been recorded yet, or if files are missing.

The command detects, prints errors, and exits with a non-0 exit code for

* all files that existent in the file system but not registered in the `asc-mhl` folder yet, and
* all files that are registered in the `asc-mhl` folder but that are missing in the file system. 

It is run with the root path of the file hierarchy as the parameter.

```
$ mhl diff /path/to/folder/ 
```

If no `asc-mhl` folder is found on the root level, an error is thrown.

`asc-mhl` folders are read recursively. 

Implementation:

* _error if no mhl folder found on root level_
* _read (recursive) mhl history (mhllib)_
* _traverse folder_
	* _on missing file:_
		* _print error_
	 	* _continue_
* _compare found files in file system with records in ascmhl folder and warn if files are missing that are recorded in the ascmhl folder_
* _end with exit !=0 if at least one of the files has failed, a file was missing, or new files have been found_



### Working with a `asc-mhl` folder

The `asc-mhl` folder contains well readable XML files, but the number of recorded files, generations, hash entries, verification info and so forth adds up to an amount of information that cannot be quickly understood. 

The `info` command helps to get a quick overview of the contents of the stored information in an `asc-mhl` folder. 


#### The `info` command _not implemented yet_

The `info` command can print

* a summary (with the `-s` option) of the information in an ascmhl folder, such as number of recorded files, and a list of the generations with their creator info, and/or
* a list (with the `-l` option) of all file (and folder) records stored in an ascmhl folder, together with relative file paths, file size, and known file hashes.

It is run with the path to a specific `asc-mhl`folder.

```
$ mhl info [-s|-l] /path/to/asc-mhl/ 
```

Implementation:

* _error if no mhl folder found on root level_
* _read (recursive) mhl history (mhllib)_
* _if summary option:_
	* _print summary_
* _if list option:_
	* _for each file record_
		* _print file info, hashes, etc._


### Working with single files

In some scenarios "sealing" and "checking" entire folder structures is not sufficient enough, and finer control of the processes files is needed. 

For that the `record`, `verify`, and `history` commands are used.

Recording single files in a new generation with the `record` command allows to add single files to an existing folder structure and create new generations only with records of these files.

Hashing and verifying single files against hash information stored in the `asc-mhl` folder  allows to "check" single files without the need for a (probably much longer running) check of the integrity of the entire folder structure. 

The `history` command prints the known history of a single file with details about all generations.


#### The `record` command _implemented_

The `record` command creates a new generation in the mhl-history. This can be used for instance when adding single files to an already mhl-managed file hierarchy. It is run with the root path of the file hierarchy as well as one or multiple paths to the individual files and folders to be recorded as the parameters.

```
$ mhl record /path /path/to/single/file
```

A new generation is created in all `asc-mhl` folders below the given root path (e.g. in a nested mhl-history). If no mhl-history is present yet, an error is thrown.

The following files will not be handled by this command:

* that are referenced in the existing ascmhl history but not specified as input, and
* files that are neither referenced in the history nor specified as input.

Implementation:

* _read (recursive) mhl-history (mhllib) starting from root path_
* _for each file from input_
	* _check if file is not recorded in `asc-mhl` folder yet_
	* _hash file_
	* _add record for file to new generation (mhllib)_
		* _add new generation if necessary in appropriate `asc-mhl` folder (mhllib)_


#### The `verify` command _not implemented yet_

The `verify` command can be used to verify a single or multiple files. It is run with either 

* the path to a single file, or
* a text file with paths to multiple files

as the parameter.

```
$ mhl verify /path/to/single/file
$ mhl verify -l list/of/files.txt
```

The command looks for an `asc-mhl` folder in the folders above the given files. If no mhl-history is present yet, an error is thrown.

If used with the `-l` option, all files in the list must be contained in the same (recursive) mhl-history. 

Implementation:

* _if input is `-f`: create a list of files from input_
* _find mhl-history information in the path above (mhllib)_
	* _error of no `asc-mhl` folder is found_
* _read (recursive) mhl-history (mhllib)_
* _for each file from input_
	* _hash each file_
	* _compare hashes (mhllib)_ 
* _if file is not found in mhl-history, throw error_
* _on error (including mismatching hashes):_
	* _don't break_
	* _print error_
	* _end with exit !=0 if at least one of the files has failed_


#### The `dirhash' command _implemented_

The `dirhash` command creates and outputs the directory hash by hashing the contained files of the given directory path.

The directory hash can be used to quickly verify if the state of a folder structure is still the same compared to the last generation created with a `seal` command (manually comapre with the hash in the `<root>` tag in the ASC MHL file).


```
$ mhl dirhash /path/to/folder
```

Implementation:

* _traverse folder_
 	* _hash each file_
* _print directory hash_


#### The `history` command _not implemented yet_

The `history` command outputs information about the full and detailed history information about one file.

```
$ mhl history /path/to/file
```

The command outputs each generation where the file has been handled, including date, creator info, activity, hash, and absolute path.

Implementation:

* _find mhl-history information in the path above (mhllib)_
	* _error of no `asc-mhl` folder is found_
* _print detailed info for file_ 


### Other commands

#### The `validate` command _implemented_

The `validate` command validates a given ASC MHL file against the XML XSD. This command can be used to ensure the creation of syntactically valid ASC MHL files, for example during  implementation of tools creating ASC MHL files.




