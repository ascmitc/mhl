"""
__author__ = "Alexander Sahm, Patrick Renner"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner"
__email__ = "opensource@pomfort.com"
"""

import hashlib
import xxhash


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
    hashformat -- string value, one of the supported hash formats, e.g. 'MD5', 'xxhash'
    """
    csum_type = context_type_for_hash_format(hash_format)
    if csum_type:
        return generate_checksum(csum_type, filepath)

    return None


def context_type_for_hash_format(hash_format):
    if hash_format == 'MD5':
        return hashlib.md5
    elif hash_format == 'SHA1':
        return hashlib.sha1
    elif hash_format == 'xxh64':
        return xxhash.xxh64
    elif hash_format == 'C4':
        return C4HashContext
    return None


class C4HashContext:

    def __init__(self):
        self.internal_context = hashlib.sha512()

    def update(self, input_data):
        self.internal_context.update(input_data)

    def hexdigest(self):
        sha512_string = self.internal_context.hexdigest()

        charset = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        base58 = 58  # the encoding basis
        c4id_length = 90  # the guaranteed length
        zero = '1'  # '0' is not in the C4ID alphabet so '1' is zero

        hash_value = int(sha512_string, 16)
        c4_string = ""
        while hash_value is not 0:
            modulo = hash_value % base58
            hash_value = hash_value // base58
            c4_string = charset[modulo] + c4_string

        c4_string = "c4" + c4_string.ljust(c4id_length - 2, zero)
        return c4_string
