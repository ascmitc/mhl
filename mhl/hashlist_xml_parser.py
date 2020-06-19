"""
__author__ = "Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

import textwrap
from timeit import default_timer as timer
from lxml import etree
from lxml.builder import E
from xml.sax.saxutils import quoteattr

from .utils import datetime_isostring
from .hashlist import *


def parse(file_path):
    """parsing the MHL XML file and building the MHLHashList for the hash_list member variable"""
    logger.debug(f'parsing {file_path}...')

    start = timer()

    hash_list = MHLHashList()
    hash_list.file_path = file_path
    current_object = None
    supported_hash_formats = {'md5', 'sha1', 'c4', 'xxh32', 'xxh64', 'xxh3'}
    # use iterparse to prevent large memory usage when parsing large files
    # pass a file handle to iterparse instead of the path directly to support the fake filesystem used in the tests
    file = open(file_path, "rb")
    for event, element in etree.iterparse(file, events=('start', 'end')):
        if current_object and event == 'end':
            # the tag might contain the namespace like {urn:ASC:MHL:v2.0}hash, so we need to strip the namespace part
            # doing it with split is faster than using the lxml QName method
            tag = element.tag.split('}', 1)[-1]
            if type(current_object) is MHLCreatorInfo:
                if tag == 'creationdate':
                    current_object.creation_date = element.text
                elif tag == 'tool':
                    current_object.tool = MHLTool(element.text, element.attrib['version'])
                elif tag == 'rootpath':
                    current_object.root_path = element.text
                elif tag == 'creatorinfo':
                    hash_list.creator_info = current_object
                    current_object = None
            elif type(current_object) is MHLMediaHash:
                if tag == 'path':
                    current_object.path = element.text
                    current_object.filesize = int(element.attrib['size'])
                # TODO: parse date
                # elif tag == 'lastmodificationdate':
                # 	current_object.filesize = element.text
                elif tag in supported_hash_formats:
                    entry = MHLHashEntry(tag, element.text, element.attrib['action'])
                    current_object.append_hash_entry(entry)
                elif tag == 'hash':
                    hash_list.append_hash(current_object)
                    current_object = None
            elif type(current_object) is MHLHashListReference:
                if tag == 'path':
                    current_object.path = element.text
                elif tag == 'c4':
                    current_object.reference_hash = element.text
                elif tag == 'hashlistreference':
                    hash_list.append_hash_list_reference(current_object)
                    current_object = None

            # in order to keep memory usage low while parsing, we clear the finished element
            # and remove it from the parent element as well but since this is clearing the children anyways
            # we only need to do it if we are not currently parsing a container object
            if not current_object:
                element.clear()
                while element.getprevious() is not None:
                    del element.getparent()[0]

        # check if we need to create a new container
        elif not current_object and event == 'start':
            # remove namespace here again instead of outside of the if
            # since we don't want to do it for tags we don't compare at all
            tag = element.tag.split('}', 1)[-1]
            if tag == 'hash':
                current_object = MHLMediaHash()
            elif tag == 'creatorinfo':
                current_object = MHLCreatorInfo()
            elif tag == 'hashlistreference':
                current_object = MHLHashListReference()

    logger.debug(f'parsing took: {timer() - start}')

    return hash_list


def write_hash_list(hash_list: MHLHashList, file_path: str):
    """creates a new mhl file and writes the xml to disk

    we write the file step by step to reduce memory load while writing large files
    e.g. we create xml objects only for single elemnts like one media hash element and write it to disk
    before creating the next one"""

    logger.verbose(f'writing \"{os.path.basename(file_path)}\"...')

    if not os.path.isdir(os.path.dirname(file_path)):
        os.mkdir(os.path.dirname(file_path))

    file = open(file_path, 'wb')
    file.write(b'<?xml version="1.0" encoding="UTF-8"?>\n<hashlist version="2.0" xmlns="urn:ASC:MHL:v2.0">\n')
    current_indent = '  '

    # write creator info
    _write_xml_string_to_file(file, _creator_info_xml_string(hash_list.creator_info), '  ')

    # write hashes
    hashes_tag = '<hashes>\n'
    _write_xml_string_to_file(file, hashes_tag, current_indent)
    current_indent += '  '

    for media_hash in hash_list.media_hashes:
        _write_xml_string_to_file(file, _media_hash_xml_string(media_hash), current_indent)

    current_indent = current_indent[:-2]
    _write_xml_string_to_file(file, '</hashes>\n', current_indent)

    # only write the optional references section if there are actually some references
    if len(hash_list.referenced_hash_lists) > 0:
        _write_xml_string_to_file(file, '<references>\n', current_indent)
        current_indent += '  '
        for ref_hash_list in hash_list.referenced_hash_lists:
            _write_xml_string_to_file(file, _ascmhlreference_xml_string(ref_hash_list, file_path), current_indent)
        current_indent = current_indent[:-2]
        _write_xml_string_to_file(file, '</references>\n', current_indent)

    current_indent = current_indent[:-2]
    _write_xml_string_to_file(file, '</hashlist>\n', current_indent)
    file.flush()

    hash_list.file_path = file_path


def _write_xml_string_to_file(file, xml_string: str, indent: str):
    result = textwrap.indent(xml_string, indent)
    file.write(result.encode('utf-8'))


def _media_hash_xml_string(media_hash) -> str:
    """builds and returns one <hash> element for a given MediaHash object"""

    hash_element = E.hash(
        E.path(media_hash.path,
               {'size': str(media_hash.filesize),
                'lastmodificationdate': datetime_isostring(media_hash.last_modification_date)}))

    for hash_entry in media_hash.hash_entries:
        entry_element = E(hash_entry.hash_format)
        entry_element.text = hash_entry.hash_string
        entry_element.attrib['action'] = hash_entry.action
        hash_element.append(entry_element)

    return etree.tostring(hash_element, pretty_print=True, encoding="unicode")


def _ascmhlreference_xml_string(hash_list: MHLHashList, file_path: str) -> str:
    """builds and returns one <hashlistreference> element for a given HashList object"""

    root_path = os.path.dirname(os.path.dirname(file_path))
    hash_element = E.hashlistreference(
        E.path(os.path.relpath(hash_list.file_path, root_path)),
        E.c4(hash_list.generate_reference_hash()))

    return etree.tostring(hash_element, pretty_print=True, encoding="unicode")


def _creator_info_xml_string(creator_info) -> str:
    """builds and returns one <creatorinfo> element for a given creator info instance"""

    info_element = E.creatorinfo(
        E.creationdate(creator_info.creation_date),
        E.hostname(creator_info.host_name),
        E.rootpath(creator_info.root_path),
        E.tool(creator_info.tool.name, version=creator_info.tool.version),
        E.process(creator_info.process.process_type)
    )
    return etree.tostring(info_element, pretty_print=True, encoding="unicode")
