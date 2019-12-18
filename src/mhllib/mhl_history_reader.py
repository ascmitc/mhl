import os
import re
from src.mhllib import mhl_defines
from src.mhllib.mhl_history import MHLHistory
from src.mhllib.mhl_hashlist_reader import MHLHashListReader
from src.util import logger

class MHLHistoryParser:
	"""
	class for reading an asc-mhl folder with MHL files

	lots of helper functions

	member variables:
	folderpath -- path to the enclosing folder (not the asc-mhl folder itself, but one up)
	"""
	@staticmethod
	def parse(asc_mhl_folder_path):
		"""finds all MHL files in the asc-mhl folder, returns the mhl_history instance with all mhl_hashlists """

		for root, directories, filenames in os.walk(asc_mhl_folder_path):
			history = MHLHistory()
			history.asc_mhl_path = asc_mhl_folder_path
			for filename in filenames:
				if filename.endswith(mhl_defines.ascmhl_file_extension):
					# A002R2EC_2019-06-21_082301_0005.ascmhl
					parts = re.findall(r'(.*)_(.+)_(.+)_(\d+)\.ascmhl', filename)
					if parts.__len__() == 1 and parts[0].__len__() == 4:
						filepath = os.path.join(asc_mhl_folder_path, filename)
						hash_list = MHLHashListReader.parse(filepath)

						generation_number = int(parts[0][3])
						hash_list.generation_number = generation_number
						hash_list.filename = filename
						history.append_hash_list(hash_list)

					else:
						logger.error(f'name of ascmhl file {filename} doesnt conform to naming convention')
		return history




