"""
__author__ = "Patrick Renner, Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

ascmhl_tool_name = "ascmhl.py"
ascmhl_tool_version = "0.2 alpha"

ascmhl_folder_name = "ascmhl"
ascmhl_file_extension = ".mhl"
ascmhl_chainfile_name = "chain.txt"
ascmhl_supported_hashformats = ['md5', 'sha1', 'xxh64', 'c4']  # is also decreasing priority list for verification
ascmhl_reference_hash_format = "c4"  # hash format used to reference other files, e.g. in references and the chain
# ascmhl_default_ignore_patterns = ['.DS_Store', ascmhl_folder_name]
