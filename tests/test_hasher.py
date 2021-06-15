"""
__author__ = "Patrick Renner"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

from ascmhl.hasher import digest_for_list, digest_for_string


def test_C4_non_contiguous_blocks_of_data():
    # test from example in 30MR-WD-ST-2114-C4ID-2017-01-17 V0 (1).pdf
    input_strings = ["alfa", "bravo", "charlie", "delta", "echo", "foxtrot", "golf", "hotel", "india"]
    list_digest = digest_for_list(input_strings, "c4")
    assert list_digest == "c435RzTWWsjWD1Fi7dxS3idJ7vFgPVR96oE95RfDDT5ue7hRSPENePDjPDJdnV46g7emDzWK8LzJUjGESMG5qzuXqq"

    # test via
    # "When this method is applied to a single block of data, the method returns the C4 ID of that single block of data." from 30MR-WD-ST-2114-C4ID-2017-01-17 V0 (1).pdf
    concatenated_input_strings = "".join(input_strings)
    string_digest = digest_for_string(concatenated_input_strings, "c4")
    short_list = []
    short_list.append(concatenated_input_strings)
    list_digest = digest_for_list(short_list, "c4")
    assert string_digest == list_digest


def test_non_contiguous_blocks_of_data():
    input_strings = ["alfa", "bravo", "charlie", "delta", "echo", "foxtrot", "golf", "hotel", "india"]
    list_digest = digest_for_list(input_strings, "md5")
    assert list_digest == "df68bb8957e25c0049d2c20128f08bb0"

    list_digest = digest_for_list(input_strings, "sha1")
    assert list_digest == "69ee70fa6143be1bb84bfbf194c3dada6e4858e3"

    list_digest = digest_for_list(input_strings, "xxh32")
    assert list_digest == "e5107d45"

    list_digest = digest_for_list(input_strings, "xxh64")
    assert list_digest == "dd848f48e61abebb"
