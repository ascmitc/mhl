from src.util import logger
from src.util.datetime import datetime_isostring
from .mhl_defines import ascmhl_supported_hashformats
from .mhl_hashlist import MHLHashList, MHLCreatorInfo, MHLMediaHash, MHLHashEntry

import os
from lxml import objectify, etree, sax

class MHLHashListXMLBackend:
	"""class to read an MHL file into a MHLHashList object
	"""

	@staticmethod
	def parse(filepath):
		"""parsing the MHL XML file and building the MHLHashList for the hash_list member variable"""
		logger.info(f'parsing \"{os.path.basename(filepath)}\"...')
		
		tree = etree.parse(filepath)
		hash_list_element = tree.getroot()
		
		hash_list = MHLHashList()

		for section in hash_list_element.getchildren():
			if section.tag == 'creatorinfo':
				creator_info = MHLCreatorInfo()
				creator_info.host_name = section.xpath('hostname')[0].text
				creator_info.tool_name = section.xpath('toolname')[0].text
				creator_info.tool_version = section.xpath('toolversion')[0].text
				creator_info.creation_date = section.xpath('creationdate')[0].text
				creator_info.process = section.xpath('process')[0].text
				hash_list.append_creator_info(creator_info)

			if section.tag == 'hashes':
				hashes = section.getchildren()
				for hash_element in hashes:
					media_hash = MHLMediaHash()
					media_hash.relative_filepath = hash_element.xpath('filename')[0].text

					for hash_format in ascmhl_supported_hashformats:
						hash_entry_elements = hash_element.xpath(hash_format)
						if hash_entry_elements:
							hash_entry_element = hash_entry_elements[0]
							hash_entry = MHLHashEntry()
							hash_entry.hash_format = hash_format
							hash_entry.hash_string = hash_entry_element.text
							hash_entry.action = hash_entry_element.get('action')
							hash_entry.secondary = (hash_entry_element.get('secondary') is True)
							media_hash.append_hash_entry(hash_entry)
							
					hash_list.append_hash(media_hash)
		return hash_list

	@staticmethod
	def write_hash_list(hash_list, file_path):
		xml_context = sax.ElementTreeContentHandler()
		xml_context.startDocument()
		xml_context.startElementNS((None, 'hashlist'), 'hashlist', {(None, 'version'): "2.0"})
		hashlist_element = xml_context._element_stack[-1]

		creatorinfo_element = MHLHashListXMLBackend._creator_info_xml_element(hash_list.creator_info)
		hashlist_element.append(creatorinfo_element)

		# if media_hash_list is not None:
		# 	genreference_element = self.element_genreference(media_hash_list)
		# 	hashlist_element.append(genreference_element)

		xml_context.startElementNS((None, 'hashes'), 'hashes', {(None, 'rootPath'): os.path.dirname(os.path.dirname(file_path))})
		hashes_element = xml_context._element_stack[-1]

		for media_hash in hash_list.media_hashes:
			hash_element = MHLHashListXMLBackend._media_hash_xml_element(media_hash)
			hashes_element.append(hash_element)

		xml_string: bytes = etree.tostring(xml_context.etree.getroot(), pretty_print=True, xml_declaration=True,
												encoding="utf-8")

		if not os.path.isdir(os.path.dirname(file_path)):
			os.mkdir(os.path.dirname(file_path))

		with open(file_path, 'wb') as file:
			# FIXME: check if file could be created
			file.write(xml_string)


	@staticmethod
	def _media_hash_xml_element(media_hash):
		"""builds and returns one <hash> element for a given MediaHash object"""

		hash_element = etree.Element('hash')

		filename_element = etree.SubElement(hash_element, 'filename')
		filename_element.text = media_hash.relative_filepath
		filesize_element = etree.SubElement(hash_element, 'filesize')
		filesize_element.text = media_hash.filesize.__str__()
		lastmodificationdate_element = etree.SubElement(hash_element, 'lastmodificationdate')
		lastmodificationdate_element.text = datetime_isostring(media_hash.last_modification_date)

		for hash_entry in media_hash.hash_entries:
			hashformat_element_attributes = {}
			if hash_entry.action is not None:
				if hash_entry.action != 'copy-only':
					hashformat_element_attributes['action'] = hash_entry.action
			if hash_entry.secondary is not None and hash_entry.secondary is not False:
				hashformat_element_attributes['secondary'] = "true" if hash_entry.secondary else None
			hashformat_element = etree.SubElement(hash_element, hash_entry.hash_format,
												  attrib=hashformat_element_attributes)
			hashformat_element.text = hash_entry.hash_string

		objectify.deannotate(hash_element, cleanup_namespaces=True, xsi_nil=True)
		return hash_element

	@staticmethod
	def _creator_info_xml_element(creator_info):
		"""builds and returns one <creatorinfo> element for a given creator info instance"""

		info_element = objectify.Element('creatorinfo')
		info_element.hostname = creator_info.host_name
		info_element.toolname = creator_info.tool_name
		info_element.toolversion = creator_info.tool_version
		info_element.creationdate = creator_info.creation_date
		info_element.process = 'verify'
		objectify.deannotate(info_element, cleanup_namespaces=True, xsi_nil=True)
		return info_element
