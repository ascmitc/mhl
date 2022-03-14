"""
__author__ = "Jon Waggoner, Patrick Renner"
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
    data = b"media-hash-list"
    # map of hash algorithm to expected hash value
    hash_type_and_value = {
        "md5": "9db0fc9f30f5ee70041a7538809e2858",
        "sha1": "7b57673ac5633937a55b59009ad0c57ee08188b7",
        "xxh32": "f67c5a4f",
        "xxh64": "584b2ea1974f2b7c",
        "xxh3": "6d4cbd75905c81aa",
        "xxh128": "61a67c014f703a456ee7a776fd8c06bd",
        "c4": "c456LycWwpMMS7VDZEKvYv2L1uJS6s4qAFnaJdnQiy5JVbBFZMA8aLDS6SPaJjLqxXH4qZdnbuktopMt9frtC2qL1R",
    }
    # ensure all of our hash types produce the expected hash value for the data
    for k, v in hash_type_and_value.items():
        h = hash_data(data, k)
        assert h == v  # assert our computed hash equals expected hash


def test_aggregate_hashing_of_data(fs):
    # the data to hash
    data = b"media-hash-list"

    # map of hash algorithm to expected hash value
    hash_type_and_value = {
        "md5": "9db0fc9f30f5ee70041a7538809e2858",
        "sha1": "7b57673ac5633937a55b59009ad0c57ee08188b7",
        "xxh32": "f67c5a4f",
        "xxh64": "584b2ea1974f2b7c",
        "xxh3": "6d4cbd75905c81aa",
        "xxh128": "61a67c014f703a456ee7a776fd8c06bd",
        "c4": "c456LycWwpMMS7VDZEKvYv2L1uJS6s4qAFnaJdnQiy5JVbBFZMA8aLDS6SPaJjLqxXH4qZdnbuktopMt9frtC2qL1R",
    }

    # Generate the hash pairings for the file and specified formats
    hash_lookup = multiple_format_hash_data(data, hash_type_and_value.keys())

    # Make sure each pair's value matches the known hash value
    evaluated_formats = []
    for hash_format, hash_value in hash_lookup.items():
        known_hash = hash_type_and_value[hash_format]
        evaluated_formats.append(hash_format)
        assert hash_value == known_hash

    # Make sure each stored format was represented in the hash pairings
    for k in hash_type_and_value:
        assert k in evaluated_formats


def test_hash_file(fs):
    # write some data to a file so we can hash it.
    file, data = "/data-file.txt", "media-hash-list"
    fs.create_file(file, contents=data)
    # map of hash algorithm to expected hash value
    hash_type_and_value = {
        "md5": "9db0fc9f30f5ee70041a7538809e2858",
        "sha1": "7b57673ac5633937a55b59009ad0c57ee08188b7",
        "xxh32": "f67c5a4f",
        "xxh64": "584b2ea1974f2b7c",
        "xxh3": "6d4cbd75905c81aa",
        "xxh128": "61a67c014f703a456ee7a776fd8c06bd",
        "c4": "c456LycWwpMMS7VDZEKvYv2L1uJS6s4qAFnaJdnQiy5JVbBFZMA8aLDS6SPaJjLqxXH4qZdnbuktopMt9frtC2qL1R",
    }
    # ensure all of our hash types produce the expected hash value for the file data
    for k, v in hash_type_and_value.items():
        h = hash_file(file, k)
        assert h == v  # assert our computed hash equals expected hash


def test_aggregate_hashing_of_file(fs):
    # write some data to a file so we can hash it.
    file, data = "/data-file.txt", "media-hash-list"
    fs.create_file(file, contents=data)
    # map of hash algorithm to expected hash value
    hash_type_and_value = {
        "md5": "9db0fc9f30f5ee70041a7538809e2858",
        "sha1": "7b57673ac5633937a55b59009ad0c57ee08188b7",
        "xxh32": "f67c5a4f",
        "xxh64": "584b2ea1974f2b7c",
        "xxh3": "6d4cbd75905c81aa",
        "xxh128": "61a67c014f703a456ee7a776fd8c06bd",
        "c4": "c456LycWwpMMS7VDZEKvYv2L1uJS6s4qAFnaJdnQiy5JVbBFZMA8aLDS6SPaJjLqxXH4qZdnbuktopMt9frtC2qL1R",
    }

    # Generate the hash pairings for the file and specified formats
    hash_lookup = multiple_format_hash_file(file, hash_type_and_value.keys())

    # Make sure each pair's value matches the known hash value
    evaluated_formats = []
    for hash_format, hash_value in hash_lookup.items():
        known_hash = hash_type_and_value[hash_format]
        evaluated_formats.append(hash_format)
        assert hash_value == known_hash

    # Make sure each stored format was represented in the hash pairings
    for k in hash_type_and_value:
        assert k in evaluated_formats


def test_hash_of_hash_list():
    # the hash list to hash - purposefully in reverse order here to ensure data ends up sorted.
    hash_list = ["bb", "aa10", "aa01", "aa"]
    # map of hash algorithm to expected hash string
    hash_type_and_value = {
        "md5": "88abf5c156ff637c6380ae461fc50c3f",
        "sha1": "22ad6b98111f6571c9ae1449988260b920960c16",
        "xxh32": "48d7bd5a",
        "xxh64": "c4e803e454029ee4",
        "xxh3": "d908e88da5ad4928",
        "xxh128": "9041108a28887a9d35b4eac5bbaa5794",
        # TODO: add c4 in here - it doesn't like my hash list above due to c4 encoder requiring length
    }
    # ensure all of our hash types produce the expected hash value for the hash list
    for k, v in hash_type_and_value.items():
        h = hash_of_hash_list(hash_list, k)
        assert h == v  # assert our computed hash equals expected hash


def test_hash_list_concat_equals_chunking():
    # this is a test to prove that concatenating all strings then hashing is same as feeding them to hasher one by one
    # the hash list to hash
    hash_list = ["bb", "aa10", "aa01", "aa"]
    # ensure all of our hash types produce the expected hash value for the hash list
    for ht in HashType:
        if ht == HashType.c4:
            continue  # skipping c4 on this test for same reason as test_hash_of_hash_list
        hasher = new_hasher_for_hash_type(ht.name)
        h1 = hasher.hash_of_hash_list(hash_list)
        concat = hasher.bytes_from_string_digest("".join(hash_list))
        h2 = hasher.hash_data(concat)
        assert h1 == h2  # assert that sequentially feeding hashes is same as concat then feeding hashes
