"""
__author__ = "Patrick Renner, Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"
__credits__ = ["Jon Waggoner"]

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""


from . import logger


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


class MHLCreatorInfo:

	# init

	def __init__(self):
		self.hash_list = None
		self.host_name = None
		self.tool_name = None
		self.tool_version = None
		self.creation_date = None
		self.process = None

	# log

	def log(self):
		logger.info("     host_name: {0}".format(self.host_name))
		logger.info("     tool_name: {0}".format(self.tool_name))
		logger.info("  tool_version: {0}".format(self.tool_version))
		logger.info(" creation_date: {0}".format(self.creation_date))
		logger.info("       process: {0}".format(self.process))