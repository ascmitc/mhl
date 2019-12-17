from src.util import logger

import os

class MHLChainReader:
	
	def __init__(self, filepath, history, context):
		self.filepath = filepath
		self.chain = None
		self.history = history
		self.context = context
		
	def filename(self):
		return os.path.relpath(self.filepath,
							   start=os.path.dirname(self.filepath))
	
	def parse(self):
		"""parsing the chain file """
		logger.info(f'parsing \"{os.path.basename(self.filepath)}\"...')
		
		self.chain = self.history.empty_chain()
		self.chain.filename = self.filename()

		lines = [line.rstrip('\n') for line in open(self.filepath)]

		for line in lines:
			line = line.rstrip().lstrip()
			if line != "" and not line.startswith("#"):
				generation = self.chain.generation_from_line_in_chainfile(line)

				if generation is not None:
					generation.chain = self
					self.chain.append_generation(generation)
				else:
					logger.error("cannot read line")