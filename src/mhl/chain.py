from src.util import logger
from src.mhl.hash import create_filehash
from src.mhl.hash import sign_hash, check_signature

import os


class Chain:
	"""class for representing a chain file with its list of generations (one for each ascmhl file)
	also uses ChainGeneration for storing information

	member variables:
	filepath -- absolute path to chain file
	generations -- list of ChainGeneration objects
	"""

	def __init__(self, filepath):
		self.filepath = filepath
		self.generations = []

		if os.path.isfile(self.filepath):
			self._parse_file()

	def ascmhl_folder_path(self):
		"""absolute path of the enclosing asc-mhl folder"""
		path = os.path.dirname(self.filepath)
		return path

	def _parse_file(self):
		""" reads chain file and builds self.generations list
		"""
		self.generations = []

		lines = [line.rstrip('\n') for line in open(self.filepath)]

		for line in lines:
			line = line.rstrip().lstrip()
			if line != "" and not line.startswith("#"):
				generation = ChainGeneration.with_line_in_chainfile(line)
				if generation is not None:
					generation.chain = self
					self.generations.append(generation)
				else:
					logger.error("cannot read line")

	def generation_with_generation_number(self, number):

		for generation in self.generations:
			if generation.generation_number == number:
				return generation
		return None

	# TODO sanity checks
	# - if generation numbers are sequential and complete
	# - check if all files exist

	def verify_all(self):
		"""verifies asc-mhl files of all listed generations in chain file

		result value:
		0 - everything ok
		>0 - number of verification failures
		"""

		logger.info(f'verifying chain {self.filepath}')
		number_of_failures = 0
		for generation in self.generations:
			result = generation.verify_hash()
			if result is False:
				number_of_failures = number_of_failures + 1

		return number_of_failures

	def append_new_generation_to_file(self, generation):
		""" appends an externally created Generation object to the chain file
		"""

		# TODO sanity checks
		# - if generation is already part of self.generations
		# - if generation number is sequential

		# immediately write to file
		if generation.is_signed():
			logger.info(
				f'appending chain generation for \"{generation.ascmhl_filename}\" with signature for '
				f'{generation.signature_identifier} to chain file')
		else:
			logger.info(
				f'appending chain generation for \"{generation.ascmhl_filename}\" to chain file')

		with open(self.filepath, 'a') as file:
			file.write(generation.line_for_chainfile() + "\n")

		# FIXME: check if file could be created

		# …and store here
		# FIXME: only if successfully written to file
		generation.chain = self
		self.generations.append(generation)

	# FIXME: return success


class ChainGeneration:
	"""class for representing one generation to be managed by a Chain object

	member variables:
	generation_number -- integer, -1 means invalid
	ascmhl_filename --
	hashformat --
	hash_string --
	signature_identifier -- opt, used to find public key
	signature -- opt, base64 encoded
	chain -- needed for absolute path resolution
	"""

	def __init__(self):

		# line string examples:
		# 0001 A002R2EC_2019-10-08_100916_0001.ascmhl SHA1: 9e9302b3d7572868859376f0e5802b87bab3199e
		# 0001 A002R2EC_2019-10-08_100916_0001.ascmhl SHA1: 9e9302b3d7572868859376f0e5802b87bab3199e bob@example.com enE9miWg6gKQQpYYzYzNVdrOrE58jnNbnqBW/J44g9jniMej7tjqhwezWd7PbfE5T+qcNx0VEetVSNiMllgGPLNcI1lw/Io/rS1NgVO13sCHd4BOPXlux2sUBuZWQliP9WFuuomtDulZyQaaSc1AOQ1YjKPuGIDoLlwvS7KXMMg=

		self.generation_number = -1  # integer, -1 means invalid
		self.ascmhl_filename = None
		self.hashformat = None
		self.hash_string = None
		self.signature_identifier = None  # opt, used to find public key
		self.signature = None  # opt, base64 encoded
		self.chain = None;

	@classmethod
	def with_line_in_chainfile(cls, line_string):
		""" creates a Generatzion object from a line int the chain file
		"""

		# TODO split by whitespace
		parts = line_string.split(None)

		if parts is not None and parts.__len__() < 4:
			logger.error("cannot read line \"{line}\"")
			return None

		generation = cls()

		generation.generation_number = int(parts[0])
		generation.ascmhl_filename = parts[1]
		generation.hashformat = (parts[2])[:-1]
		generation.hash_string = parts[3]

		if parts.__len__() == 6:
			generation.signature_identifier = parts[4]
			generation.signature = parts[5]

		# TODO sanity checks

		return generation

	@classmethod
	def with_new_ascmhl_file(cls, generation_number, filepath, hashformat):
		""" hashes ascmhl file and creates new, filled Generation object
		"""

		# TODO check if ascmhl file exists

		generation = cls()

		generation.generation_number = generation_number
		generation.ascmhl_filename = os.path.basename(os.path.normpath(filepath))
		generation.hashformat = hashformat

		# TODO somehow pass in xxattr flag from context ?
		generation.hash_string = create_filehash(filepath, hashformat)

		return generation

	@classmethod
	def with_new_ascmhl_file_and_signature(cls, generation_number, filepath, hashformat,
										   signature_identifier, private_key_filepath):
		""" hashes ascmhl file, signs it, and creates new, filled Generation object
		"""

		generation = ChainGeneration.with_new_ascmhl_file(generation_number, filepath, hashformat)

		signature_string = sign_hash(generation.hash_string, private_key_filepath)

		generation.signature_identifier = signature_identifier
		generation.signature = signature_string

		return generation

	def is_signed(self):
		return self.signature_identifier is not None and self.signature is not None

	def line_for_chainfile(self):
		"""creates a text line for appending a generation to a chain file
		"""
		result_string = str(self.generation_number).zfill(4) + " " + \
						self.ascmhl_filename + " " + \
						self.hashformat + ": " + \
						self.hash_string

		if self.is_signed():
			result_string = result_string + " " + self.signature_identifier + " " + self.signature

		return result_string

	def verify(self, public_key_filepath=None):
		"""verifies hash and signature (if available) of generation

		paramters:
		public_key_filepath - path to pem file with signer's public key (needs to be found via self.signature_identifier)

		result value:
		True - everything ok
		False - verification of hash or signature failed
		"""

		result = self.verify_hash()

		if result is False:
			return False

		if self.is_signed():
			if public_key_filepath is None:
				logger.error("public key needed for verifying signature of generation {self.generation_number}")
				result = False
			else:
				result = self.verify_signature(public_key_filepath)

		return result

	def verify_hash(self):
		"""verifies the asc-mhl file of a generation against available hash

		result value:
		True - everything ok
		False - verification failed
		"""

		ascmhl_file_path = os.path.join(self.chain.ascmhl_folder_path(), self.ascmhl_filename)

		# TODO somehow pass in xxattr flag from context ?
		current_filehash = create_filehash(ascmhl_file_path , self.hashformat)

		if current_filehash != self.hash_string:
			logger.error(f'hash mismatch for {self.ascmhl_filename} '
						 f'old {self.hashformat}: {self.hash_string}, '
						 f'new {self.hashformat}: {current_filehash}')
			self.log_chain_generation(True, 'failed')
			return False
		else:
			self.log_chain_generation(False, 'verified')
			return True

		# digest again in order to compare hashes
		# $ openssl dgst -sha1 self.ascmhl_filename

		# return result of hash comparison:
		# return (digest_hash == self.hash_string)

	def verify_signature(self, public_key_filepath):
		"""verifies the signature against  available hash

		paramters:
		public_key_filepath - path to pem file with signer's public key (needs to be found via self.signature_identifier)

		result value:
		True - everything ok
		False - verification of signature failed
		"""

		signature_hash = check_signature(self.signature, public_key_filepath)

		# return result of hash comparison:
		if signature_hash != self.hash_string:
			logger.error(f'signature verification failed for {self.ascmhl_filename} with '
						 f'public key at {public_key_filepath}')
			self.log_chain_generation(True, 'sign error')
			return False
		else:
			self.log_chain_generation(False, 'verified')
			return True


	def log_chain_generation(self, failed, action):
		indicator = " "
		if failed:
			indicator = "!"

		if self.is_signed():
			logger.info("{0} {1}: {2} {3}: {4} (signed by {5})".format(indicator,
																	   self.hashformat.rjust(6),
																	   self.hash_string.ljust(32),
																	   action.ljust(10),
																	   self.ascmhl_filename,
																	   self.signature_identifier))
		else:
			logger.info("{0} {1}: {2} {3}: {4}".format(indicator,
													   self.hashformat.rjust(6),
													   self.hash_string.ljust(32),
													   action.ljust(10),
													   self.ascmhl_filename))