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

	def __init__(self):
		self.hash_lists = list()
		self.asc_mhl_path = None

	def append_hash_list(self, hash_list):
		hash_list.history = self
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
