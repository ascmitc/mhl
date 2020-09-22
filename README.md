
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

The `ascmhl` tool is a command line tool (`./ascmhl.py`) based on `mhllib` that allows to perform typical activities for the use cases of ASC MHL.

The ASC MHL tool implementation can

* create and extend ASC MHL history for given files and entire file hierarchies in a file system,
* output information about recorded history (summary of history or detailed information about single files), and
* verify files and entire file hierarchies.

Typical scenarios, sample CLI output, and generated ASC MHL files can be found in the [README.md](examples/scenarios/README.md) file in the ``examples/scenarios`` folder.

## Getting started

The `mhllib` as well as the `ascmhl` tool require a few dependencies that need to be installed first. 

For installing system dependencies on macOS [Homebrew](https://brew.sh) is recommended.

### System requirements

```shell
$ ./ascmhl.py --help
$ ./ascmhl.py verify --help
```

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


## Installing `ascmhl`

> TBD


## Common Scenarios for `ascmhl.py`

The ascmhl tool can be used to 

* create new MHL generations for given files and folders (command `create`), 
* verify the state of files and folders against the MHL history (command `verify`),
* print differences between the records in the MHL history and given files and folders (command `diff`), and
* print information about an MHL history (command `info`).

Additional utility commands:
* for validating MHL (command `_validatexml`)


### Working with file hierarchies (with completeness check)

The most common commands when using the `mhl-tool.py` in data management scenarios are the `create` and the `check` commands in their default behavior (without subcommand options). 

Sealing a folder / drive with the `create` command traverses through a folder hierarchy, hashes all found files and compares the hashes against the records in the `ascmhl` folder (if present). The command creates a new generation (or an initial one) for the content of an entire folder at the given folder level. It can be used to document all files in a folder or drive with all verified or newly created file hashes of the moment the `create` command ran.

Checking a folder / drive with the `verify` command traverses through the content of a folder, hashes all found files and compares the hashes against the records in the `ascmhl` folder. The `verify` command behaves like a `create` command (both without additional options), but doesn't write new generations. It can be used to verify the content of a received drive with existing ascmhl information.

The `diff` command also traverses through the content of a folder / drive.  The `diff` command thus behaves like the `verify` command, but the `diff` command does not hash any files (e.g. doesn't do file verification) and thus is much faster in execution. It can be used to print all files that are existent in the file system and are not registered in the `ascmhl` folder yet, and all files that are registered in the `ascmhl` folder but that are missing in the file system.


### Working with single files (without completeness check)

In some scenarios working with an entire folder structure is not adequate, and finer control of the processes files is needed. For those scenarios the `create` and `verify` commands are used with additional subcommand options.

Adding single files in a new generation with the `create -sf` ("single files, no completeness check") command allows to add single files to an existing folder structure and create new generations only with records of these files.

Hashing and verifying single files against hash information stored in the `ascmhl` folder with the `verify -sf` ("single files") command allows to "check" single files without the need for a (probably much longer running) check of the integrity of the entire folder structure. 

The `info -sf` ("single file") command prints the known history of a single file with details about all generations.


## Commands of `ascmhl.py`

_Implementation status 2020-09-08:_

* __Implemented__: `create`, `verify` (partially), `diff`, `_validatexml`
* __Not implemented yet__: `info`

_The commands are also marked below with their current implementation status._


### The `create` command

The `create` command hashes all files given with the different options and creates a new generation in the mhl-history with records for all hashed files. The command compares the hashes against the hashes stored in previous generations if available.

#### `create` default behavior (for file hierarchy, with completeness check)

The `create` command traverses through a folder hierarchy (such as a folder with media files, a camera card, or an entire drive). The command hashes all files (not ignored by the given ignore patterns given with the `-i` or `-if` options) and the hashes are compared against records in the `ascmhl` folder. It records all hashed files in the new generation. Directory hashes are computed and also recorded in the new generation.

The command detects, prints error, and exits with a non-0 exit code if it finds files that are registered in the `ascmhl` folder but that are missing in the file system. 

Files that are existent in the file system but are not registered in the `ascmhl` folder yet, are registered as new entries in the newly created generation(s).

The `create` command takes the root path of the file hierarchy as the parameter:

```
$ ./ascmhl.py create [-i ignore pattern|-if /path/to/ignore-file.txt] /path/to/folder/
```

It works on folders with or without an `ascmhl` folder within the given folder hierarchy, and creates a new `ascmhl` folder at the given folder level if none is present before.

`ascmhl` folders further down the file hierarchy are read, handled, and referenced in top-level `ascmhl` folders. Existing `ascmhl` folders further down the folder structure will also get a new generation added.

Implementation:

```
read (recursive) mhl history (mhllib)
traverse folder
 	hash each file
	if `ascmhl` folder exists, compare hash (mhllib)
	on error (including mismatching hashes):
		print error
	 	continue
 	add files to new generation if not present yet
compare found files in file system with records in ascmhl folder and \
   warn if files are missing that are recorded in the ascmhl folder
create new generation(s) (mhllib)
```

#### `create` with `-sf` option(s) (for single file(s), no completeness check)

The `create` command with `-sf` option is run with the root path of the file hierarchy as well as one or multiple paths to the individual files to be recorded as the parameters.

This command can be used for instance when adding single files to an already mhl-managed file hierarchy.

```
$ ./ascmhl.py create /path/to/root/folder -sf /path/to/single/file1 [-sf /path/to/single/file2 ..]
```

A new generation is created in all `ascmhl` folders below the given root path (e.g. in a nested mhl-history). If no mhl-history is present yet, an error is thrown.

No other files than the ones specified as `-sf` options are handled by this command.

Implementation:

```
read (recursive) mhl-history (mhllib) starting from root path
for each file from input
	check if file is not recorded in `ascmhl` folder yet
	hash file
	add record for file to new generation (mhllib)
		add a new generation if necessary in appropriate `ascmhl` folder (mhllib)
```

### The `verify` command

#### `verify` default behavior (for file hierarchy, with completeness check)

The `verify` command traverses through the content of a folder, hashes all found files  (filtered by the ignore patterns from the `ascmhl` folder) and compares the hashes against the records in the `ascmhl` folder.

The command detects, prints errors, and exits with a non-0 exit code for

* all files that are existent in the file system but are not registered in the `ascmhl` folder yet, and
* all files that are registered in the `ascmhl` folder but that are missing in the file system. 

It is run with the root path of the file hierarchy as the parameter.

```
$ ./ascmhl.py verify /path/to/folder/
```

If no `ascmhl` folder is found on the root level, an error is thrown.

`ascmhl` folders further down the file hierarchy are also read, and its recorded hashes are used for verification.

Implementation:

```
error if no mhl folder found on root level
read (recursive) mhl history (mhllib)
traverse folder
	hash each file (filtered by ignore patterns from mhl folder)
	compare hash (mhllib)
	on error (including mismatching hashes):
		print error
	 	continue
compare found files in file system with records in ascmhl folder and \
  warn if files are missing that are recorded in the ascmhl folder
end with exit !=0 if at least one of the files has failed, a file was \
  missing, or new files have been found
```


#### `verify` with `-sf` option (for single files, no completeness check) _[not implemented yet]_

The `verify` command can be used to verify a single or multiple files. It is run with either 

* the path to a single file, or
* a text file with paths to multiple files

as the parameter.

```
$ ./ascmhl.py verify -sf /path/to/single/file
$ ./ascmhl.py verify -sf -l list/of/files.txt
```

The command looks for an `ascmhl` folder in the folders above the given files. If no mhl-history is present yet, an error is thrown.

If used with the `-l` option, all files in the list must be contained in the same (recursive) mhl-history. 

Implementation:

```
if input is `-l`: create a list of files from input
find mhl-history information in the path above (mhllib)
	error of no `ascmhl` folder is found
read (recursive) mhl-history (mhllib)
for each file from input
	hash each file
	compare hashes (mhllib)
if file is not found in mhl-history, throw error
on error (including mismatching hashes):
	don't break
	print error
	end with exit !=0 if at least one of the files has failed
```


#### `verify` with `-dh` subcommand option (for directory hash) _[not implemented yet]_

The `verify` command with the `-dh` subcommand option creates the directory hash by hashing the contained files of the given directory path (filtered by the ignore patterns from the `ascmhl` folder) and compares it with the to-be-expected directory hash calculated from the file hashes (same calculation as the `info` command with the `-dh` subcommand option).


```
$ ./ascmhl.py verify -dh /path/to/folder
```

Implementation:

```
find mhl-history information in the path above (mhllib)
	error of no `ascmhl` folder is found
read (recursive) mhl history (mhllib)
calculate to-be-expected directory hash from file hashes
traverse folder
 	hash each file
calculate actual directory hash
compare to-be-expected directory hash with actual directory hash
on error (including mismatching hash):
	print error
	end with exit !=0
```

### The `diff` command

The `diff` command is very similar to the `verify` command in the default behavior, only that it doesn't create hashes and doesn't verify them. It can be used to quickly check if a folder structure has new files that have not been recorded yet, or if files are missing.

The command detects, prints errors, and exits with a non-0 exit code for

* all files that existent in the file system but not registered in the `ascmhl` folder yet, and
* all files that are registered in the `ascmhl` folder but that are missing in the file system. 

It is run with the root path of the file hierarchy as the parameter.

```
$ ./ascmhl.py diff /path/to/folder/ 
```

If no `ascmhl` folder is found on the root level, an error is thrown.

`ascmhl` folders are read recursively. 

Implementation:

```
error if no mhl folder found on root level
read (recursive) mhl history (mhllib)
traverse folder
	on missing file:
		print error
	 	continue
compare found files in file system with records in ascmhl folder \
  and warn if files are missing that are recorded in the ascmhl folder
end with exit !=0 if at least one of the files has failed, a file was \
  missing, or new files have been found
```


### The `info` command _[not implemented yet]_

#### `info` default behavior _[not implemented yet]_

The `ascmhl` folder contains well readable XML files, but the number of recorded files, generations, hash entries, verification info and so forth adds up to an amount of information that cannot be quickly understood. The `info` command helps to get a quick overview of the contents of the stored information in an `ascmhl` folder. 

The `info` command prints
* a summary (with the `-s` subcommand option) of the information in an ascmhl folder, such as number of recorded files, and a list of the generations with their creator info, and/or
* a list (with the `-l` option) of all file (and folder) records stored in an ascmhl folder, together with relative file paths, file size, and known file hashes.

It is run with the path to a specific `ascmhl`folder.

```
$ ./ascmhl.py info [-s|-l] /path/to/ascmhl/ 
```

Implementation:

```
error if no mhl folder found on root level
read (recursive) mhl history (mhllib)
if summary option:
	print summary
if list option:
	for each file record
		print file info, hashes, etc.
```


#### `info` with the `-sf` subcommand option _[not implemented yet]_

The `info` command with the `-sf` subcommand option outputs information about the full and detailed history information about one file.

```
$ ./ascmhl.py info -sf /path/to/file
```

The command outputs each generation where the file has been handled, including date, creator info, activity, hash, and absolute path.

Implementation:

```
find mhl-history information in the path above (mhllib)
	error of no `ascmhl` folder is found
print detailed info for file
```


#### `info` with the `-dh` subcommand option _[not implemented yet]_

The `info` command with the `-dh` subcommand option prints
* the directory hash of a folder computed from stored file hashes of an `ascmhl` folder (with the `-dh` option).

The directory hash can be used to quickly verify if the state of a folder structure is still the same compared to the last generation created with a `create` command (manually compare with the hash in the `<root>` tag in the ASC MHL file).

It is run with the path to a specific `ascmhl`folder and the path to the desired folder for the computed directory hash.

```
$ ./ascmhl.py info -dh /path/to/ascmhl/ /path/to/sub/folder 
```

Implementation:

```
error if no mhl folder found on root level
read (recursive) mhl history (mhllib)
calculate directory hash from file hashes
print directory hash
```


### The `validatexml` command

The `validatexml` command validates a given ASC MHL file against the XML XSD. This command can be used to ensure the creation of syntactically valid ASC MHL files, for example during  implementation of tools creating ASC MHL files.


```
$ ./ascmhl.py validatexml /path/to/ascmhl/XXXXX.mhl
```


