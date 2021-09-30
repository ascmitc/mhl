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
    """parsing the MHL directory file and building the MHLChain for the chain member variable"""
    logger.debug(f'parsing "{os.path.basename(file_path)}"...')

    chain = MHLChain(file_path)
    chain.file_path = file_path
    current_object = None

    if not os.path.exists(file_path):
        return chain

    file = open(file_path, "rb")
    for event, element in etree.iterparse(file, events=("start", "end")):

        # check if we need to create a new container
        if event == "start":
            # the tag might contain the namespace like {urn:ASC:MHL:v2.0}hash, so we need to strip the namespace part
            # doing it with split is faster than using the lxml QName method
            tag = element.tag.split("}", 1)[-1]

            if not current_object:
                if tag == "hashlist":
                    current_object = MHLChainGeneration()

        elif event == "end":
            if current_object:
                tag = element.tag.split("}", 1)[-1]

                if type(current_object) is MHLChainGeneration:
                    if tag == "path":
                        current_object.ascmhl_filename = element.text
                    elif tag in ascmhl_supported_hashformats:
                        current_object.hash_format = tag
                        current_object.hash_string = element.text
                    elif tag == "hashlist":
                        current_object.generation_number = element.attrib.get("sequencenr")
                        chain.append_generation(current_object)
                        current_object = None

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

    for generation in chain.generations:
        _write_xml_element_to_file(file, _hashlist_xml_element_from_chaingeneration(generation), "  ")

    # write new hashlist
    _write_xml_element_to_file(file, _hashlist_xml_element_from_hashlist(new_hash_list), "  ")

    current_indent = current_indent[:-2]
    _write_xml_string_to_file(file, "</ascmhldirectory>\n", current_indent)
    file.flush()


def _write_xml_element_to_file(file, xml_element, indent: str):
    xml_string = etree.tostring(xml_element, pretty_print=True, encoding="unicode")
    _write_xml_string_to_file(file, xml_string, indent)


def _write_xml_string_to_file(file, xml_string: str, indent: str):
    result = textwrap.indent(xml_string, indent)
    file.write(result.encode("utf-8"))


def _hashlist_xml_element_from_hashlist(hash_list: MHLHashList):
    """builds and returns one <hashlist> element for a given HashList object"""

    hash_list_element = E.hashlist(
        E.path(os.path.basename(hash_list.file_path)),
        E.c4(hash_list.generate_reference_hash()),
    )
    hash_list_element.attrib["sequencenr"] = str(hash_list.generation_number)

    return hash_list_element


def _hashlist_xml_element_from_chaingeneration(generation: MHLChainGeneration):
    """builds and returns one <hashlist> element for a given ChainGeneration object"""

    if generation.hash_format == "c4":
        hash_list_element = E.hashlist(
            E.path(generation.ascmhl_filename),
            E.c4(generation.hash_string),
        )
        hash_list_element.attrib["sequencenr"] = str(generation.generation_number)

        return hash_list_element
    else:
        logger.error("ERR: fixme: non-c4 hash in chain file, not implemented")
        return E.hashlist()
