"""
__author__ = "Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""
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
    """parsing the MHL XML file and building the MHLHashList for the hash_list member variable"""
    logger.debug(f"parsing {file_path}...")

    start = timer()

    hash_list = MHLHashList()
    hash_list.file_path = file_path
    object_stack = []
    current_object = None
    is_directory_structure = False

    # use iterparse to prevent large memory usage when parsing large files
    # pass a file handle to iterparse instead of the path directly to support the fake filesystem used in the tests
    file = open(file_path, "rb")
    existing_ignore_patterns = []
    for event, element in etree.iterparse(file, events=("start", "end")):

        # check if we need to create a new container
        if event == "start":
            # the tag might contain the namespace like {urn:ASC:MHL:v2.0}hash, so we need to strip the namespace part
            # doing it with split is faster than using the lxml QName method
            tag = element.tag.split("}", 1)[-1]

            if not current_object:
                if tag == "creatorinfo":
                    current_object = MHLCreatorInfo()
                elif tag == "processinfo":
                    current_object = MHLProcessInfo()
                elif tag == "hash":
                    current_object = MHLMediaHash()
                elif tag == "directoryhash":
                    current_object = MHLMediaHash()
                    current_object.is_directory = True
                elif tag == "hashlistreference":
                    current_object = MHLHashListReference()

            # these are the only cases where we push to the object stack
            if type(current_object) is MHLProcessInfo:
                if tag == "ignore":
                    object_stack.append(current_object)
                    current_object = MHLIgnoreSpec()
                elif tag == "roothash":
                    object_stack.append(current_object)
                    current_object = MHLMediaHash()
                    current_object.is_directory = True

            # take a note where we are ina <directoryhash>
            elif type(current_object) is MHLMediaHash:
                if tag == "structure":
                    is_directory_structure = True
                elif tag == "content":
                    is_directory_structure = False

        elif event == "end":

            if current_object:
                tag = element.tag.split("}", 1)[-1]

                if type(current_object) is MHLCreatorInfo:
                    if tag == "creationdate":
                        current_object.creation_date = element.text
                    elif tag == "tool":
                        current_object.tool = MHLTool(element.text, element.attrib["version"])
                    elif tag == "hostname":
                        current_object.host_name = element.text
                    elif tag == "creatorinfo":
                        hash_list.creator_info = current_object
                        current_object = None
                    # TODO: missing location, comment

                elif type(current_object) is MHLProcessInfo:
                    if tag == "process":
                        current_object.process = element.text
                    elif tag == "processinfo":
                        hash_list.process_info = current_object
                        current_object = None
                elif type(current_object) is MHLIgnoreSpec:
                    if tag == "pattern":
                        existing_ignore_patterns.append(element.text)
                    elif tag == "ignore":
                        hash_list.process_info.ignore_spec = current_object
                        current_object = object_stack.pop()
                    else:
                        current_object = None

                elif type(current_object) is MHLMediaHash:
                    if tag == "path":
                        current_object.path = element.text
                        file_size = element.attrib.get("size")
                        current_object.file_size = int(file_size) if file_size else None
                    # TODO: parse date
                    # elif tag == 'lastmodificationdate':
                    # 	current_object.file_size = element.text
                    elif tag in ascmhl_supported_hashformats:
                        hash_date = None
                        hash_date_string = element.attrib.get("hashdate")
                        if hash_date_string is not None:
                            hash_date = dateutil.parser.parse(hash_date_string)
                        if current_object.is_directory:
                            if is_directory_structure == False:
                                entry = MHLHashEntry(tag, element.text, element.attrib.get("action"), hash_date)
                                current_object.append_hash_entry(entry)
                            else:
                                # find right hash entry and set structure hash
                                entry = current_object.find_hash_entry_for_format(tag)
                                entry.structure_hash_string = element.text
                        else:
                            entry = MHLHashEntry(tag, element.text, element.attrib.get("action"), hash_date)
                            current_object.append_hash_entry(entry)

                    elif tag == "hash" or tag == "directoryhash":
                        hash_list.append_hash(current_object)
                        current_object = None

                    elif tag == "roothash":
                        root_media_hash = current_object
                        root_media_hash.is_directory = True
                        current_object = object_stack.pop()
                        current_object.root_media_hash = root_media_hash

                elif type(current_object) is MHLHashListReference:
                    if tag == "path":
                        current_object.path = element.text
                    elif tag == "c4":
                        current_object.reference_hash = element.text
                    elif tag == "hashlistreference":
                        hash_list.append_hash_list_reference(current_object)
                        current_object = None

            # in order to keep memory usage low while parsing, we clear the finished element
            # and remove it from the parent element as well but since this is clearing the children anyways
            # we only need to do it if we are not currently parsing a container object
            if not current_object:
                element.clear()
                while element.getprevious() is not None:
                    del element.getparent()[0]

    hash_list.process_info.ignore_spec = MHLIgnoreSpec(existing_ignore_patterns)
    logger.debug(f"parsing took: {timer() - start}")

    return hash_list


def write_hash_list(hash_list: MHLHashList, file_path: str):
    """creates a new mhl file and writes the xml to disk

    we write the file step by step to reduce memory load while writing large files
    e.g. we create xml objects only for single elemnts like one media hash element and write it to disk
    before creating the next one"""

    directory_path = os.path.dirname(file_path)
    if not os.path.isdir(directory_path):
        os.mkdir(directory_path)

    file = open(file_path, "wb")
    file.write(b'<?xml version="1.0" encoding="UTF-8"?>\n<hashlist version="2.0" xmlns="urn:ASC:MHL:v2.0">\n')
    current_indent = "  "

    # set the file name early so we can use it to e.g. get the root path
    hash_list.file_path = file_path
    # write creator info
    _write_xml_element_to_file(file, _creator_info_xml_element(hash_list), "  ")
    # write process info
    _write_xml_element_to_file(file, _process_info_xml_element(hash_list), "  ")

    # write hashes
    hashes_tag = "<hashes>\n"
    _write_xml_string_to_file(file, hashes_tag, current_indent)
    current_indent += "  "

    for media_hash in hash_list.media_hashes:
        if media_hash.is_directory:
            _write_xml_element_to_file(file, _directory_hash_xml_element(media_hash), current_indent)
        else:
            _write_xml_element_to_file(file, _media_hash_xml_element(media_hash), current_indent)

    current_indent = current_indent[:-2]
    _write_xml_string_to_file(file, "</hashes>\n", current_indent)

    # only write the optional references section if there are actually some references
    if len(hash_list.referenced_hash_lists) > 0:
        _write_xml_string_to_file(file, "<references>\n", current_indent)
        current_indent += "  "
        for ref_hash_list in hash_list.referenced_hash_lists:
            _write_xml_element_to_file(file, _ascmhlreference_xml_element(ref_hash_list, file_path), current_indent)
        current_indent = current_indent[:-2]
        _write_xml_string_to_file(file, "</references>\n", current_indent)

    current_indent = current_indent[:-2]
    _write_xml_string_to_file(file, "</hashlist>\n", current_indent)
    file.flush()


def _write_xml_element_to_file(file, xml_element, indent: str):
    xml_string = etree.tostring(xml_element, pretty_print=True, encoding="unicode")
    _write_xml_string_to_file(file, xml_string, indent)


def _write_xml_string_to_file(file, xml_string: str, indent: str):
    result = textwrap.indent(xml_string, indent)
    file.write(result.encode("utf-8"))


def _media_hash_xml_element(media_hash: MHLMediaHash):
    """builds and returns one <hash> element for a given MediaHash object"""

    path_element = E.path(media_hash.path)
    if media_hash.file_size:
        path_element.attrib["size"] = str(media_hash.file_size)
    if media_hash.last_modification_date:
        path_element.attrib["lastmodificationdate"] = datetime_isostring(media_hash.last_modification_date)

    hash_element = E.hash(path_element)
    for hash_entry in media_hash.hash_entries:
        entry_element = E(hash_entry.hash_format)
        entry_element.text = hash_entry.hash_string
        if hash_entry.action:
            entry_element.attrib["action"] = hash_entry.action
        if hash_entry.hash_date:
            entry_element.attrib["hashdate"] = datetime_isostring(hash_entry.hash_date, True)
        hash_element.append(entry_element)

    return hash_element


def _directory_hash_xml_element(media_hash: MHLMediaHash, skipPath=False):
    """builds and returns one <hash> element for a given MediaHash object"""

    content_element = E.content()
    structure_element = E.structure()

    for hash_entry in media_hash.hash_entries:
        entry_element_content = E(hash_entry.hash_format)
        entry_element_content.text = hash_entry.hash_string

        entry_element_structure = E(hash_entry.hash_format)
        entry_element_structure.text = hash_entry.structure_hash_string

        if hash_entry.action:
            entry_element_content.attrib["action"] = hash_entry.action
            entry_element_structure.attrib["action"] = hash_entry.action
        if hash_entry.hash_date:
            entry_element_content.attrib["hashdate"] = datetime_isostring(hash_entry.hash_date, True)
            entry_element_structure.attrib["hashdate"] = datetime_isostring(hash_entry.hash_date, True)

        content_element.append(entry_element_content)
        structure_element.append(entry_element_structure)

    hash_element = E.directoryhash()

    if skipPath == False:
        path_element = E.path(media_hash.path)
        if media_hash.file_size:
            path_element.attrib["size"] = str(media_hash.file_size)
        if media_hash.last_modification_date:
            path_element.attrib["lastmodificationdate"] = datetime_isostring(media_hash.last_modification_date)
        hash_element.append(path_element)

    hash_element.append(content_element)
    hash_element.append(structure_element)

    return hash_element


def _ascmhlreference_xml_element(hash_list: MHLHashList, file_path: str):
    """builds and returns one <hashlistreference> element for a given HashList object"""

    root_path = os.path.dirname(os.path.dirname(file_path))
    hash_element = E.hashlistreference(
        E.path(os.path.relpath(hash_list.file_path, root_path)),
        E.c4(hash_list.generate_reference_hash()),
    )

    return hash_element


def _creator_info_xml_element(hash_list: MHLHashList):
    """builds and returns one <creatorinfo> element for a given creator info instance"""
    creator_info = hash_list.creator_info
    info_element = E.creatorinfo(
        E.creationdate(creator_info.creation_date),
        E.hostname(creator_info.host_name),
        E.tool(creator_info.tool.name, version=creator_info.tool.version),
    )
    # TODO: missing location, comment, ignore
    return info_element


def _process_info_xml_element(hash_list: MHLHashList):
    """builds and returns one <creatorinfo> element for a given creator info instance"""
    process_info = hash_list.process_info
    # create empty root hash if directory hashes are disabled or use the generated one from the hash list
    root_hash = hash_list.process_info.root_media_hash
    if not root_hash:
        root_hash = MHLMediaHash()
        root_hash.path = hash_list.get_root_path()
    if root_hash.path == ".":  # TODO: can we find out if this is a non-flattened history further up?
        root_hash.path = hash_list.get_root_path()

    info_element = E.processinfo(
        E.process(process_info.process.process_type),
        _root_media_hash_xml_element(root_hash),
        _ignorespec_xml_element(hash_list.process_info.ignore_spec),
    )
    return info_element


def _ignorespec_xml_element(ignore_spec: MHLIgnoreSpec):
    spec_element = E.ignore()
    if ignore_spec:
        for ignore_pattern in ignore_spec.get_pattern_list():
            spec_element.append(E.pattern(ignore_pattern))
    return spec_element


def _ignore_xml_element(ignore_pattern: str):
    """builds and returns one <ignore> element for a given ignore_spec pattern entry"""
    return E.ignore(ignore_pattern)


def _root_media_hash_xml_element(root_media_hash: MHLMediaHash):
    element = _directory_hash_xml_element(root_media_hash, skipPath=True)
    element.tag = "roothash"
    return element
