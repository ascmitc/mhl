from .mhl_hashlist import MHLHashList
from .mhl_chain import MHLChain
from src.util import logger
import os


class MHLHistory:
	"""
	class for representing an entire MHL history

	- public interface
		* intitialized with a root path containting an MHL folder with MHL files
		* accessing derived information (e.g. earliest hash for file)

	- private interface
		* initialize new, empty MHLHashList for adding files/hashes, define path and filename for new MHLHashList

	model member variables:
	hashlists -- list of MHLHashList (one for each generation / MHL file)

	attribute member variables:

	other member variables:
	root_path -- path where the mhl folder resides
	"""

	def __init__(self, asc_mhl_path=None):
		self.hash_lists = list()
		self.asc_mhl_path = asc_mhl_path

	def empty_hashlist(self):
		hash_list = MHLHashList(self)
		return hash_list

	def empty_chain(self):
		chain = MHLChain(self)
		return chain

	def append_hash_list(self, hash_list):
		self.hash_lists.append(hash_list)

	
	# accessors

	def generation_number_for_filename(self, filename):
		return 9999		# FIXME

	def log(self):
		logger.info("mhl history")
		logger.info("asc_mhl path: {0}".format(self.asc_mhl_path))

		for hash_list in self.hash_lists:
			logger.info("")
			hash_list.log()
