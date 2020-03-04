from src.util import logger
from .mhl_chain import MHLChain
from .mhl_history import MHLHistory

import os

class MHLChainTXTBackend:
	"""class to read a chain.txt file into a MHLChain object
	"""

	@staticmethod
	def parse(filepath):
		"""parsing the chain.txt file and building the MHLChain for the chain member variable"""
		logger.info(f'parsing \"{os.path.basename(filepath)}\"... TBI')		#FIXME

		chain = MHLChain()
		chain.file_path = filepath

		return chain

	@staticmethod
	def write_chain(chain: MHLChain):
		logger.info(f'writing \"{os.path.basename(chain.file_path)}\"... TBI') 	#FIXME

