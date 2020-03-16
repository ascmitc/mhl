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


def create_filehash(hashformat, filepath):
    """creates a hash value for a file and returns the hex string

    arguments:
    filepath -- string value, the path to the file
    hashformat -- string value, one of the supported hash formats, e.g. 'MD5', 'xxhash'
    """
    hash_string = None
    if hashformat == 'MD5':
        hash_string = md5(filepath)
    elif hashformat == 'SHA1':
        hash_string = sha1(filepath)
    elif hashformat == 'xxhash':
        hash_string = xxhash64(filepath)
    elif hashformat == 'C4':
        hash_string = c4(filepath)

    return hash_string


def md5(file_path):
    return generate_checksum(hashlib.md5, file_path)


def sha1(file_path):
    return generate_checksum(hashlib.sha1, file_path)


def xxhash64(file_path):
    return generate_checksum(xxhash.xxh64, file_path)


def c4(file_path):
    sha512_string = generate_checksum(hashlib.sha512, file_path)

    charset = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
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
