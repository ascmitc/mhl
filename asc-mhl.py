#!/usr/bin/env python3

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


ascmhl_toolname_string = 'ascmhl-verify'
ascmhl_toolversion_string = '0.0.3'


def create_filehash(filepath, hashformat, write_xattr):
    hash_string = None
    if hashformat == 'MD5':
        hash_string = md5(filepath)
    elif hashformat == 'SHA1':
        hash_string = sha1(filepath)
    elif hashformat == 'xxhash':
        hash_string = xxhash(filepath)
    elif hashformat == 'C4':
        hash_string = c4(filepath)
    else:
        print("ERROR: unspported hash format \"{0}\"".format(hashformat))

    if write_xattr:
        if hash_string is not None:
            try:
                xattr.setxattr(filepath, "com.theasc.asc-mhl." + hashformat, hash_string.encode('utf8'))
            except IOError:
                print("ERR: couldn't set xattr for \"{0}\", errno {1}".format(filepath, IOError))

    return hash_string


def create_datahash(data, hashformat):
    file = tempfile.NamedTemporaryFile(delete=False)
    file.write(data)
    file.close()

    filehash = create_filehash(file.name, hashformat, False)
    return filehash


def md5(filepath):
    result_string = subprocess.check_output(['md5', filepath], encoding="utf-8")
    parts = result_string.split('= ')
    hash_string: str = parts[1]
    return hash_string.rstrip()


def sha1(filepath):
    result_string = subprocess.check_output(['openssl', "sha1", filepath], encoding="utf-8")
    parts = result_string.split('= ')
    hash_string: str = parts[1]
    return hash_string.rstrip()


def xxhash(filepath):
    result_string = subprocess.check_output(['xxhsum', filepath], encoding="utf-8")
    parts = result_string.split('  ')
    hash_string: str = parts[0]
    return hash_string.rstrip()


def c4(filepath):
    result_string = subprocess.check_output(['openssl', "sha512", filepath], encoding="utf-8")
    parts = result_string.split('= ')
    sha512_string: str = parts[1]

    # go, Javascript
    charset = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    # wikipedia, whitepaper
    # charset = "123456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"

    base58 = 58         # the encoding basis
    c4id_length = 90    # the guaranteed length
    zero = '1'          # '0' is not in the C4ID alphabet so '1' is zero

    hash_value = int(sha512_string, 16)
    c4_string = ""
    while hash_value is not 0:
        modulo = hash_value % base58
        hash_value = hash_value // base58
        c4_string = charset[modulo] + c4_string

    c4_string = "c4" + c4_string.ljust(c4id_length - 2, zero)
    return c4_string


def datetime_isostring(date, keep_microseconds=False):
    utc_offset_sec = time.altzone if time.localtime().tm_isdst else time.timezone
    utc_offset = datetime.timedelta(seconds=-utc_offset_sec)

    if keep_microseconds:
        date_to_format = date
    else:
        date_to_format = date.replace(microsecond=0)

    return date_to_format.replace(tzinfo=datetime.timezone(offset=utc_offset)).isoformat()


def datetime_now_isostring():
    return datetime_isostring(datetime.datetime.now())


def datetime_now_filename_string():
    return datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d_%H%M%S')


def datetime_now_isostring_with_microseconds():
    return datetime_isostring(datetime.datetime.now(), keep_microseconds=True)


def matches_prefixes(text: str, prefixes: list):
    for prefix in prefixes:
        if text.startswith(prefix):
            return True
    return False


class MediaHashList:
    def __init__(self, root_path):
        self.root_path = root_path
        self.media_hashes = list()
        self.generation_number = 0

    def append_media_hash(self, media_hash):
        self.media_hashes.append(media_hash)

    def append_media_hash_list(self, other_media_hash_list):
        self.media_hashes = self.media_hashes + other_media_hash_list.media_hashes

    # input: strings(relative path)
    def media_hash_for_relative_filepath(self, filepath):
        for media_hash in self.media_hashes:
            if media_hash.relative_filepath == filepath:
                return media_hash
        return None

    # input: array of strings (relative paths)
    def media_hash_list_for_relative_filepaths(self, filepaths):
        directory_media_list = MediaHashList(self.root_path)
        for filepath in sorted(filepaths):
            directory_media_hash = self.media_hash_for_relative_filepath(filepath)
            if directory_media_hash is not None:
                directory_media_list.append_media_hash(directory_media_hash)
            else:
                print("WARNING: couldn't find MediaHash for \"{0}\"".format(filepath))
        return directory_media_list


class MediaHash:
    def __init__(self, relative_filepath):
        self.relative_filepath = relative_filepath
        self.filesize = 0
        self.last_modification_date = None
        self.hash_entries = list()

    def append_hash_entry(self, hash_entry):
        if hash_entry.action == 'new' and not len(self.hash_entries) == 0:
            hash_entry.secondary = True
        self.hash_entries.append(hash_entry)

    def hash_entry_for_format(self, hash_format):
        for hash_entry in self.hash_entries:
            if hash_entry.hash_format == hash_format:
                return hash_entry
        return None

    def has_hash_entry_of_action(self, action):
        for hash_entry in self.hash_entries:
            if hash_entry.action == action:
                return True
        return False

    def has_verified_or_failed_hash_entry(self):
        if self.has_hash_entry_of_action('verified'):
            return True
        elif self.has_hash_entry_of_action('failed'):
            return True
        else:
            return False

    def log_hash_entry(self, hash_format):
        for hash_entry in self.hash_entries:
            if hash_entry.hash_format == hash_format:
                indicator = " "
                if hash_entry.action == 'failed':
                    indicator = "!"
                elif hash_entry.action == 'directory':
                    indicator = "d"

                print("{0} {1}: {2} {3}: {4}".format(indicator,
                                                     hash_entry.hash_format.rjust(6),
                                                     hash_entry.hash_string.ljust(32),
                                                     (hash_entry.action if hash_entry.action is not None else "").ljust(10),
                                                     self.relative_filepath))


class HashEntry:
    def __init__(self, hash_string, hash_format):
        self.hash_string = hash_string
        self.hash_format = hash_format
        self.hash_date = datetime_now_isostring_with_microseconds()
        self.action = None
        self.secondary = False

    def matches_hash_entry(self, other_hash_entry):
        if self.hash_format != other_hash_entry.hash_format:
            return False
        if self.hash_string != other_hash_entry.hash_string:
            return False
        return True


class HashListCreator:
    supported_hashformats = {'xxhash', 'MD5', 'SHA1', 'C4'}           # is also decreasing priority list for verification

    def __init__(self, root_path, info):
        if not os.path.exists(root_path) or not os.path.isdir(root_path):
            print("ERR: HashListCreator init: foler \"" + root_path + "\" does not exist.")
            return
        if not root_path.endswith(os.path.sep):
            root_path = root_path + os.path.sep

        self.rootPath = root_path
        self.verbose = False
        self.simulate = False
        self.info = info
        self.filenameIgnorePrefixes = ['Icon', '.DS_Store']
        self.foldernameIgnores = ['asc-mhl']
        self._h = lxml.sax.ElementTreeContentHandler()
        self.create_directory_hashes = False
        self.write_xattr = False

    def element_hash(self, media_hash):
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

    def element_creator_info(self, creator_data):
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
        genreference_element = etree.Element('genreference')
        path_element = etree.SubElement(genreference_element, 'path')
        path_element.text = media_hash_list.relative_filepath
        hash_element = etree.SubElement(genreference_element, 'xxhash')
        hash_element.text = xxhash(os.path.join(self.rootPath, media_hash_list.relative_filepath))

        # for hashformat in media_hash_list.hashformats:
        #    hash_element = etree.SubElement(genreference_element, hashformat['hashformat'])
        #    hash_element.text = hashformat['hash_string']
        return genreference_element

    def element_ascmhlreference(self, ascmhl_relative_path):
        ascmhlreference_element = etree.Element('ascmhlreference')
        path_element = etree.SubElement(ascmhlreference_element, 'path')
        path_element.text = ascmhl_relative_path
        hash_element = etree.SubElement(ascmhlreference_element, 'xxhash')
        hash_element.text = xxhash(os.path.join(self.rootPath, ascmhl_relative_path))
        return ascmhlreference_element

    def traverse(self, hashformat_for_new):
        self.traverse_with_existing_hashes(None, hashformat_for_new)

    def traverse_with_existing_hashes(self, media_hash_list, hashformat_for_new):
        if self.verbose:
            print("initializing new ASC-MHL file...")
        self._h.startDocument()
        self._h.startElementNS((None, 'hashlist'), 'hashlist', {(None, 'version'): "2.0"})
        hashlist_element = self._h._element_stack[-1]

        creatorinfo_element = self.element_creator_info({'comment': self.info['comment']})
        hashlist_element.append(creatorinfo_element)

        if media_hash_list is not None:
            genreference_element = self.element_genreference(media_hash_list)
            hashlist_element.append(genreference_element)

        if self.verbose:
            print("Scanning \"" + self.rootPath + "\"...")

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
                current_directory_media_hash = self.media_hash_for_directory_with_contents(relative_directory_path, file_media_list, directory_media_list, directory_hash_format)
                all_directories_media_list.append_media_hash(current_directory_media_hash)

                current_directory_media_hash.log_hash_entry(directory_hash_format)

                if self.write_xattr:
                    try:
                        xattr.setxattr(root, "com.theasc.asc-mhl.xxhash", current_directory_media_hash.hash_entry_for_format(directory_hash_format).hash_string.encode('utf8'))
                    except IOError:
                        print("ERR: couldn't set xattr for \"{0}\", errno {1}".format(root, IOError))

        self._h.endElementNS((None, 'hashes'), 'hashes')

        self._h.endElementNS((None, 'hashlist'), 'hashlist')
        self._h.endDocument()

        return number_of_failed_verifications

    def recurse(self, folderpath, hashformat, info):

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

        directory_content_items_hash_list = file_media_list
        directory_content_items_hash_list.append_media_hash_list(directory_media_list)

        relative_filepaths_for_sorting = list()
        for media_hash in directory_content_items_hash_list.media_hashes:
            relative_filepaths_for_sorting.append(media_hash.relative_filepath)

        collected_hash_data = bytes(0)

        for relative_filepath in sorted(relative_filepaths_for_sorting):        # FIXME: define sort criteria
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
        tree = self._h.etree
        xml_string: bytes = lxml.etree.tostring(tree.getroot(), pretty_print=True, xml_declaration=True,
                                                encoding="utf-8")
        return xml_string.decode()


class HashListFolderManager:
    ascmhl_folder_name = "asc-mhl"
    ascmhl_file_extension = ".ascmhl"

    def __init__(self, folderpath):
        self.verbose = False
        if not os.path.exists(folderpath) or not os.path.isdir(folderpath):
            print("ERR: HashListFolderManager init: foler \"" + folderpath + "\" does not exist.")
            folderpath = None
        elif not folderpath[len(folderpath):1] == os.path.sep:
            folderpath = folderpath + os.path.sep
        self.folderpath = folderpath

    def ascmhl_folder_path(self):
        path = os.path.join(self.folderpath, HashListFolderManager.ascmhl_folder_name)
        return path

    def ascmhl_folder_exists(self):
        return os.path.exists(self.ascmhl_folder_path())

    def ascmhl_folder_exists_above_up_to_but_excluding(self, rootpath):
        if os.path.relpath(self.folderpath, rootpath) is None:
            return False
        #path = os.path.dirname(os.path.normpath(self.folderpath))
        path = os.path.normpath(self.folderpath)
        rootpath = os.path.normpath(rootpath)
        while path != rootpath:
            ascmhl_path = os.path.join(path, self.ascmhl_folder_name)
            if os.path.exists(ascmhl_path):
                return True
            path = os.path.dirname(path)
        return False

    def queried_ascmhl_filename(self, generation_number):
        ascmhl = self._ascmhl_files(generation_number)
        if 'queried_filename' in ascmhl:
            return ascmhl['queried_filename']
        else:
            return None

    def earliest_ascmhl_generation_number(self) -> int:
        ascmhl = self._ascmhl_files()
        return ascmhl['earliest_generation_number']

    def earliest_ascmhl_filename(self):
        ascmhl = self._ascmhl_files()
        return ascmhl['earliest_filename']

    def latest_ascmhl_generation_number(self) -> int:
        ascmhl = self._ascmhl_files()
        return ascmhl['latest_generation_number']

    def latest_ascmhl_filename(self):
        ascmhl = self._ascmhl_files()
        return ascmhl['latest_filename']

    def _ascmhl_files(self, query_generation_number=None):
        ascmhl_folder_path = self.ascmhl_folder_path()
        if ascmhl_folder_path is None:
            return None
        else:
            queried_filename = None
            queried_generation_number = 0
            earliest_filename = None
            lowest_generation_number = 1000000
            latest_filename = None
            highest_generation_number = 0
            for root, directories, filenames in os.walk(ascmhl_folder_path):
                for filename in filenames:
                    if filename.endswith(HashListFolderManager.ascmhl_file_extension):
                        # A002R2EC_2019-06-21_082301_0005.ascmhl
                        parts = re.findall(r'(.*)_(.+)_(.+)_(\d+)\.ascmhl', filename)
                        if parts.__len__() == 1 and parts[0].__len__() == 4:
                            generation_number = int(parts[0][3])
                            if query_generation_number == generation_number:
                                queried_generation_number = generation_number
                                queried_filename = filename
                            if lowest_generation_number > generation_number:
                                lowest_generation_number = generation_number
                                earliest_filename = filename
                            if highest_generation_number < generation_number:
                                highest_generation_number = generation_number
                                latest_filename = filename
                        else:
                            print("ERROR: name of ascmhl file \"{0}\" doesn't conform to naming convention.",
                                  filename)
            result_tuple = {'earliest_filename': earliest_filename,
                            'earliest_generation_number': lowest_generation_number,
                            'latest_filename': latest_filename,
                            'latest_generation_number': highest_generation_number}

            if queried_filename is not None:
                result_tuple['queried_filename'] = queried_filename
                result_tuple['queried_generation_number'] = queried_generation_number

            return result_tuple

    def path_for_ascmhl_file(self, filename):
        if filename is None:
            return None
        else:
            path = os.path.join(self.folderpath, HashListFolderManager.ascmhl_folder_name, filename)
            return path

    def path_for_ascmhl_generation_number(self, generation_number):
        if generation_number is None:
            return None
        else:
            filename = self.queried_ascmhl_filename(generation_number)
            if filename is None:
                return None
            path = os.path.join(self.folderpath, HashListFolderManager.ascmhl_folder_name, filename)
            return path

    def new_ascmhl_filename(self):
        date_string = datetime_now_filename_string()
        index = self.latest_ascmhl_generation_number() + 1
        return os.path.basename(os.path.normpath(self.folderpath)) + "_" + date_string + "_" + str(index).zfill(
            4) + ".ascmhl"

    def path_for_new_ascmhl_file(self):
        filename = self.new_ascmhl_filename()
        if filename is not None:
            return self.path_for_ascmhl_file(filename)

    def write_ascmhl(self, xml_string):
        filepath = self.path_for_new_ascmhl_file()
        if filepath is not None:
            # if self.verbose:
            print("Writing \"" + filepath + "\"")
            with open(filepath, 'wb') as file:
                # FIXME: check if file could be created
                file.write(xml_string.encode('utf8'))
            return filepath

    def file_is_in_ascmhl_folder(self, filepath):
        ascmhl_folder_path = self.ascmhl_folder_path()
        if ascmhl_folder_path is None:
            return False
        else:
            return filepath.startswith(self.ascmhl_folder_path())


class HashListReader:
    def __init__(self, filepath, generation_number):
        # print("DBG: filename " + filename )
        self.filepath = filepath
        self.verbose = False
        self.media_hash_list = None
        self.generation_number = generation_number

    def parse(self):
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

        if self.verbose:
            for media_hash in self.media_hash_list.media_hashes:
                for hash_entry in media_hash.hash_entries:
                    media_hash.log_hash_entry(hash_entry.hash_format)


@click.group()
def cli():
    pass


@click.command()
@click.argument('folderpath', type=click.Path(exists=True, file_okay=False))
@click.option('--name', '-n', help="Full name of user")
@click.option('--username', '-u', help="Login name of user")
@click.option('--comment', '-c', help="Comment string for human readable context")
@click.option('--hashformat', '-h', type=click.Choice(['xxhash', 'MD5', 'SHA1', 'C4']), multiple=False, default='xxhash')
@click.option('--generationnumber', '-g', help="Generation number to verify against")
@click.option('--simulate', '-s', default=False, is_flag=True, help="Simulate only, don't write new ascmhl file")
@click.option('--directoryhashes', '-d', default=False, is_flag=True, help="Log calculated directory hashes")
@click.option('--write-xattr', '-wx', default=False, is_flag=True, help="Write hashes as xattr to file system")
@click.option('--verbose', '-v', default=False, is_flag=True, help="Verbose output")
def verify(folderpath, name, username, comment, write_xattr, generationnumber, verbose, simulate,
           directoryhashes, hashformat):
    """Verify a folder and create a new ASC-MHL file"""
    info = {'username': username,
            'name': name,
            'comment': comment}

    # find existing ASC-MHL files
    folder_manager = HashListFolderManager(folderpath)
    folder_manager.verbose = verbose

    if generationnumber is not None:
        ascmhl_generationnumber = int(generationnumber)
    else:
        ascmhl_generationnumber = folder_manager.earliest_ascmhl_generation_number()

    ascmhl_path = folder_manager.path_for_ascmhl_generation_number(ascmhl_generationnumber)

    if generationnumber is not None and ascmhl_path is None:
        print("ERROR: couldn't find ascmhl file with generation number {0}".format(generationnumber))
    else:
        creator = HashListCreator(folderpath, info)
        creator.verbose = verbose
        creator.create_directory_hashes = directoryhashes
        creator.write_xattr = write_xattr
        creator.simulate = simulate

        print("Traversing\"" + folderpath + "\"...")

        if ascmhl_path is not None:
            reader = HashListReader(ascmhl_path, ascmhl_generationnumber)
            reader.verbose = verbose
            reader.parse()

            number_failures = creator.traverse_with_existing_hashes(reader.media_hash_list, hashformat)
            if number_failures > 0:
                print("ERROR: verification failed for {0} file(s)".format(number_failures))
            if not simulate:
                folder_manager.write_ascmhl(creator.xml_string())
        else:
            creator.traverse(hashformat)

            if not simulate:
                if not os.path.exists(folder_manager.ascmhl_folder_path()):
                    os.makedirs(folder_manager.ascmhl_folder_path())
                folder_manager.write_ascmhl(creator.xml_string())


@click.command()
@click.argument('filename', type=click.Path(exists=True))
def read(filename):
    """Read an ASC-MHL file"""
    reader = HashListReader(filename, 0)
    reader.parse()


@click.command()
@click.argument('folderpath', type=click.Path(exists=True, file_okay=True))
def test(folderpath):
    c4_string = c4(folderpath)
    print("TEST: c4_string : {0}: {1}".format(c4_string, folderpath))


cli.add_command(verify)
cli.add_command(read)
cli.add_command(test)


if __name__ == "__main__":
    cli()
    exit(0)
