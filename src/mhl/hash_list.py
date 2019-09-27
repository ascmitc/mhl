from src.util.datetime import datetime_now_filename_string, datetime_isostring, datetime_now_isostring

from src.mhl import mhl_dir
from src.mhl.context import pass_context
from src.mhl.hash import *
from src.mhl.hash_entry import *
from src.mhl.hash_folder import *

from src.util import matches_prefixes
from src.util import logger

import click

import lxml
from lxml import objectify, etree, sax

import datetime
import time
import platform
import os
import subprocess
import re
import xattr
import tempfile
import binascii

# TODO: these should be defined dynamically. check the command invoked and the version programmatically so this doesn't have to be updated.
ascmhl_toolname_string = 'ascmhl-verify'
ascmhl_toolversion_string = '0.0.3'


class MediaHashList:
    """class for representing a list of media hashes, e.g. from an MHL file,
    also uses MediaHash and HashEntry class for storing information

    member variables:
    root_path -- root path for files
    media_hashes -- list of MediaHash objects
    generation_number -- generation number of the corresponding MHL file
    """

    def __init__(self, root_path):
        """init empty list"""
        self.root_path = root_path
        self.media_hashes = list()
        self.generation_number = 0

    def append_media_hash(self, media_hash):
        """add one MediaHash object"""
        self.media_hashes.append(media_hash)

    def append_media_hash_list(self, other_media_hash_list):
        """add all MediaHash objects from another media hash list"""
        self.media_hashes = self.media_hashes + other_media_hash_list.media_hashes

    # input: strings(relative path)
    def media_hash_for_relative_filepath(self, filepath):
        """retrieve the stored MediaHash object for a given relative path"""
        for media_hash in self.media_hashes:
            if media_hash.relative_filepath == filepath:
                return media_hash
        return None

    # input: array of strings (relative paths)
    def media_hash_list_for_relative_filepaths(self, filepaths):
        """retrieve multiple MediaHash objects for a list of given relative paths"""
        directory_media_list = MediaHashList(self.root_path)
        for filepath in sorted(filepaths):
            directory_media_hash = self.media_hash_for_relative_filepath(filepath)
            if directory_media_hash is not None:
                directory_media_list.append_media_hash(directory_media_hash)
            else:
                print("WARNING: couldn't find MediaHash for \"{0}\"".format(filepath))
        return directory_media_list


class HashListReader:
    """class to read an MHL file into a MediaHashList object

    this is used to read MHL files of earlier generations

    member variables:
    filepath -- path to MHL file
    media_hash_list -- MediaHashList object representing the MHL file
    generation_number -- generation number of the MHL file
    """

    def __init__(self, filepath, generation_number):
        self.filepath = filepath
        self.media_hash_list = None
        self.generation_number = generation_number

    def parse(self):
        """parsing the MHL XML file and building the MediaHashList for the media_hash_list member variable"""

        print("Verifying against hashes from \"" + os.path.basename(self.filepath) + "\"...")

        tree = etree.parse(self.filepath)
        hashlist_element = tree.getroot()

        self.media_hash_list = MediaHashList(None)
        self.media_hash_list.generation_number = self.generation_number

        for section in hashlist_element.getchildren():
            if section.tag == 'hashes':
                self.media_hash_list.root_path = section.get('rootPath')
                self.media_hash_list.relative_filepath = os.path.relpath(self.filepath,
                                                                         start=os.path.dirname(
                                                                             os.path.dirname(self.filepath)))

                hashes = section.getchildren()
                for hash_element in hashes:
                    relative_filepath = hash_element.xpath('filename')[0].text

                    media_hash = MediaHash(relative_filepath)
                    for hashformat in HashListCreator.supported_hashformats:
                        hashelement = hash_element.xpath(hashformat)
                        if hashelement:
                            hash_string = hash_element.xpath(hashformat)[0].text

                            hash_entry = HashEntry(hash_string, hashformat)
                            media_hash.append_hash_entry(hash_entry)
                    self.media_hash_list.media_hashes.append(media_hash)

        ctx = click.get_current_context().obj
        if ctx.verbose:
            for media_hash in self.media_hash_list.media_hashes:
                for hash_entry in media_hash.hash_entries:
                    media_hash.log_hash_entry(hash_entry.hash_format)


class HashListCreator:
    """class used to create an MHL XML file

    Main task is to traverse a folder structure and during the traversal write a MHL XML file for a new generation
    with the traverse and traverse_with_existing_hashes methods.

    member variables:
    rootPath -- folder where traversal should start
    verbose -- bool value, enables/disables logging
    simulate -- bool value, if true doesn't write the MHL file
    info -- user info (name, email, ..) for MHL header
    filenameIgnorePrefixes -- ignore all files that start with these prefixes
    create_directory_hashes -- bool value, if true also computes compound hashes for directories
    write_xattr -- bool value, also lets create_filehash write the created hash to the filesystem
    """

    supported_hashformats = {'xxhash', 'MD5', 'SHA1', 'C4'}  # is also decreasing priority list for verification

    def __init__(self, root_path, info):
        """initialize the HashListCreator, set default values

        arguments:
        root_path -- folder where traversal should start
        info -- user info (name, email, ..) for MHL header
        """
        if not os.path.exists(root_path) or not os.path.isdir(root_path):
            print("ERR: HashListCreator init: foler \"" + root_path + "\" does not exist.")
            return
        if not root_path.endswith(os.path.sep):
            root_path = root_path + os.path.sep

        self.rootPath = root_path
        ctx = click.get_current_context().obj
        self.verbose = ctx.verbose  # TODO: we should not be setting verbose a million places...
        self.simulate = False
        self.info = info
        self.filenameIgnorePrefixes = ['Icon', '.DS_Store']
        self.foldernameIgnores = ['asc-mhl']
        self._h = lxml.sax.ElementTreeContentHandler()
        self.create_directory_hashes = False
        self.write_xattr = False

    def element_hash(self, media_hash):
        """builds and returns one <hash> element for a given MediaHash object"""

        hash_element = etree.Element('hash')

        filename_element = etree.SubElement(hash_element, 'filename')
        filename_element.text = media_hash.relative_filepath
        filesize_element = etree.SubElement(hash_element, 'filesize')
        filesize_element.text = media_hash.filesize.__str__()
        lastmodificationdate_element = etree.SubElement(hash_element, 'lastmodificationdate')
        lastmodificationdate_element.text = datetime_isostring(media_hash.last_modification_date)

        for hash_entry in media_hash.hash_entries:
            hashformat_element_attributes = {}
            if hash_entry.action is not None:
                if hash_entry.action != 'copy-only':
                    hashformat_element_attributes['action'] = hash_entry.action
            if hash_entry.secondary is not None and hash_entry.secondary is not False:
                hashformat_element_attributes['secondary'] = "true" if hash_entry.secondary else None
            hashformat_element = etree.SubElement(hash_element, hash_entry.hash_format,
                                                  attrib=hashformat_element_attributes)
            hashformat_element.text = hash_entry.hash_string

        objectify.deannotate(hash_element, cleanup_namespaces=True, xsi_nil=True)
        return hash_element

    # TODO: swap this out to use the data from context rather than info dictionary
    def element_creator_info(self, creator_data):
        """builds and returns one <creatorinfo> element for a given dictionary of information"""

        creator_info = objectify.Element('creatorinfo')
        if self.info['name'] is not None:
            creator_info.name = self.info['name']
        if self.info['username'] is not None:
            creator_info.username = self.info['username']
        creator_info.hostname = platform.node()
        creator_info.toolname = ascmhl_toolname_string
        creator_info.toolversion = ascmhl_toolversion_string
        creator_info.creationdate = datetime_now_isostring()
        creator_info.process = 'verify'
        if self.info['comment'] is not None:
            creator_info.comment = creator_data['comment']
        objectify.deannotate(creator_info, cleanup_namespaces=True, xsi_nil=True)
        return creator_info

    def element_genreference(self, media_hash_list):
        """builds and returns one <genreference> element referencing a given MHL file"""

        genreference_element = etree.Element('genreference')
        path_element = etree.SubElement(genreference_element, 'path')
        path_element.text = media_hash_list.relative_filepath
        hash_element = etree.SubElement(genreference_element, 'xxhash')
        hash_element.text = xxhash64(os.path.join(self.rootPath, media_hash_list.relative_filepath))

        # for hashformat in media_hash_list.hashformats:
        #    hash_element = etree.SubElement(genreference_element, hashformat['hashformat'])
        #    hash_element.text = hashformat['hash_string']
        return genreference_element

    def element_ascmhlreference(self, ascmhl_relative_path):
        """builds and returns one <ascmhlreference> element referencing a relative path"""

        ascmhlreference_element = etree.Element('ascmhlreference')
        path_element = etree.SubElement(ascmhlreference_element, 'path')
        path_element.text = ascmhl_relative_path
        hash_element = etree.SubElement(ascmhlreference_element, 'xxhash')
        hash_element.text = xxhash64(os.path.join(self.rootPath, ascmhl_relative_path))
        return ascmhlreference_element

    def traverse(self, hashformat_for_new):
        """traverse and build an MHL file without comparing to exiting hashes (e.g. generation 0001)

        arguments:
        hashformat_for_new -- format for new hashes
        """
        self.traverse_with_existing_hashes(None, hashformat_for_new)

    def traverse_with_existing_hashes(self, media_hash_list, hashformat_for_new):
        """traverse and build an MHL file and compare to exiting hashes

        arguments:
        media_hash_list -- MediaHashList object withe existing hashes from previous MHL file
        hashformat_for_new -- format for new hashes
        """
        logger.verbose('initializing new ASC-MHL file...')

        self._h.startDocument()
        self._h.startElementNS((None, 'hashlist'), 'hashlist', {(None, 'version'): "2.0"})
        hashlist_element = self._h._element_stack[-1]

        creatorinfo_element = self.element_creator_info({'comment': self.info['comment']})
        hashlist_element.append(creatorinfo_element)

        if media_hash_list is not None:
            genreference_element = self.element_genreference(media_hash_list)
            hashlist_element.append(genreference_element)

        logger.verbose(f'scanning {self.rootPath} ...')

        self._h.startElementNS((None, 'hashes'), 'hashes', {(None, 'rootPath'): self.rootPath})
        hashes_element = self._h._element_stack[-1]

        all_directories_media_list = MediaHashList(self.rootPath)
        number_of_failed_verifications = 0

        for root, directories, filenames in os.walk(self.rootPath, topdown=False):
            # if os.path.basename(os.path.normpath(root)) in self.foldernameIgnores is not None:
            #   continue
            # print("DBG: traversing folder \"{0}\"...".format(root))

            # recurse?
            if root is not self.rootPath:
                folder_manager = HashListFolderManager(root)
                folder_manager.verbose = self.verbose

                if folder_manager.ascmhl_folder_exists():
                    result = self.recurse(root, hashformat_for_new, self.info)
                    if not self.simulate:
                        element_ascmhlreference = self.element_ascmhlreference(
                            os.path.relpath(result['new_ascmhl_filepath'], self.rootPath))
                        hashlist_element.append(element_ascmhlreference)
                    number_of_failed_verifications = number_of_failed_verifications + result['number_failures']
                    continue
                elif folder_manager.ascmhl_folder_exists_above_up_to_but_excluding(self.rootPath):
                    continue

            # verify files
            file_media_list = MediaHashList(root)
            for filename in sorted(filenames):
                filepath = os.path.join(root, filename)
                if matches_prefixes(filename, self.filenameIgnorePrefixes) is False:
                    previous_media_hash = None

                    relative_filepath = os.path.relpath(filepath, start=self.rootPath)
                    current_media_hash = MediaHash(relative_filepath)
                    current_media_hash.filesize = os.path.getsize(filepath)
                    current_media_hash.last_modification_date = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))

                    if media_hash_list is not None:
                        previous_media_hash = media_hash_list.media_hash_for_relative_filepath(relative_filepath)

                    if previous_media_hash is not None:
                        for hashformat in HashListCreator.supported_hashformats:
                            previous_hash_entry = previous_media_hash.hash_entry_for_format(hashformat)
                            if previous_hash_entry is not None:
                                if not current_media_hash.has_verified_or_failed_hash_entry():
                                    hash_string = create_filehash(filepath, hashformat, self.write_xattr)
                                    hash_entry = HashEntry(hash_string, hashformat)
                                    if previous_hash_entry.matches_hash_entry(hash_entry):
                                        hash_entry.action = 'verified'
                                    else:
                                        hash_entry.action = 'failed'
                                        if self.verbose:
                                            print("\nERROR: hash mismatch for \"{0}\"! old {1}: {2}, new {3}: {4}\n"
                                                  .format(relative_filepath,
                                                          hashformat, previous_hash_entry.hash_string,
                                                          hashformat, hash_string))
                                        number_of_failed_verifications = number_of_failed_verifications + 1
                                else:
                                    hash_entry = previous_hash_entry
                                    hash_entry.action = 'copy-only'

                                current_media_hash.append_hash_entry(hash_entry)

                    if not current_media_hash.has_verified_or_failed_hash_entry() or \
                            current_media_hash.hash_entry_for_format(hashformat_for_new) is None:
                        hash_string = create_filehash(filepath, hashformat_for_new, self.write_xattr)
                        hash_entry = HashEntry(hash_string, hashformat_for_new)

                        if media_hash_list is None:
                            hash_entry.action = 'original'
                        else:
                            hash_entry.action = 'new'

                        current_media_hash.append_hash_entry(hash_entry)

                    for hash_entry in current_media_hash.hash_entries:
                        if hash_entry.action == 'verified' or hash_entry.action == 'failed' or \
                                hash_entry.action == 'new' or hash_entry.action == 'original':
                            current_media_hash.log_hash_entry(hash_entry.hash_format)

                    file_media_list.append_media_hash(current_media_hash)

                    # extend XML
                    hash_element = self.element_hash(current_media_hash)
                    hashes_element.append(hash_element)

            if self.create_directory_hashes:
                # collect previous hashes of directories
                relative_directories = list()
                for directory in directories:
                    relative_directories.append(os.path.relpath(os.path.join(root, directory), start=self.rootPath))
                directory_media_list = all_directories_media_list.media_hash_list_for_relative_filepaths(relative_directories)

                # create directory hash with all items from current directory
                # FIXME: directory hash is hard-coded to xxhash
                directory_hash_format = 'xxhash'
                relative_directory_path = os.path.relpath(root, start=self.rootPath)
                current_directory_media_hash = self.media_hash_for_directory_with_contents(relative_directory_path, file_media_list,
                                                                                           directory_media_list, directory_hash_format)
                all_directories_media_list.append_media_hash(current_directory_media_hash)

                current_directory_media_hash.log_hash_entry(directory_hash_format)

                if self.write_xattr:
                    try:
                        xattr.setxattr(root, "com.theasc.asc-mhl.xxhash",
                                       current_directory_media_hash.hash_entry_for_format(directory_hash_format).hash_string.encode('utf8'))
                    except IOError:
                        print("ERR: couldn't set xattr for \"{0}\", errno {1}".format(root, IOError))

        self._h.endElementNS((None, 'hashes'), 'hashes')

        self._h.endElementNS((None, 'hashlist'), 'hashlist')
        self._h.endDocument()

        return number_of_failed_verifications

    def recurse(self, folderpath, hashformat, info):
        """sets up recursive traversal of an embedded folder that has an ascmhl folder itself
        and calls traverse_with_existing_hashes on a new HashListCreator

        arguments:

        folderpath -- path of embedded folder with own ascmhl folder
        hashformat -- format for new hashes
        info -- user info (name, email, ..) for MHL header
        """

        folder_manager = HashListFolderManager(folderpath)
        folder_manager.verbose = self.verbose

        ascmhl_generationnumber = folder_manager.earliest_ascmhl_generation_number()
        ascmhl_path = folder_manager.path_for_ascmhl_generation_number(ascmhl_generationnumber)

        print("Traversing\"" + folderpath + "\"...")

        reader = HashListReader(ascmhl_path, ascmhl_generationnumber)
        reader.verbose = self.verbose
        reader.parse()

        creator = HashListCreator(folderpath, info)
        creator.verbose = self.verbose
        creator.create_directory_hashes = self.create_directory_hashes
        creator.write_xattr = self.write_xattr

        number_failures = creator.traverse_with_existing_hashes(reader.media_hash_list, hashformat)

        new_ascmhl_filepath = None
        if not self.simulate:
            new_ascmhl_filepath = folder_manager.write_ascmhl(creator.xml_string())

        return {'number_failures': number_failures,
                'new_ascmhl_filepath': new_ascmhl_filepath}

    # create folder hash
    # input:
    # - file_media_list (MediaList)
    # - directory_media_list (MediaList)
    # return:
    # - MediaHash
    def media_hash_for_directory_with_contents(self, directory_path, file_media_list, directory_media_list, hash_format):
        """creates a compound hash (as a MediaHash object) for a directory , based on the directories contents

        arguments:
        file_media_list -- MediaList for all files in directory
        directory_media_list -- MediaList for all directory hashes for all directories in directory
        """

        directory_content_items_hash_list = file_media_list
        directory_content_items_hash_list.append_media_hash_list(directory_media_list)

        relative_filepaths_for_sorting = list()
        for media_hash in directory_content_items_hash_list.media_hashes:
            relative_filepaths_for_sorting.append(media_hash.relative_filepath)

        collected_hash_data = bytes(0)

        for relative_filepath in sorted(relative_filepaths_for_sorting):  # FIXME: define sort criteria
            media_hash = directory_content_items_hash_list.media_hash_for_relative_filepath(relative_filepath)
            hash_entry = media_hash.hash_entry_for_format(hash_format)
            if hash_entry is None:
                print("ERROR: cannot create directory hash of format {0}, no such hash format available for \"{1}\"".
                      format(hash_format, media_hash.relative_filepath))
                exit(103)

            hash_data = binascii.unhexlify(hash_entry.hash_string)
            collected_hash_data = collected_hash_data + hash_data

        directory_hash_string = create_datahash(collected_hash_data, hash_format)

        directory_hash = MediaHash(directory_path)
        directory_hash_entry = HashEntry(directory_hash_string, hash_format)
        directory_hash_entry.action = 'directory'
        directory_hash.append_hash_entry(directory_hash_entry)

        return directory_hash

    def xml_string(self):
        """finalizes the XML string"""

        tree = self._h.etree
        xml_string: bytes = lxml.etree.tostring(tree.getroot(), pretty_print=True, xml_declaration=True,
                                                encoding="utf-8")
        return xml_string.decode()
