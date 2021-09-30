"""
__author__ = "Patrick Renner"
__copyright__ = "Copyright 2021, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

from . import logger
from .__version__ import ascmhl_reference_hash_format
from .chain import MHLChain, MHLChainGeneration
from .hashlist import MHLHashList
from .hasher import create_filehash
import os
import textwrap
from timeit import default_timer as timer
import dateutil.parser

from lxml import etree
from lxml.builder import E

from . import logger
from .hashlist import *
from .utils import datetime_isostring
from .__version__ import ascmhl_supported_hashformats
from .hashlist import (
    MHLCreatorInfo,
    MHLHashEntry,
    MHLHashList,
    MHLHashListReference,
    MHLMediaHash,
    MHLProcessInfo,
    MHLTool,
)
from .ignore import MHLIgnoreSpec
from .utils import datetime_isostring


def parse(file_path):
    """parsing the chain.txt file and building the MHLChain for the chain member variable"""
    logger.debug(f'parsing "{os.path.basename(file_path)}"...')

    chain = MHLChain(file_path)

    # TODO




    return chain


def write_chain(chain: MHLChain, new_hash_list: MHLHashList):
    logger.debug(f'writing "{os.path.basename(chain.file_path)}"...')

    """creates a new chain file and writes the xml to disk
    """

    directory_path = os.path.dirname(chain.file_path)
    if not os.path.isdir(directory_path):
        os.mkdir(directory_path)

    file = open(chain.file_path, "wb")
    file.write(b'<?xml version="1.0" encoding="UTF-8"?>\n<ascmhldirectory xmlns="urn:ASC:MHL:DIRECTORY:v2.0">\n')
    current_indent = "  "

    # TODO for hash_list in chain

    # ...

    # write new hashlist
    _write_xml_element_to_file(file, _hashlist_xml_element(new_hash_list), "  ")

    current_indent = current_indent[:-2]
    _write_xml_string_to_file(file, "</ascmhldirectory>\n", current_indent)
    file.flush()


def _write_xml_element_to_file(file, xml_element, indent: str):
    xml_string = etree.tostring(xml_element, pretty_print=True, encoding="unicode")
    _write_xml_string_to_file(file, xml_string, indent)


def _write_xml_string_to_file(file, xml_string: str, indent: str):
    result = textwrap.indent(xml_string, indent)
    file.write(result.encode("utf-8"))


def _hashlist_xml_element(hash_list: MHLHashList):
    """builds and returns one <hashlist> element for a given HashList object"""

    root_path = os.path.dirname(os.path.dirname(hash_list.file_path))
    hash_list_element = E.hashlist(
        E.path(os.path.relpath(hash_list.file_path, root_path)),
        E.c4(hash_list.generate_reference_hash()),
    )
    hash_list_element.attrib["sequencenr"] = str(hash_list.generation_number)

    return hash_list_element
