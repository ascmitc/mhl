"""
__author__ = "Jon Waggoner, Alexander Sahm, Patrick Renner"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner"
__email__ = "opensource@pomfort.com"
"""
import binascii
import hashlib

import xxhash
import os
from enum import Enum, unique
from abc import ABC, abstractmethod
from typing import Dict


class Hasher(ABC):
    """
    Hasher is an abstract base class (ABC) that outlines the needed hash functionality by ascmhl.
    This abstraction is primarily necessary due to some discrepancies in the hash encoding of C4ID.
    """

    def __init__(self):
        # instantiate our internal hash generator. such as: hashlib.md5 or xxhash.xxh64
        self.hasher = self.hashlib_type()()

    def update(self, data: bytes) -> None:
        """
        writes data to the internal hasher.
        """
        self.hasher.update(data)

    @abstractmethod
    def string_digest(self) -> str:
        """
        get the string digest of the current state of the internal hasher
        """
        pass

    @classmethod
    @abstractmethod
    def bytes_from_string_digest(cls, hash_string: str) -> bytes:
        """
        helper to convert a hash string to its underlying byte representation adhering to the encoding of the hash_type.
        """
        pass

    @staticmethod
    @abstractmethod
    def hashlib_type():
        """
        returns the underlying wrapped hasher type from either the hashlib or xxhash libraries.
        such as: hashlib.md5 or xxhash.xxh64
        """
        pass

    @classmethod
    def hash_of_hash_list(cls, hash_list: [str]) -> str:
        """
        generates and returns a new hash string by hashing a list of existing hash strings.
        """
        hasher = cls()

        # empty checksum for empty lists
        if len(hash_list) == 0:
            return hasher.string_digest()

        # sort lexicographically
        hash_list.sort()
        for hash_string in hash_list:
            hasher.update(cls.bytes_from_string_digest(hash_string))

        return hasher.string_digest()

    @classmethod
    def hash_file(cls, filepath: str) -> str:
        """
        computes and returns a new hash string for a file

        arguments:
        filepath -- string value, path of file to generate hash for.
        hash_format -- string value, one of the supported hash formats, e.g. 'md5', 'xxh64'
        """
        hasher = cls()
        with open(filepath, "rb") as fd:
            # process files in chunks so that large files won't cause excessive memory consumption.
            size = 1024 * 1024  # chunk size 1MB
            chunk = fd.read(size)
            while chunk:
                hasher.update(chunk)
                chunk = fd.read(size)

        return hasher.string_digest()

    @classmethod
    def hash_data(cls, input_data: bytes) -> str:
        """
        computes and returns a new hash string from the input data.

        arguments:
        input_data -- the bytes to compute the hash from
        hash_format -- string value, one of the supported hash formats, e.g. 'md5', 'xxh64'
        """
        hasher = cls()
        hasher.update(input_data)
        return hasher.string_digest()


class HexHasher(Hasher, ABC):
    """
    HexHasher inherits from the base Hasher class to implement the hexadecimal encoding and decoding of hashes.
    Cannot be instantiated directly. Choose a subclass.
    """

    def string_digest(self) -> str:
        return self.hasher.hexdigest()

    @classmethod
    def bytes_from_string_digest(cls, hash_string: str) -> bytes:
        return binascii.unhexlify(hash_string)


class MD5(HexHasher):
    """
    md5 checksum generator.
    """

    @staticmethod
    def hashlib_type():
        return hashlib.md5


class SHA1(HexHasher):
    """
    sha1 checksum generator.
    """

    @staticmethod
    def hashlib_type():
        return hashlib.sha1


class XXH32(HexHasher):
    """
    xxh32 checksum generator.
    """

    @staticmethod
    def hashlib_type():
        return xxhash.xxh32


class XXH64(HexHasher):
    """
    xxh64 checksum generator.
    """

    @staticmethod
    def hashlib_type():
        return xxhash.xxh64


class XXH3(HexHasher):
    """
    xxh3 checksum generator.
    """

    @staticmethod
    def hashlib_type():
        return xxhash.xxh3_64


class XXH128(HexHasher):
    """
    xxh128 checksum generator.
    """

    @staticmethod
    def hashlib_type():
        return xxhash.xxh3_128


class C4(Hasher):
    """
    C4 checksum generator.
    C4 Hasher is different than the other supported hash algorithms in that it does not adhere to a hex char set.
    """

    # c4 has a different character set than the usual hex char set of other checksum types. encoding is different.
    charset = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"  # C4ID character set

    @staticmethod
    def hashlib_type():
        return hashlib.sha512

    def string_digest(self) -> str:
        sha512_string = self.hasher.hexdigest()

        base58 = 58  # the encoding basis
        c4id_length = 90  # the guaranteed length
        zero = "1"  # '0' is not in the C4ID alphabet so '1' is zero

        hash_value = int(sha512_string, 16)
        c4_string = ""
        while hash_value != 0:
            modulo = hash_value % base58
            hash_value = hash_value // base58
            c4_string = C4.charset[modulo] + c4_string

        c4_string = "c4" + c4_string.rjust(c4id_length - 2, zero)
        return c4_string

    @classmethod
    def bytes_from_string_digest(cls, hash_string: str) -> bytes:
        base58 = 58  # the encoding basis
        c4id_length = 90  # the guaranteed length
        result = 0
        i = 2

        while i < c4id_length:
            temp = C4.charset.index(hash_string[i])
            result = result * base58 + temp
            i = i + 1

        data = result.to_bytes(64, byteorder="big")
        return data


@unique
class HashType(Enum):
    """
    HashType wraps all ascmhl supported hash formats.
    """

    md5 = MD5
    sha1 = SHA1
    xxh32 = XXH32
    xxh64 = XXH64
    xxh3 = XXH3
    xxh128 = XXH128
    c4 = C4


class AggregateHasher:
    def __init__(self, hash_formats: [str]):

        # Build a hasher for each format
        hasher_lookup = Dict[str, str]
        for hash_format in hash_formats:
            hasher_lookup[hash_format] = new_hasher_for_hash_type(hash_format)

        self.hash_formats = hash_formats
        self.hasher_lookup = hasher_lookup

    """
    Handles multiple hashing to facilitate a read-once create-many hashing paradigm
    """

    @classmethod
    def hash_file(cls, file_path: str, hash_formats: [str]) -> Dict[str, str]:
        """
        computes and returns new hash strings for a file

        arguments:
        file_path -- string value, path of file to generate hash for.
        hash_formats -- array string values, each entry should be one of the supported hash formats, e.g. 'md5', 'xxh64'
        """

        # Build a hasher for each supplied format
        hasher_lookup = {}
        for hash_format in hash_formats:
            hasher = new_hasher_for_hash_type(hash_format)
            hasher_lookup[hash_format] = hasher

        # Open the file
        with open(file_path, "rb") as fd:
            # process files in chunks so that large files won't cause excessive memory consumption.
            size = 1024 * 1024  # chunk size 1MB
            chunk = fd.read(size)
            while chunk:
                # Update each stored hasher with the read chunk
                for hash_format in hasher_lookup:
                    hasher_lookup[hash_format].update(chunk)

                chunk = fd.read(size)

        # Get the digest from each hasher
        hash_output_lookup = {}
        for hash_format in hasher_lookup:
            hash_output_lookup[hash_format] = hasher_lookup[hash_format].string_digest()

        return hash_output_lookup

    @classmethod
    def hash_data(cls, input_data: bytes, hash_formats: [str]) -> Dict[str, str]:
        """
        computes and returns new hash strings for a file

        arguments:
        input_data -- the bytes to compute the hash from.
        hash_formats -- array string values, each entry should be one of the supported hash formats, e.g. 'md5', 'xxh64'
        """

        # Build a hash for each supplied format
        hash_output_lookup = {}
        for hash_format in hash_formats:
            hash_generator = new_hasher_for_hash_type(hash_format)
            hash_generator.update(input_data)
            computed_hash = hash_generator.string_digest()
            hash_output_lookup[hash_format] = computed_hash

        return hash_output_lookup


class DirectoryHashContext:
    """
    DirectoryHashContext wraps the data necessary to compute directory checksums.
    """

    def __init__(self, hash_format: str):

        self.hash_format = hash_format
        self.hasher = new_hasher_for_hash_type(hash_format)
        self.content_hash_strings = []
        self.structure_hash_strings = []

    def append_file_hash(self, path: str, content_hash_string: str):
        """
        append child file data to this directory context.
        """
        self.content_hash_strings.append(content_hash_string)

        # structure hashes are computed from lists of children name+hash strings
        path_bytes = os.path.basename(os.path.normpath(path)).encode("utf8")
        hash_bytes = self.hasher.bytes_from_string_digest(content_hash_string)
        structure_hash = self.hasher.hash_data(path_bytes + hash_bytes)
        self.structure_hash_strings.append(structure_hash)

    def append_directory_hashes(self, path: str, content_hash_string: str, structure_hash_string: str):
        """
        append child directory data to this directory context.
        """
        self.content_hash_strings.append(content_hash_string)

        # structure hashes are computed from lists of children name+hash strings
        path_bytes = os.path.basename(os.path.normpath(path)).encode("utf8")
        hash_bytes = self.hasher.bytes_from_string_digest(structure_hash_string)
        structure_hash = self.hasher.hash_data(path_bytes + hash_bytes)
        self.structure_hash_strings.append(structure_hash)

    def final_content_hash_str(self):
        """
        compute and return the content hash of this directory context by hashing the child content hash list.
        """
        return self.hasher.hash_of_hash_list(self.content_hash_strings)

    def final_structure_hash_str(self):
        """
        compute and return the structure hash of this directory context by hashing the child structure hash list.
        """
        return self.hasher.hash_of_hash_list(self.structure_hash_strings)


def new_hasher_for_hash_type(hash_format: str) -> Hasher:
    """
    creates a new instance of the appropriate Hasher class based on the hash_format argument

    arguments:
    hash_format -- string value, one of the supported hash formats, e.g. 'md5', 'xxh64'
    """
    if not hash_format:
        raise ValueError
    hash_type = HashType[hash_format]
    if not hash_type:
        raise ValueError

    return hash_type.value()  # instantiate and return a new Hasher of the specified HashType


def hash_of_hash_list(hash_list: [str], hash_format: str) -> str:
    """
    computes and returns a new hash string from a given list of hash strings.

    arguments:
    hash_list -- list of string hashes to compute a new single hash from
    hash_format -- string value, one of the supported hash formats, e.g. 'md5', 'xxh64'
    """
    hasher = new_hasher_for_hash_type(hash_format)
    return hasher.hash_of_hash_list(hash_list)


def multiple_format_hash_file(file_path: str, hash_formats: [str]) -> Dict[str, str]:
    """
    computes and returns a new hash strings for a file

    arguments:
    file_path -- string value, path of file to generate hash for.
    hash_formats -- string values, each entry is one of the supported hash formats, e.g. 'md5', 'xxh64'
    """
    return AggregateHasher.hash_file(file_path, hash_formats)


def hash_file(filepath: str, hash_format: str) -> str:
    """
    computes and returns a new hash string for a file

    arguments:
    filepath -- string value, path of file to generate hash for.
    hash_format -- string value, one of the supported hash formats, e.g. 'md5', 'xxh64'
    """
    hasher = new_hasher_for_hash_type(hash_format)
    return hasher.hash_file(filepath)


def hash_data(input_data: bytes, hash_format: str) -> str:
    """
    computes and returns a new hash string from the input data.

    arguments:
    input_data -- the bytes to compute the hash from
    hash_format -- string value, one of the supported hash formats, e.g. 'md5', 'xxh64'
    """
    hasher = new_hasher_for_hash_type(hash_format)
    return hasher.hash_data(input_data)


def multiple_format_hash_data(input_data: bytes, hash_formats: [str]) -> Dict[str, str]:
    """
    computes and returns new hash strings from the input data
    arguments:
    input_data -- the bytes to compute the hash from
    hash_formats -- string values, each entry is one of the supported hash formats, e.g. 'md5', 'xxh64'
    """
    return AggregateHasher.hash_data(input_data, hash_formats)


def bytes_for_hash_string(hash_string: str, hash_format: str) -> bytes:
    """
    wraps the different Hasher string to byte conversions

    arguments:
    hash_string -- string value, the hash string to convert to bytes
    hash_format -- string value, one of the supported hash formats, e.g. 'md5', 'xxh64'
    """
    hasher = new_hasher_for_hash_type(hash_format)
    return hasher.bytes_from_string_digest(hash_string)
