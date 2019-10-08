from src.util.datetime import datetime_now_filename_string
from src.util import logger
import os
import re
import click


class HashListFolderManager:
    """class for managing an asc-mhl folder with MHL files

    is used to write a ready XML string to a new MHL file, and also includes lots of helper functions

    member variables:
    folderpath -- path to the enclosing folder (not the asc-mhl folder itself, but one up)
    """

    ascmhl_folder_name = "asc-mhl"
    ascmhl_file_extension = ".ascmhl"

    def __init__(self, folderpath):
        # TODO: we shouldn't be setting verbosity on these classes. reference context for value when needed
        self.verbose = click.get_current_context().obj.verbose
        # TODO: what was this check for? click should handle path anomolies since we used the special "path" type.
        if not folderpath[len(folderpath):1] == os.path.sep:
            folderpath = folderpath + os.path.sep
        self.folderpath = folderpath

    def ascmhl_folder_path(self):
        """absolute path of the asc-mhl folder"""
        path = os.path.join(self.folderpath, HashListFolderManager.ascmhl_folder_name)
        return path

    def ascmhl_folder_exists(self):
        return os.path.exists(self.ascmhl_folder_path())

    def ascmhl_folder_exists_above_up_to_but_excluding(self, rootpath):
        """finds out if self is embedded within a folder that itself has an asc-mhl folder"""
        if os.path.relpath(self.folderpath, rootpath) is None:
            return False
        #path = os.path.dirname(os.path.normpath(self.folderpath))
        path = os.path.normpath(self.folderpath)
        rootpath = os.path.normpath(rootpath)
        while path != rootpath:
            ascmhl_path = os.path.join(path, self.ascmhl_folder_name)
            if os.path.exists(ascmhl_path):
                return True
            path = os.path.dirname(path)
        return False

    def queried_ascmhl_filename(self, generation_number):
        ascmhl = self._ascmhl_files(generation_number)
        if 'queried_filename' in ascmhl:
            return ascmhl['queried_filename']
        else:
            return None

    def earliest_ascmhl_generation_number(self) -> int:
        ascmhl = self._ascmhl_files()
        return ascmhl['earliest_generation_number']

    def earliest_ascmhl_filename(self):
        ascmhl = self._ascmhl_files()
        return ascmhl['earliest_filename']

    def latest_ascmhl_generation_number(self) -> int:
        ascmhl = self._ascmhl_files()
        return ascmhl['latest_generation_number']

    def latest_ascmhl_filename(self):
        ascmhl = self._ascmhl_files()
        return ascmhl['latest_filename']

    def _ascmhl_files(self, query_generation_number=None):
        """find all MHL files in the asc-mhl folder, returns information about found generations

        arguments:
        query_generation_number -- find additional information about a specific generation
        """
        ascmhl_folder_path = self.ascmhl_folder_path()
        if ascmhl_folder_path is None:
            return None
        else:
            queried_filename = None
            queried_generation_number = 0
            earliest_filename = None
            lowest_generation_number = 1000000
            latest_filename = None
            highest_generation_number = 0
            for root, directories, filenames in os.walk(ascmhl_folder_path):
                for filename in filenames:
                    if filename.endswith(HashListFolderManager.ascmhl_file_extension):
                        # A002R2EC_2019-06-21_082301_0005.ascmhl
                        parts = re.findall(r'(.*)_(.+)_(.+)_(\d+)\.ascmhl', filename)
                        if parts.__len__() == 1 and parts[0].__len__() == 4:
                            generation_number = int(parts[0][3])
                            if query_generation_number == generation_number:
                                queried_generation_number = generation_number
                                queried_filename = filename
                            if lowest_generation_number > generation_number:
                                lowest_generation_number = generation_number
                                earliest_filename = filename
                            if highest_generation_number < generation_number:
                                highest_generation_number = generation_number
                                latest_filename = filename
                        else:
                            logger.error(f'name of ascmhl file {filename} doesnt conform to naming convention')
            result_tuple = {'earliest_filename': earliest_filename,
                            'earliest_generation_number': lowest_generation_number,
                            'latest_filename': latest_filename,
                            'latest_generation_number': highest_generation_number}

            if queried_filename is not None:
                result_tuple['queried_filename'] = queried_filename
                result_tuple['queried_generation_number'] = queried_generation_number

            return result_tuple

    def path_for_ascmhl_file(self, filename):
        if filename is None:
            return None
        else:
            path = os.path.join(self.folderpath, HashListFolderManager.ascmhl_folder_name, filename)
            return path

    def path_for_ascmhl_generation_number(self, generation_number):
        if generation_number is None:
            return None
        else:
            filename = self.queried_ascmhl_filename(generation_number)
            if filename is None:
                return None
            path = os.path.join(self.folderpath, HashListFolderManager.ascmhl_folder_name, filename)
            return path

    def new_ascmhl_filename(self):
        date_string = datetime_now_filename_string()
        index = self.latest_ascmhl_generation_number() + 1
        return os.path.basename(os.path.normpath(self.folderpath)) + "_" + date_string + "_" + str(index).zfill(
            4) + ".ascmhl"

    def path_for_new_ascmhl_file(self):
        filename = self.new_ascmhl_filename()
        if filename is not None:
            return self.path_for_ascmhl_file(filename)

    def write_ascmhl(self, xml_string):
        """writes a given XML string into a new MHL file"""
        filepath = self.path_for_new_ascmhl_file()
        if filepath is not None:
            logger.info(f'writing {filepath}')
            with open(filepath, 'wb') as file:
                # FIXME: check if file could be created
                file.write(xml_string.encode('utf8'))
            return filepath

    def file_is_in_ascmhl_folder(self, filepath):
        ascmhl_folder_path = self.ascmhl_folder_path()
        if ascmhl_folder_path is None:
            return False
        else:
            return filepath.startswith(self.ascmhl_folder_path())