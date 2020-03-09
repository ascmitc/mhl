"""
__author__ = "Patrick Renner, Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"
__credits__ = ["Jon Waggoner"]

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

class MHLContext:
	"""
	class for wrapping runtime configurations
	"""
	
	def __init__(self):
		self.verbose = False
	
	def load_args(self, **kwargs):
		"""
		sets all context properties based on the values contained in the kwargs.
		intended to be called directly with the arguments and options provided to the cli upon invocation.
		:param kwargs: all arguments/options from the cli passed along as key-word-arguments.
		:return: none
		"""
		self.verbose = kwargs.get('verbose')