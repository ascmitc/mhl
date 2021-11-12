"""
__author__ = "Patrick Renner"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

import pytest
from ascmhl.hasher import *


def test_cannot_instantiate_abstract_classes():
    with pytest.raises(TypeError):
        h = Hasher()  # this should raise TypeError - abstract class
    with pytest.raises(TypeError):
        h = HexHasher()  # this should raise TypeError - abstract class


def test_hash_data():
    # the data to hash
    data = b'media-hash-list'
    # map of hash algorithm to expected hash value
    hash_type_and_value = {
        'md5': '9db0fc9f30f5ee70041a7538809e2858',
        'sha1': '7b57673ac5633937a55b59009ad0c57ee08188b7',
        'xxh32': 'f67c5a4f',
        'xxh64': '584b2ea1974f2b7c',
        'xxh3': '6d4cbd75905c81aa',
        'xxh128': '61a67c014f703a456ee7a776fd8c06bd',
        'c4': 'c456LycWwpMMS7VDZEKvYv2L1uJS6s4qAFnaJdnQiy5JVbBFZMA8aLDS6SPaJjLqxXH4qZdnbuktopMt9frtC2qL1R',
    }
    # ensure all of our hash types produce the expected hash value for the data
    for k, v in hash_type_and_value.items():
        hasher = new_hasher_for_hash_type(k)
        h = hasher.hash_data(data)
        assert h == v  # assert our computed hash equals expected hash


def test_hash_file(fs):
    # write some data to a file so we can hash it.
    file, data = "/data-file.txt", "media-hash-list"
    fs.create_file(file, contents=data)
    # map of hash algorithm to expected hash value
    hash_type_and_value = {
        'md5': '9db0fc9f30f5ee70041a7538809e2858',
        'sha1': '7b57673ac5633937a55b59009ad0c57ee08188b7',
        'xxh32': 'f67c5a4f',
        'xxh64': '584b2ea1974f2b7c',
        'xxh3': '6d4cbd75905c81aa',
        'xxh128': '61a67c014f703a456ee7a776fd8c06bd',
        'c4': 'c456LycWwpMMS7VDZEKvYv2L1uJS6s4qAFnaJdnQiy5JVbBFZMA8aLDS6SPaJjLqxXH4qZdnbuktopMt9frtC2qL1R',
    }
    # ensure all of our hash types produce the expected hash value for the file data
    for k, v in hash_type_and_value.items():
        hasher = new_hasher_for_hash_type(k)
        h = hasher.hash_file(file)
        assert h == v  # assert our computed hash equals expected hash


def test_hash_of_hash_list():
    # the hash list to hash
    hash_list = ['aa', 'bb', 'cc', 'dd']  # valid chars in all of our hash algorithms
    # map of hash algorithm to expected hash string
    hash_type_and_value = {
        'md5': 'ca6ffbf95b47864fd4e73f2601326304',
        'sha1': 'a7b7e9592daa0896db0517bf8ad53e56b1246923',
        'xxh32': '653fda5e',
        'xxh64': '781c641b331c6481',
        'xxh3': 'bfd691c4f6750254',
        'xxh128': 'ab65044d6377f7528d403d7d59bb88f3',
        # TODO: add c4 in here - it doesn't seem to like my hash list above due to decoder
    }
    # ensure all of our hash types produce the expected hash value for the hash list
    for k, v in hash_type_and_value.items():
        hasher = new_hasher_for_hash_type(k)
        h = hasher.hash_of_hash_list(hash_list)
        assert h == v  # assert our computed hash equals expected hash


def test_hash_list_concat_equals_chunking():
    # this is a test to prove that concatenating all strings then hashing is same as feeding them to hasher one by one
    # the hash list to hash
    hash_list = ['aa', 'bb', 'cc', 'dd']  # valid chars in all of our hash algorithms
    # ensure all of our hash types produce the expected hash value for the hash list
    for ht in HashType:
        if ht == HashType.c4:
            continue  # skipping c4 on this test since it has a length requirement.
        hasher = new_hasher_for_hash_type(ht.name)
        h1 = hasher.hash_of_hash_list(hash_list)
        concat = hasher.bytes_from_string_digest("".join(hash_list))
        h2 = hasher.hash_data(concat)
        assert h1 == h2  # assert that sequentially feeding hashes is same as concat then feeding hashes
