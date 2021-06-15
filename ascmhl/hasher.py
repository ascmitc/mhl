"""
__author__ = "Alexander Sahm, Patrick Renner"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner"
__email__ = "opensource@pomfort.com"
"""
import binascii
import hashlib
import xxhash
import math
import os


def generate_checksum(csum_type, file_path):
    """
    generate a checksum for the hashlib checksum type.
    :param csum_type: the hashlib compliant checksum type
    :param file_path: the absolute path to the resource being hashed
    :return: hexdigest of the checksum
    """
    csum = csum_type()

    if file_path is None:
        print("ERROR: file_path is None")
        return None

    with open(file_path, "rb") as fd:
        # process files in 1MB chunks so that large files won't cause excessive memory consumption.
        chunk = fd.read(1024 * 1024)
        while chunk:
            csum.update(chunk)
            chunk = fd.read(1024 * 1024)
    return csum.hexdigest()


def create_filehash(hash_format, filepath):
    """creates a hash value for a file and returns the hex string

    arguments:
    filepath -- string value, the path to the file
    hashformat -- string value, one of the supported hash formats, e.g. 'md5', 'xxh64'
    """
    csum_type = context_type_for_hash_format(hash_format)
    if csum_type:
        return generate_checksum(csum_type, filepath)

    return None


def context_type_for_hash_format(hash_format):
    if hash_format == "md5":
        return hashlib.md5
    elif hash_format == "sha1":
        return hashlib.sha1
    elif hash_format == "xxh32":
        return xxhash.xxh32
    elif hash_format == "xxh64":
        return xxhash.xxh64
    elif hash_format == "xxh3":
        return xxhash.xxh3_64
    elif hash_format == "xxh128":
        return xxhash.xxh3_128
    elif hash_format == "c4":
        return C4HashContext
    assert False, "unsupported hash format"


class C4HashContext:
    def __init__(self):
        self.internal_context = hashlib.sha512()
        self.charset = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

    def update(self, input_data):
        self.internal_context.update(input_data)

    def hexdigest(self):
        sha512_string = self.internal_context.hexdigest()

        base58 = 58  # the encoding basis
        c4id_length = 90  # the guaranteed length
        zero = "1"  # '0' is not in the C4ID alphabet so '1' is zero

        hash_value = int(sha512_string, 16)
        c4_string = ""
        while hash_value != 0:
            modulo = hash_value % base58
            hash_value = hash_value // base58
            c4_string = self.charset[modulo] + c4_string

        c4_string = "c4" + c4_string.rjust(c4id_length - 2, zero)
        return c4_string

    def data_for_C4ID_string(self, c4id_string):
        base58 = 58  # the encoding basis
        c4id_length = 90  # the guaranteed length
        result = 0
        i = 2

        while i < c4id_length:
            temp = self.charset.index(c4id_string[i])
            result = result * base58 + temp
            i = i + 1

        data = result.to_bytes(64, byteorder="big")
        return data


class DirectoryHashContext:
    def __init__(self, hash_format: str):
        self.hash_format = hash_format
        self.content_hash_strings = []
        self.structure_hash_strings = []
        self.directory_paths = []
        self.file_paths = []

    def append_file_hash(self, path: str, content_hash_string: str):
        self.content_hash_strings.append(content_hash_string)
        self.file_paths.append(path)

    def append_directory_hashes(self, path: str, content_hash_string: str, structure_hash_string: str):
        self.content_hash_strings.append(content_hash_string)
        self.structure_hash_strings.append(structure_hash_string)
        self.directory_paths.append(path)

    def final_content_hash_str(self):
        # simply create a list-digest of all content digests
        element_list = self.content_hash_strings
        element_list = list(set(element_list))  # deduplicate, is not happening in digest_for_digest_list any more
        content_hash = digest_for_digest_list(element_list, self.hash_format)
        return content_hash

    def final_structure_hash_str(self):
        # we need to mix file names and recursive directory structure here...
        # .. so start with the file names themselves and hash those individually ..
        file_names = []
        for path in self.file_paths:
            file_names.append(os.path.basename(os.path.normpath(path)))
        element_list = digest_list_for_list(file_names, self.hash_format)
        # .. and then add digests of concatenated directory names and structure digest
        assert len(self.directory_paths) == len(self.structure_hash_strings)
        for i in range(len(self.directory_paths)):
            directory_name = os.path.basename(os.path.normpath(self.directory_paths[i]))
            element_data = directory_name.encode("utf8") + digest_data_for_digest_string(
                self.structure_hash_strings[i], self.hash_format
            )
            element_list.append(digest_for_data(element_data, self.hash_format))
        # at the end make a list-digest of all the collected and created digests
        structure_hash = digest_for_digest_list(element_list, self.hash_format)
        return structure_hash


def digest_for_list(input_list, hash_format: str):
    if len(input_list) == 0:
        return digest_for_string("", hash_format)
    # from pseudo code in 30MR-WD-ST-2114-C4ID-2017-01-17 V0 (1).pdf
    input_list = sorted_deduplicates(input_list)
    digest_list_names = digest_list_for_list(input_list, hash_format)
    return digest_for_digest_list(digest_list_names, hash_format)


def digest_for_digest_list(digest_list, hash_format: str):
    if len(digest_list) == 0:
        return digest_for_string("", hash_format)
    # from pseudo code in 30MR-WD-ST-2114-C4ID-2017-01-17 V0 (1).pdf (cont'd)
    digest_list.sort()  # dedupliaction is not happening here, happening outside where suitable
    digest_list_names = digest_list
    while len(digest_list_names) != 1:
        last_digest = None
        if (len(digest_list_names) % 2) == 1:
            last_digest = digest_list_names[len(digest_list_names) - 1]

        num_pairs = math.floor(len(digest_list_names) / 2)
        i = 0
        new_digest_list_names = []
        while i < num_pairs:
            digest_pair = []
            digest_pair.append(digest_list_names[i * 2 + 0])
            digest_pair.append(digest_list_names[i * 2 + 1])
            pair_digest = digest_for_digest_pair(digest_pair, hash_format)
            new_digest_list_names.append(pair_digest)
            i = i + 1

        if last_digest is not None:
            new_digest_list_names.append(last_digest)

        digest_list_names = new_digest_list_names

    return digest_list_names[0]


def digest_list_for_list(input_list, hash_format: str):
    input_list = sorted_deduplicates(input_list)
    digest_list = []
    for input_string in input_list:
        digest_list.append(digest_for_string(input_string, hash_format))

    return digest_list


def digest_data_for_digest_string(digest_string, hash_format: str):
    if hash_format == "c4":
        c4context = C4HashContext()
        hash_binary = c4context.data_for_C4ID_string(digest_string)
    else:
        hash_binary = binascii.unhexlify(digest_string)
    return hash_binary


def digest_for_digest_pair(input_pair, hash_format: str):
    input_pair.sort()
    input_data = bytearray(128)
    input_data0 = digest_data_for_digest_string(input_pair[0], hash_format)
    input_data1 = digest_data_for_digest_string(input_pair[1], hash_format)
    input_data[0:64] = input_data0[:]
    input_data[64:128] = input_data1[:]
    return digest_for_data(input_data, hash_format)


def digest_for_data(input_data, hash_format: str):
    hash_context = context_type_for_hash_format(hash_format)()
    hash_context.update(input_data)
    return hash_context.hexdigest()


def digest_for_string(input_string, hash_format: str):
    return digest_for_data(input_string.encode("utf-8"), hash_format)


def sorted_deduplicates(input_list):
    input_list = list(set(input_list))  # remove duplicates
    input_list.sort()  # sort
    return input_list
