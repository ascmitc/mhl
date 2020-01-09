import os
import re
from src.mhllib import mhl_defines
from src.mhllib.mhl_history import MHLHistory
from src.mhllib.mhl_hashlist_xml_backend import MHLHashListXMLBackend
from src.mhllib.mhl_defines import ascmhl_folder_name
from src.util import logger
from src.util.datetime import datetime_now_filename_string

class MHLHistoryXMLBackend:
	"""
	class for reading an asc-mhl folder with MHL files

	lots of helper functions

	member variables:
	folderpath -- path to the enclosing folder (not the asc-mhl folder itself, but one up)
	"""
	@staticmethod
	def parse(root_path):
		"""finds all MHL files in the asc-mhl folder, returns the mhl_history instance with all mhl_hashlists """

		asc_mhl_folder_path = os.path.join(root_path, ascmhl_folder_name)
		history = MHLHistory()
		history.asc_mhl_path = asc_mhl_folder_path
		hash_lists = []
		for root, directories, filenames in os.walk(asc_mhl_folder_path):
			for filename in filenames:
				if filename.endswith(mhl_defines.ascmhl_file_extension):
					# A002R2EC_2019-06-21_082301_0005.ascmhl
					parts = re.findall(r'(.*)_(.+)_(.+)_(\d+)\.ascmhl', filename)
					if parts.__len__() == 1 and parts[0].__len__() == 4:
						filepath = os.path.join(asc_mhl_folder_path, filename)
						hash_list = MHLHashListXMLBackend.parse(filepath)

						generation_number = int(parts[0][3])
						hash_list.generation_number = generation_number
						hash_list.filename = filename
						hash_lists.append(hash_list)
					else:
						logger.error(f'name of ascmhl file {filename} doesnt conform to naming convention')
		# sort all found hash lists by generation number first to make sure we add them to the history in order
		hash_lists.sort(key=lambda x: x.generation_number)
		for hash_list in hash_lists:
			history.append_hash_list(hash_list)
		return history

	@staticmethod
	def create_new_generation(history, new_hash_list):
		MHLHistoryXMLBackend._validate_new_hash_list(history, new_hash_list)
		file_name, generation_number = MHLHistoryXMLBackend._new_generation_filename(history)
		file_path = os.path.join(history.asc_mhl_path, file_name)
		new_hash_list.generation_number = generation_number
		MHLHashListXMLBackend.write_hash_list(new_hash_list, file_path)
		history.append_hash_list(new_hash_list)

	@staticmethod
	def _new_generation_filename(history):
		date_string = datetime_now_filename_string()
		index = history.latest_generation_number() + 1
		file_name = os.path.basename(os.path.normpath(history.get_root_path())) + "_" + date_string + "_" + str(index).zfill(
			4) + ".ascmhl"
		return file_name, index

	@staticmethod
	def _validate_new_hash_list(history, hash_list):
		"""Method to check mandatory conditions e.g. before serializing
		Validates for example that a new secondary hash in a different format is verified
		against the original hash(format) of the same file
		"""

		# TODO: validate new secondary hash entries
		for media_hash in hash_list.media_hashes:
			for hash_entry in media_hash.hash_entries:
				if hash_entry.action == 'new' and hash_entry.secondary is True:
					# TODO: do need to use the original hash here or can we also use another secondary hash
					original_hash_entry = history.find_original_hash_entry_for_path(media_hash.relative_filepath)
					required_hash_entry = media_hash.find_hash_entry_for_format(original_hash_entry.hash_format)
					if required_hash_entry is None:
						raise AssertionError('no hash entry found for new secondary hash', hash_entry)
					if required_hash_entry.action != 'verified':
						raise AssertionError('hash entry for new secondary hash not verified', hash_entry, required_hash_entry)
		return True


