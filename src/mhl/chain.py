from src.util import logger
from src.mhl.hash import create_filehash

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

	def _parse_file(self):
		""" reads chain file and builds self.generations list
		"""
		self.generations = []

		lines = [line.rstrip('\n') for line in open(self.filepath)]

		for line in lines:
			line = line.rstrip().lstrip()
			if not line.startswith("#"):
				generation = ChainGeneration.with_line_in_chainfile(line)
				if generation is not None:
					self.generations.append(generation)
				else:
					logger.error("cannot read line")

	# TODO sanity checks
	# - if generation numbers are sequential and complete
	# - check if all files exist

	def verify_all(self):
		"""verifies asc-mhl files of all listed generations in chain file

		result value:
		True - everything ok
		False - verification of one or more generations failed
		"""

		result = True
		for generation in self.generations:
			result = generation.verify_hash()
			if result is False:
				result = False

		return result

	def append_new_generation_to_file(self, generation):
		""" appends an externally created Generation object to the chain file
		"""

		# TODO sanity checks
		# - if generation is already part of self.generations
		# - if generation number is sequential

		# immediately write to file
		logger.info(f'appending chain generation for \"{generation.ascmhl_filename}\" to chain file')

		with open(self.filepath, 'a') as file:
			file.write(generation.line_for_chainfile() + "\n")

		# FIXME: check if file could be created

		# …and store here
		# FIXME: only if successfully written to file
		self.generations.append(generation)

	# FIXME: return success


class ChainGeneration:
	"""class for representing one generation to be managed by a Chain object

	member variables:
	generation_number -- integer, -1 means invalid
	ascmhl_filename --
	hashformat --
	filehash --
	signature_identifier -- opt, used to find public key
	signature -- opt, base64 encoded
	"""

	def __init__(self):

		# line string examples:
		# 0001 A002R2EC_2019-10-08_100916_0001.ascmhl SHA1: 9e9302b3d7572868859376f0e5802b87bab3199e
		# 0001 A002R2EC_2019-10-08_100916_0001.ascmhl SHA1: 9e9302b3d7572868859376f0e5802b87bab3199e bob@example.com enE9miWg6gKQQpYYzYzNVdrOrE58jnNbnqBW/J44g9jniMej7tjqhwezWd7PbfE5T+qcNx0VEetVSNiMllgGPLNcI1lw/Io/rS1NgVO13sCHd4BOPXlux2sUBuZWQliP9WFuuomtDulZyQaaSc1AOQ1YjKPuGIDoLlwvS7KXMMg=

		self.generation_number = -1  # integer, -1 means invalid
		self.ascmhl_filename = None
		self.hashformat = None
		self.filehash = None
		self.signature_identifier = None  # opt, used to find public key
		self.signature = None  # opt, base64 encoded

	@classmethod
	def with_line_in_chainfile(cls, line_string):
		""" creates a Generatzion object from a line int the chain file
		"""

		# TODO split by whitespace
		parts = line_string.split(None)

		if parts is not None and parts.__len__() < 4:
			logger.error("cannot read line \"{line}\"")
			return None

		cls.generation_number = int(parts[0])
		cls.ascmhl_filename = parts[1]
		cls.hashformat = (parts[2])[:-1]
		cls.filehash = parts[3]

		if parts.__len__() == 6:
			cls.signature_identifier = parts[5]
			cls.signature = parts[6]

		# TODO sanity checks

		return cls

	@classmethod
	def with_new_ascmhl_file(cls, generation_number, filepath, hashformat):
		""" hashes ascmhl file and creates new, filled Generation object
		"""

		# TODO check if ascmhl file exists
		generation = cls()

		generation.generation_number = generation_number
		generation.ascmhl_filename = os.path.basename(os.path.normpath(filepath))
		generation.hashformat = hashformat
		generation.filehash = create_filehash(filepath, hashformat)

		return generation

	@classmethod
	def with_new_ascmhl_file_and_signature(cls, generation_number, filepath, hashformat,
										   signature_identifier, private_key_filepath):
		""" hashes ascmhl file, signs it, and creates new, filled Generation object
		"""

		generation = ChainGeneration.with_new_ascmhl_file(generation_number, filepath, hashformat)

		# creating signature for Sidecar.txt
		# $ openssl rsautl -sign -inkey mykey.pem -keyform PEM -in self.filehash > sig.dat
		# $ base64 -i sig.dat -o sig.base64.txt

		generation.signature_identifier = signature_identifier
		# generation.signature = # TODO content of sig.base64.txt file

		return generation

	def is_signed(self):
		return self.signature_identifier is not None and self.signature is not None

	def line_for_chainfile(self):
		"""creates a text line for appending a generation to a chain file
		"""
		result_string = str(self.generation_number).zfill(4) + " " + \
						self.ascmhl_filename + " " + \
						self.hashformat + ": " + \
						self.filehash

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

		return False

		# digest again in order to compare hashes
		# $ openssl dgst -sha1 self.ascmhl_filename

		# return result of hash comparison:
		# return (digest_hash == self.filehash)

	def verify_signature(self, public_key_filepath):
		"""verifies the signature against  available hash

		paramters:
		public_key_filepath - path to pem file with signer's public key (needs to be found via self.signature_identifier)

		result value:
		True - everything ok
		False - verification of signature failed
		"""

		return False

		# verifying (only shows the hash that was signed)
		# $ base64 -D -i sig.base64.txt -o sig.dat
		# $ openssl rsautl -verify -inkey pubkey.pem -pubin -keyform PEM -in sig.dat

		# return result of hash comparison:
		# return (digest_hash == decoded has from signature)
