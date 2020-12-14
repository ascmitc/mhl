"""
__author__ = "Patrick Renner"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

from mhl.hasher import digest_for_list

def test_C4_con_contiguous_blocks_of_data():
	# test from example in 30MR-WD-ST-2114-C4ID-2017-01-17 V0 (1).pdf
	input_strings = ["alfa", "bravo", "charlie", "delta", "echo", "foxtrot", "golf", "hotel", "india"]
	result_string = digest_for_list(input_strings, 'c4')
	assert(result_string == "c435RzTWWsjWD1Fi7dxS3idJ7vFgPVR96oE95RfDDT5ue7hRSPENePDjPDJdnV46g7emDzWK8LzJUjGESMG5qzuXqq")

