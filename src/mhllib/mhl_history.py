from .mhl_hashlist import MHLHashList
from .mhl_chain import MHLChain

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

	def empty_hashlist(self):
		hashlist = MHLHashList(self)
		return hashlist

	def empty_chain(self):
		chain = MHLChain(self)
		return chain

	
	# accessors

	def generation_number_for_filename(self, filename):
		return 9999		# FIXME