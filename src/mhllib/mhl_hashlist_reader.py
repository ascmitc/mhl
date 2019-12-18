from src.util import logger
from .mhl_defines import ascmhl_supported_hashformats
from .mhl_hashlist import MHLHashList, MHLCreatorInfo, MHLMediaHash, MHLHashEntry

import os
from lxml import objectify, etree, sax

class MHLHashListReader:
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
						hash_entry_element = hash_element.xpath(hash_format)
						if hash_entry_element:
							hash_entry = MHLHashEntry()
							hash_entry.hash_format = hash_format
							hash_entry.hash_string = hash_element.xpath(hash_format)[0].text
							media_hash.append_hash_entry(hash_entry)
							
					hash_list.append_hash(media_hash)
		return hash_list
