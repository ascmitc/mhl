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

    with open(file_path, 'rb') as fd:
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
    if hash_format == 'md5':
        return hashlib.md5
    elif hash_format == 'sha1':
        return hashlib.sha1
    elif hash_format == 'xxh32':
        return xxhash.xxh32
    elif hash_format == 'xxh64':
        return xxhash.xxh64
    elif hash_format == 'c4':
        return C4HashContext
    assert False, 'unsupported hash format'


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
        zero = '1'  # '0' is not in the C4ID alphabet so '1' is zero

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
            i = i+1

        data = result.to_bytes(64, byteorder='big')
        return data


class DirectoryHashContext:

    def __init__(self, hash_format: str):
        self.hash_format = hash_format
        self.content_hash_strings = []
        self.content_names = []

    def append_hash(self, hash_string: str, item_name: str):
        self.content_hash_strings.append(hash_string)
        self.content_names.append(item_name)

    def final_hash_str(self):
        digest_list_names = digest_list_for_list(digest_list_names, 'c4')
        digest_list_names = sorted_deduplicates(input_list)


        # FIXME: cont'd here!


        # replace this with digest_for_list()

        while digest_list_names.count() != 1:
            last_digest = None
            if (digest_list_names.count()%2) ==1:
                last_digest = digest_list_names[digest_list_names.count-1]

            num_pairs = digest_list_names.count / 2
            i = 0
            new_digest_list_names = []
            while i < num_pairs:
                digest_pair = []
                digest_pair.append(digest_list_names[i*2 + 0])
                digest_pair.append(digest_list_names[i*2 + 1])
                pair_digest = digest_for_pair(digest_pair)
                new_digest_list_names.append(pair_digest)

            if last_digest is not None:
                new_digest_list_names.append(last_digest)

            digest_list_names = new_digest_list_names

        return digest_list_names[0]


        # original code for reference

        # print('append hash:', hash_string, 'item name: ', item_name)
        # first we add the name of the item (file or directory) to the context
        self.hash_context.update(item_name.encode('utf-8'))
        # then we add the binary representation of the hash of the file or directory
        # in case of C4 we can't easily use the binary value so we encode the hash string instead
        if self.hash_format == 'c4':
            hash_binary = hash_string.encode('utf-8')
        else:
            hash_binary = binascii.unhexlify(hash_string)
        self.hash_context.update(hash_binary)

        return self.hash_context.hexdigest()

def digest_for_list(input_list, hash_format: str):
    input_list = sorted_deduplicates(input_list)

    digest_list_names = digest_list_for_list(input_list, hash_format)
    digest_list_names = sorted_deduplicates(digest_list_names)
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
            i = i+1

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

def digest_for_digest_pair(input_pair, hash_format: str):
    input_pair.sort()
    input_data = bytearray(128)
    # fixme: non C4 !
    c4context = C4HashContext()
    input_data0 = c4context.data_for_C4ID_string(input_pair[0])
    input_data1 = c4context.data_for_C4ID_string(input_pair[1])
    input_data[0:64] = input_data0[:]
    input_data[64:128] = input_data1[:]
    return digest_for_data(input_data, hash_format)

def digest_for_data(input_data, hash_format: str):
    hash_context = context_type_for_hash_format(hash_format)()
    hash_context.update(input_data)
    return hash_context.hexdigest()

def digest_for_string(input_string, hash_format: str):
    return digest_for_data(input_string.encode('utf-8'), hash_format)

def sorted_deduplicates(input_list):
    input_list = list(set(input_list))  # remove duplicates
    input_list.sort()                   # sort
    return input_list

