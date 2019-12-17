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