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

    def update(self, input_data):
        self.internal_context.update(input_data)

    def hexdigest(self):
        sha512_string = self.internal_context.hexdigest()

        charset = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        base58 = 58  # the encoding basis
        c4id_length = 90  # the guaranteed length
        zero = "1"  # '0' is not in the C4ID alphabet so '1' is zero

        hash_value = int(sha512_string, 16)
        c4_string = ""
        while hash_value != 0:
            modulo = hash_value % base58
            hash_value = hash_value // base58
            c4_string = charset[modulo] + c4_string

        c4_string = "c4" + c4_string.rjust(c4id_length - 2, zero)
        return c4_string


class DirectoryHashContext:
    def __init__(self, hash_format: str):
        self.hash_context = context_type_for_hash_format(hash_format)()
        self.hash_format = hash_format

    def append_hash(self, hash_string: str, item_name: str):
        # print('append hash:', hash_string, 'item name: ', item_name)
        # first we add the name of the item (file or directory) to the context
        self.hash_context.update(item_name.encode("utf-8"))
        # then we add the binary representation of the hash of the file or directory
        # in case of C4 we can't easily use the binary value so we encode the hash string instead
        if self.hash_format == "c4":
            hash_binary = hash_string.encode("utf-8")
        else:
            hash_binary = binascii.unhexlify(hash_string)
        self.hash_context.update(hash_binary)

    def final_hash_str(self):
        return self.hash_context.hexdigest()
