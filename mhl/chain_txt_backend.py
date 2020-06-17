"""
__author__ = "Patrick Renner"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

from . import logger
from .chain import MHLChain, MHLChainGeneration
from .hashlist import MHLHashList
from .hasher import create_filehash
import os


class MHLChainTXTBackend:
	"""class to read a chain.txt file into a MHLChain object
	"""

	chain_filename = "chain.txt"

	@staticmethod
	def parse(filepath):
		"""parsing the chain.txt file and building the MHLChain for the chain member variable"""
		logger.debug(f'parsing \"{os.path.basename(filepath)}\"...')

		chain = MHLChain()
		chain.file_path = filepath

		if not os.path.exists(filepath):
			return chain

		lines = [line.rstrip('\n') for line in open(filepath)]

		for line in lines:
			line = line.rstrip().lstrip()
			if line != "" and not line.startswith("#"):
				generation = MHLChainTXTBackend._generation_from_line_in_chainfile(line)
				if generation is None:
					logger.error("cannot read line")
					continue
				chain.append_generation(generation)

		return chain

	@staticmethod
	def _generation_from_line_in_chainfile(line):
		""" creates a Generation object from a line int the chain file
		"""

		# TODO split by whitespace
		parts = line.split(None)

		if parts is not None and parts.__len__() < 4:
			logger.error("cannot read line \"{line}\"")
			return None

		generation = MHLChainGeneration()
		generation.generation_number = int(parts[0])
		generation.ascmhl_filename = parts[1]
		generation.hashformat = (parts[2])[:-1]
		generation.hash_string = parts[3]

		if parts.__len__() == 6:
			generation.signature_identifier = parts[4]
			generation.signature = parts[5]

		# TODO sanity checks
		return generation


	@staticmethod
	def write_chain(chain: MHLChain, new_hash_list: MHLHashList):
		logger.debug(f'writing \"{os.path.basename(chain.file_path)}\"...')
		MHLChainTXTBackend._append_new_generation_to_file(chain, new_hash_list)

	@staticmethod
	def _line_for_chainfile(chain_generation: MHLChainGeneration):
		"""creates a text line for appending a generation to a chain file
		"""
		result_string = str(chain_generation.generation_number).zfill(4) + " " + \
						chain_generation.ascmhl_filename + " " + \
						chain_generation.hashformat + ": " + \
						chain_generation.hash_string

		return result_string

	@staticmethod
	def _append_new_generation_to_file(chain: MHLChain, hash_list: MHLHashList):
		""" appends an externally created Generation object to the chain file
		"""

		hash_format = 'c4'

		# get a new generation for a hashlist
		generation = MHLChainGeneration()
		generation.generation_number = hash_list.generation_number
		generation.hashformat = hash_format
		generation.hash_string = create_filehash(hash_format, hash_list.file_path)
		generation.ascmhl_filename = hash_list.get_file_name()

		# TODO sanity checks
		# - if generation is already part of self.generations
		# - if generation number is sequential

		# immediately write to file
		logger.debug(f'   appending chain generation for \"{generation.ascmhl_filename}\" to chain file')
		file_path = os.path.join(chain.history.asc_mhl_path, MHLChainTXTBackend.chain_filename)

		with open(file_path, 'a') as file:
			file.write(MHLChainTXTBackend._line_for_chainfile(generation) + "\n")

		# FIXME: check if file could be created

		# …and store here
		# FIXME: only if successfully written to file
		generation.chain = chain
		chain.generations.append(generation)
