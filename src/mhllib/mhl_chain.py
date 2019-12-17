from .mhl_chain_reader import MHLChainReader
from src.util import logger

import os

class MHLChain:

	"""
	class for representing a chain file with its list of generations (one for each ascmhl file)
	managed by the MHLHistory class
	uses MHLChainGeneration for storing information

	model member variables:
	mhl_history -- MHLHistory object for context
	generations -- list of MHLChainGeneration objects

	attribute member variables:
	filepath -- absolute path to chain file

	other member variables:
	file_name -- file name of the chain file
	"""

	# init

	def __init__(self, history):
		self.history = history
		self.filepath = None
		self.generations = list()
			
	@staticmethod
	def chain_with_filepath(filepath, history, context):
		reader = MHLChainReader(filepath, history, context)
		reader.parse()
		return reader.chain
	
	# build
	
	def empty_generation(self):
		hash = MHLChainGeneration(self)
		return hash
	
	def generation_from_line_in_chainfile(self, line):
		""" creates a Generatzion object from a line int the chain file
		"""

		# TODO split by whitespace
		parts = line.split(None)

		if parts is not None and parts.__len__() < 4:
			logger.error("cannot read line \"{line}\"")
			return None

		generation = MHLChainGeneration(self)

		generation.generation_number = int(parts[0])
		generation.ascmhl_filename = parts[1]
		generation.hashformat = (parts[2])[:-1]
		generation.hash_string = parts[3]

		if parts.__len__() == 6:
			generation.signature_identifier = parts[4]
			generation.signature = parts[5]

		# TODO sanity checks

		return generation
	
	def append_generation(self, generation):
		self.generations.append(generation)
	
	# log

	def log(self):
		logger.info("      filename: {0}".format(self.filename))
		for generation in self.generations:
			generation.log()
		

class MHLChainGeneration:

	"""
	class for representing one generation
	managed by a MHLChain object

	model member variables:
	mhl_chain -- MHLChain object for context

	attribute member variables:
	generation_number -- integer, -1 means invalid
	ascmhl_filename --
	hashformat --
	hash_string --

	other member variables:
	"""

	def __init__(self, chain):

		# line string examples:
		# 0001 A002R2EC_2019-10-08_100916_0001.ascmhl SHA1: 9e9302b3d7572868859376f0e5802b87bab3199e
		# 0001 A002R2EC_2019-10-08_100916_0001.ascmhl SHA1: 9e9302b3d7572868859376f0e5802b87bab3199e bob@example.com enE9miWg6gKQQpYYzYzNVdrOrE58jnNbnqBW/J44g9jniMej7tjqhwezWd7PbfE5T+qcNx0VEetVSNiMllgGPLNcI1lw/Io/rS1NgVO13sCHd4BOPXlux2sUBuZWQliP9WFuuomtDulZyQaaSc1AOQ1YjKPuGIDoLlwvS7KXMMg=

		self.generation_number = -1  # integer, -1 means invalid
		self.ascmhl_filename = None
		self.hashformat = None
		self.hash_string = None
		self.signature_identifier = None  # opt, used to find public key
		self.signature = None  # opt, base64 encoded
		self.chain = chain;
		
	def set_values_from_line_in_chainfile(cls, line_string):
		""" sets values from a line int the chain file
		"""

		# TODO split by whitespace
		parts = line_string.split(None)

		if parts is not None and parts.__len__() < 4:
			logger.error("cannot read line \"{line}\"")
			return None

		self.generation_number = int(parts[0])
		self.ascmhl_filename = parts[1]
		self.hashformat = (parts[2])[:-1]
		self.hash_string = parts[3]

		if parts.__len__() == 6:
			self.signature_identifier = parts[4]
			self.signature = parts[5]

		# TODO sanity checks

	
	def log(self):
		action = "*"			# FIXME
		indicator = " "
#		if failed:
#			indicator = "!"
		
		logger.info("{0} {1}: {2} {3}: {4}".format(indicator,
																	   self.hashformat.rjust(6),
																	   self.hash_string.ljust(32),
																	   action.ljust(10),
																	   self.ascmhl_filename))
			

