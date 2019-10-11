
# ASC Media Hash List (ASC-MHL) Format Sample Implementation

> The software in this repository aids the ongoing specification process of the ASC-MHL format by the Advanced Data Management Subcommittee of the ASC Motion Imaging Technology Council at the [American Society of Cinematographers](https://theasc.com) (ASC). 
> 
> This software is work in progress and is not intended to be used as a reference  or in production (yet).
> 
> In case you are looking for the current, original specification of MHL, please take a look at [https://mediahashlist.org](https://mediahashlist.org).

Ensuring file integrity when backing up and verifying files during production and post production is of utmost importance. The ASC-MHL is used to create a chain of custody by tracking each and every copy made between the media’s initial download on set, all the way through to final archival.

The ASC-MHL uses common checksum methods for hashing files and folders, but standardizes what information is gathered, where the checksum is placed, and documents these hashes together with essential file metadata in an XML format that is human readable.

## Features

The ASC-MHL sample implementation can

* create ASC-MHL XML files based on given file hierarchies in a file system
* verify hashes against previous generations of ASC-MHL files
* export hashes for use in other systems

ASC-MHL supports the hash formats

* xxHash
* MD5
* SHA1
* SHA256
* C4

## Repository content

The ASC-MHL sample implementation consists of:

* ``README.md`` – Overview of features, installation, and usage of the sample implementation
* ``asc-mhl.py`` –  A command line tool for creating and verifying ASC-MHL files, written in Python 3
* ``Scenarios/`` – Additional bash scripts that showcase different scenarios for using the ASC_MHL command line tool


## Getting started

The ``asc-mhl.py`` tool requires a few dependencies that need to be installed first. 

For installing system dependencies on macOS [Homebrew](https://brew.sh) is recommended.

### System requirements

Make sure you have Python 3 installed:

```shell
$ brew install python3
$ brew postinstall python3
```

Install dependencies using a [Virtual Environment](https://docs.python.org/3/tutorial/venv.html):

```shell
$ python3 -m venv env
$ source env/bin/activate
$ pip3 install -r requirements.txt
```

> As of now, this process has only been tested on macOS 10.13.

## Running ``asc-mhl.py``

Here are the steps to use and learn more about the ``asc-mhl.py`` tool:

```shell
$ git clone https://github.com/pomfort/asc-mhl-tools.git
$ cd asc-mhl-tools
$ ./asc-mhl.py --help
$ ./asc-mhl.py verify --help
```
The most important command is the ``verify`` command:

```
$ asc-mhl.py verify --help
Usage: asc-mhl.py verify [OPTIONS] FOLDERPATH

  Verify a folder and create a new ASC-MHL file

Options:
  -n, --name TEXT                 Full name of user
  -u, --username TEXT             Login name of user
  -c, --comment TEXT              Comment string for human readable context
  -h, --hashformat [xxhash|MD5|SHA1]
  -g, --generationnumber TEXT     Generation number to verify against
  -s, --simulate                  Simulate only, don't write new ascmhl file
  -d, --directoryhashes           Log calculated directory hashes
  -wx, --write-xattr              Write hashes as xattr to file system
  -v, --verbose                   Verbose output
  --help                          Show this message and exit.
```

Here is the basic use case for creating an ASC-MHL file for all files in a folder:

```shell
$ ./asc-mhl.py verify /PATH/TO/FOLDER/
```

The output will look like this:

```
  xxhash: 0ea03b369a463d9d                 new       : Clips/A002C006_141024_R2EC.mov
  xxhash: 7680e5f98f4a80fd                 new       : Clips/A002C007_141024_R2EC.mov
  xxhash: 3ab5a4166b9bde44                 new       : Sidecar.txt    
```

And the new folder ``/PATH/TO/FOLDER/asc-mhl/`` will contain the first ASC-MHL file.

For more advanced use of ``asc-mhl.py`` please see the scripts in the ``Scenarios``folder (see below).

## Running ``Scenarios`` scripts

The scripts in the ``Scenarios`` folder implement several scenarios and output of the ``asc-mhl.py`` tool.

```shell
$ cd Scenarios
$ ./scenario01.sh
...
```

These scripts use the folder structure in ``Template/`` as a template and creates new folder structures and ASC-MHL files in a new folder ``Temp/``.

Sample output of all scenario scripts can be found in the [README.md](Scenarios/README.md) file of the ``Scenarios/`` folder. 
The created ASC-MHL files can also be found in the ``Output/`` folder. 

## Licensing

The code in this project is licensed under MIT license.
