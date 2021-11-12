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


class Hasher(ABC):
    """
    Hasher is an abstract base class (ABC) that outlines the needed hash functionality by ascmhl.
    This abstraction is primarily necessary due to some discrepancies in the hash encoding of C4ID.
    """
    def __init__(self):
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
    def hashlib_type() -> type:
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


class HexHasher(Hasher, ABC):
    """
    HexHasher inherits from the base Hasher class to implement the hexadecimal encoding and decoding of hashes.
    """

    def string_digest(self) -> str:
        return self.hasher.hexdigest()

    @classmethod
    def bytes_from_string_digest(cls, hash_string: str) -> bytes:
        return binascii.unhexlify(hash_string)


class MD5(HexHasher):
    @staticmethod
    def hashlib_type():
        return hashlib.md5


class SHA1(HexHasher):
    @staticmethod
    def hashlib_type():
        return hashlib.sha1


class XXH32(HexHasher):
    @staticmethod
    def hashlib_type():
        return xxhash.xxh32


class XXH64(HexHasher):
    @staticmethod
    def hashlib_type():
        return xxhash.xxh64


class XXH3(HexHasher):
    @staticmethod
    def hashlib_type():
        return xxhash.xxh3_64


class XXH128(HexHasher):
    @staticmethod
    def hashlib_type():
        return xxhash.xxh3_128


class C4(Hasher):
    """
    C4 Hasher is different than the other supported hash algorithms in that it does not adhere to a hex char set.
    """

    # c4 has a different character set than the usual hex char set of other checksum types. encoding is different.
    charset = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"  # C4ID character set

    @staticmethod
    def hashlib_type():
        return hashlib.sha512

    def string_digest(self):
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
    def bytes_from_string_digest(cls, hash_string: str):
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


# TODO: swap magic strings of hash_format for HashType throughout the code (we pass hash_format as str args everywhere)
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


def new_hasher_for_hash_type(hash_format: str) -> Hasher:
    """
    creates a new instance of the appropriate Hasher class based on the hash_format argument

    arguments:
    hash_format -- string value, one of the supported hash formats, e.g. 'md5', 'xxh64'
    """
    hash_type = HashType[hash_format]
    if not hash_type:
        raise ValueError

    return hash_type.value()  # instantiate and return a new hasher of the specified HashType


# TODO: DirectoryHashContext likely should be moved out of this file to where the directories are iterated. DirectoryHashContext isn't like anything else in this file.
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
        hasher = new_hasher_for_hash_type(self.hash_format)
        return hasher.hash_of_hash_list(self.content_hash_strings)

    def final_structure_hash_str(self):
        # we need to mix file names and recursive directory structure here...
        # .. so start with the file names themselves and hash those individually ..
        file_names = []
        for path in self.file_paths:
            file_names.append(os.path.basename(os.path.normpath(path)))

        # hash all filenames into a list
        # e = [hash_data(fn.encode('utf-8'), self.hash_format) for fn in file_names]

        element_list = digest_list_for_list(file_names, self.hash_format)
        # .. and then add digests of concatenated directory names and structure digest
        assert len(self.directory_paths) == len(self.structure_hash_strings)
        for i in range(len(self.directory_paths)):
            directory_name = os.path.basename(os.path.normpath(self.directory_paths[i]))
            element_data = directory_name.encode("utf8") + bytes_for_hash_string(
                self.structure_hash_strings[i], self.hash_format
            )
            element_list.append(hash_data(element_data, self.hash_format))
        # at the end make a list-digest of all the collected and created digests
        structure_hash = hash_of_hash_list(element_list, self.hash_format)
        return structure_hash


def hash_of_hash_list(hash_list: [str], hash_format: str) -> str:
    """
    computes and returns a new hash string from a given list of hash strings.

    arguments:
    hash_list -- list of string hashes to compute a new single hash from
    hash_format -- string value, one of the supported hash formats, e.g. 'md5', 'xxh64'
    """
    hasher = new_hasher_for_hash_type(hash_format)
    return hasher.hash_of_hash_list(hash_list)


def hash_file(filepath: str, hash_format: str) -> str:
    """
    computes and returns a new hash string for a file

    arguments:
    filepath -- string value, path of file to generate hash for.
    hash_format -- string value, one of the supported hash formats, e.g. 'md5', 'xxh64'
    """
    hasher = new_hasher_for_hash_type(hash_format)
    with open(filepath, "rb") as fd:
        # process files in chunks so that large files won't cause excessive memory consumption.
        size = 1024 * 1024  # chunk size 1MB
        chunk = fd.read(size)
        while chunk:
            hasher.update(chunk)
            chunk = fd.read(size)
    return hasher.string_digest()


def hash_data(input_data: bytes, hash_format: str) -> str:
    """
    computes and returns a new hash string from the input data.

    arguments:
    input_data -- the bytes to compute the hash from
    hash_format -- string value, one of the supported hash formats, e.g. 'md5', 'xxh64'
    """
    hasher = new_hasher_for_hash_type(hash_format)
    hasher.update(input_data)
    return hasher.string_digest()


# TODO: remove bytes_for_hash_string in favor of HexHasher.bytes_from_hash_string & C4.bytes_for_hash_string methods
def bytes_for_hash_string(digest_string, hash_format: str):
    hasher = new_hasher_for_hash_type(hash_format)
    return hasher.bytes_from_string_digest(digest_string)


# TODO: remove digest_list_for_list in favor of a unified approach with the rest of this file.
def digest_list_for_list(input_list, hash_format: str):
    input_list = sorted_deduplicates(input_list)
    digest_list = []
    for input_string in input_list:
        digest_list.append(hash_data(input_string.encode(), hash_format))
    return digest_list


# TODO: remove digest_for_digest_pair since it should no longer be needed given our update to Appendix G in the spec.
def digest_for_digest_pair(input_pair, hash_format: str):
    input_pair.sort()
    input_data = bytearray(128)
    input_data0 = bytes_for_hash_string(input_pair[0], hash_format)
    input_data1 = bytes_for_hash_string(input_pair[1], hash_format)
    input_data[0:64] = input_data0[:]
    input_data[64:128] = input_data1[:]
    return hash_data(input_data, hash_format)


# TODO: remove sorted_deduplicates func - should no longer be needed given our update to Appendix G in the spec.
def sorted_deduplicates(input_list):
    input_list = list(set(input_list))  # remove duplicates
    input_list.sort()  # sort
    return input_list
