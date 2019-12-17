from src.util import logger
from .mhl_defines import ascmhl_supported_hashformats

import os
from lxml import objectify, etree, sax

class MHLHashListReader:
	"""class to read an MHL file into a MHLHashList object

	member variables:
	filepath -- path to MHL file
	hash_list -- MHLHashList object representing the MHL file
	generation_number -- generation number of the MHL file
	"""
	
	def __init__(self, filepath, history, context):
		self.filepath = filepath
		self.hashlist = None
		self.generation_number = history.generation_number_for_filename(self.filename())
		self.history = history
		self.context = context
		
	def filename(self):
		return os.path.relpath(self.filepath,
							   start=os.path.dirname(self.filepath))
		
	def parse(self):
		"""parsing the MHL XML file and building the MHLHashList for the hash_list member variable"""
		logger.info(f'parsing \"{os.path.basename(self.filepath)}\"...')
		
		tree = etree.parse(self.filepath)
		hashlist_element = tree.getroot()
		
		self.hashlist = self.history.empty_hashlist()
		self.hashlist.generation_number = self.generation_number
		self.hashlist.filename = self.filename()

		for section in hashlist_element.getchildren():
			if section.tag == 'creatorinfo':
				hostname = section.xpath('hostname')[0].text
				toolname = section.xpath('toolname')[0].text
				toolversion = section.xpath('toolversion')[0].text
				creationdate = section.xpath('creationdate')[0].text
				process = section.xpath('process')[0].text
			
				self.hashlist.creatorinfo.hostname = hostname
				self.hashlist.creatorinfo.toolname = toolname
				self.hashlist.creatorinfo.toolversion = toolversion
				self.hashlist.creatorinfo.creationdate = creationdate
				self.hashlist.creatorinfo.process = process

			if section.tag == 'hashes':

				hashes = section.getchildren()
				for hash_element in hashes:
					relative_filepath = hash_element.xpath('filename')[0].text
					
					mediahash = self.hashlist.empty_hash()
					mediahash.relative_filepath = relative_filepath

					for hashformat in ascmhl_supported_hashformats:
						hashentry_element = hash_element.xpath(hashformat)
						if hashentry_element :
							hash_string = hash_element.xpath(hashformat)[0].text
							hashentry = mediahash.empty_hashentry()
							hashentry.hash_string = hash_string
							hashentry.hashformat = hashformat
							mediahash.append_hashentry(hashentry)
							
					self.hashlist.append_hash(mediahash)

#					if self.context.verbose:
#						mediahash.log()
			

						