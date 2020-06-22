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
    object_stack = []
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
                elif tag == 'creatorinfo':
                    hash_list.creator_info = current_object
                    current_object = None
            elif type(current_object) is MHLMediaHash:
                if tag == 'path':
                    current_object.path = element.text
                    file_size = element.attrib.get('size')
                    current_object.filesize = int(file_size) if file_size else None
                # TODO: parse date
                # elif tag == 'lastmodificationdate':
                # 	current_object.filesize = element.text
                elif tag in supported_hash_formats:
                    entry = MHLHashEntry(tag, element.text, element.attrib.get('action'))
                    current_object.append_hash_entry(entry)
                elif tag == 'hash':
                    if element.attrib.get('directory') == 'true':
                        current_object.is_directory = True
                    hash_list.append_hash(current_object)
                    current_object = None
                elif tag == 'root':
                    root_media_hash = current_object
                    root_media_hash.is_directory = True
                    current_object = object_stack.pop()
                    hash_list.root_media_hash = root_media_hash
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
        elif type(current_object) is MHLCreatorInfo and event == 'start':
            # remove namespace here again instead of outside of the if
            # since we don't want to do it for tags we don't compare at all
            tag = element.tag.split('}', 1)[-1]
            if tag == 'root':
                object_stack.append(current_object)
                current_object = MHLMediaHash()

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

    # set the file name early so we can use it to e.g. get the root path
    hash_list.file_path = file_path
    # write creator info
    _write_xml_element_to_file(file, _creator_info_xml_element(hash_list), '  ')

    # write hashes
    hashes_tag = '<hashes>\n'
    _write_xml_string_to_file(file, hashes_tag, current_indent)
    current_indent += '  '

    for media_hash in hash_list.media_hashes:
        _write_xml_element_to_file(file, _media_hash_xml_element(media_hash), current_indent)

    current_indent = current_indent[:-2]
    _write_xml_string_to_file(file, '</hashes>\n', current_indent)

    # only write the optional references section if there are actually some references
    if len(hash_list.referenced_hash_lists) > 0:
        _write_xml_string_to_file(file, '<references>\n', current_indent)
        current_indent += '  '
        for ref_hash_list in hash_list.referenced_hash_lists:
            _write_xml_element_to_file(file, _ascmhlreference_xml_element(ref_hash_list, file_path), current_indent)
        current_indent = current_indent[:-2]
        _write_xml_string_to_file(file, '</references>\n', current_indent)

    current_indent = current_indent[:-2]
    _write_xml_string_to_file(file, '</hashlist>\n', current_indent)
    file.flush()


def _write_xml_element_to_file(file, xml_element, indent: str):
    xml_string = etree.tostring(xml_element, pretty_print=True, encoding="unicode")
    _write_xml_string_to_file(file, xml_string, indent)


def _write_xml_string_to_file(file, xml_string: str, indent: str):
    result = textwrap.indent(xml_string, indent)
    file.write(result.encode('utf-8'))


def _media_hash_xml_element(media_hash):
    """builds and returns one <hash> element for a given MediaHash object"""

    path_element = E.path(media_hash.path)
    if media_hash.filesize:
        path_element.attrib['size'] = str(media_hash.filesize)
    if media_hash.last_modification_date:
        path_element.attrib['lastmodificationdate'] = datetime_isostring(media_hash.last_modification_date)

    hash_element = E.hash(path_element)
    if media_hash.is_directory:
        hash_element.attrib['directory'] = 'true'

    for hash_entry in media_hash.hash_entries:
        entry_element = E(hash_entry.hash_format)
        entry_element.text = hash_entry.hash_string
        if hash_entry.action:
            entry_element.attrib['action'] = hash_entry.action
        hash_element.append(entry_element)

    return hash_element


def _ascmhlreference_xml_element(hash_list: MHLHashList, file_path: str):
    """builds and returns one <hashlistreference> element for a given HashList object"""

    root_path = os.path.dirname(os.path.dirname(file_path))
    hash_element = E.hashlistreference(
        E.path(os.path.relpath(hash_list.file_path, root_path)),
        E.c4(hash_list.generate_reference_hash()))

    return hash_element


def _creator_info_xml_element(hash_list: MHLHashList):
    """builds and returns one <creatorinfo> element for a given creator info instance"""
    creator_info = hash_list.creator_info
    # create empty root hash if directory hashes are disabled or use the generated one from the hash list
    root_hash = hash_list.root_media_hash
    if not root_hash:
        root_hash = MHLMediaHash()
    root_hash.path = hash_list.get_root_path()

    info_element = E.creatorinfo(
        E.creationdate(creator_info.creation_date),
        E.hostname(creator_info.host_name),
        _root_media_hash_xml_element(root_hash),
        E.tool(creator_info.tool.name, version=creator_info.tool.version),
        E.process(creator_info.process.process_type)
    )
    return info_element

def _root_media_hash_xml_element(root_media_hash: MHLMediaHash):
    element = _media_hash_xml_element(root_media_hash)
    element.tag = 'root'
    return element