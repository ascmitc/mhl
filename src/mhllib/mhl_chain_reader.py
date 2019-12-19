from src.util import logger
from .mhl_chain import MHLChain, MHLChainGeneration
import os

class MHLChainReader:

	@staticmethod
	def parse(filepath):
		"""parsing the chain file """
		logger.info(f'parsing \"{os.path.basename(filepath)}\"...')
		
		chain = MHLChain()
		chain.filepath = filepath
		lines = [line.rstrip('\n') for line in open(filepath)]

		for line in lines:
			line = line.rstrip().lstrip()
			if line != "" and not line.startswith("#"):
				generation = MHLChainReader._generation_from_line_in_chainfile(line)
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
