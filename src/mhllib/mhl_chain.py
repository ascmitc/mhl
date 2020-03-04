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
	file path -- absolute path to chain file
	"""

	# init

	def __init__(self):
		self.history = None
		self.file_path = None
		self.filepath = None
		self.generations = list()

	# build
	
	def append_generation(self, generation):
		generation.chain = self
		self.generations.append(generation)
	
	# log

	def log(self):
		logger.info("      filepath: {0}".format(self.filepath))
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

	def __init__(self):

		# line string examples:
		# 0001 A002R2EC_2019-10-08_100916_0001.ascmhl SHA1: 9e9302b3d7572868859376f0e5802b87bab3199e
		# 0001 A002R2EC_2019-10-08_100916_0001.ascmhl SHA1: 9e9302b3d7572868859376f0e5802b87bab3199e bob@example.com enE9miWg6gKQQpYYzYzNVdrOrE58jnNbnqBW/J44g9jniMej7tjqhwezWd7PbfE5T+qcNx0VEetVSNiMllgGPLNcI1lw/Io/rS1NgVO13sCHd4BOPXlux2sUBuZWQliP9WFuuomtDulZyQaaSc1AOQ1YjKPuGIDoLlwvS7KXMMg=

		self.generation_number = None  # integer, -1 means invalid
		self.ascmhl_filename = None
		self.hashformat = None
		self.hash_string = None
		self.signature_identifier = None  # opt, used to find public key
		self.signature = None  # opt, base64 encoded
		self.chain = None

	
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
			

