from src.util.datetime import datetime_now_isostring_with_microseconds
from src.util import logger


class MediaHash:
    """class for representing one media hash for a (media) file to be managed by a MediaHashList object
    uses HashEntry class for storing information

    member variables:
    relative_filepath -- relative file path to the file (supplements the root_path from the MediaHashList object)
    filesize -- size of the file
    last_modification_date -- last modification date as read from the filesystem
    hash_entries -- list of HashEntry objects to manage hash values (e.g. for different formats)
    """

    def __init__(self, relative_filepath):
        self.relative_filepath = relative_filepath
        self.filesize = 0
        self.last_modification_date = None
        self.hash_entries = list()

    def append_hash_entry(self, hash_entry):
        """add one HashEntry object"""
        if hash_entry.action == 'new' and not len(self.hash_entries) == 0:
            hash_entry.secondary = True
        self.hash_entries.append(hash_entry)

    def hash_entry_for_format(self, hash_format):
        """retrieve the HashEntry object of a given hash format"""
        for hash_entry in self.hash_entries:
            if hash_entry.hash_format == hash_format:
                return hash_entry
        return None

    def has_hash_entry_of_action(self, action):
        """retrieve the HashEntry object of a given action"""
        for hash_entry in self.hash_entries:
            if hash_entry.action == action:
                return True
        return False

    def has_verified_or_failed_hash_entry(self):
        """returns bool value, indicates if the media hash has been verified (either succesfully or unsuccesfully)"""
        if self.has_hash_entry_of_action('verified'):
            return True
        elif self.has_hash_entry_of_action('failed'):
            return True
        else:
            return False

    def log_hash_entry(self, hash_format):
        """find HashEntry object of a given format and print it"""
        for hash_entry in self.hash_entries:
            if hash_entry.hash_format == hash_format:
                indicator = " "
                if hash_entry.action == 'failed':
                    indicator = "!"
                elif hash_entry.action == 'directory':
                    indicator = "d"
                logger.info("{0} {1}: {2} {3}: {4}".format(indicator,
                                                           hash_entry.hash_format.rjust(6),
                                                           hash_entry.hash_string.ljust(32),
                                                           (hash_entry.action if hash_entry.action is not None else "").ljust(10),
                                                           self.relative_filepath))


class HashEntry:
    """class to store one hash value to be managed by a MediaHash object

    member variables:
    hash_string -- stringg representation (hex) of the hash value
    hash_format -- string value, hash format, e.g. 'MD5', 'xxhash'
    hash_date -- date of creation of the hash value
    action -- action/result of verification, e.g. 'verified', 'failed', 'new', 'original'
    secondary -- bool value, indicates if created after the original hash (TBD)
    """

    def __init__(self, hash_string, hash_format):
        self.hash_string = hash_string
        self.hash_format = hash_format
        self.hash_date = datetime_now_isostring_with_microseconds()
        self.action = None
        self.secondary = False

    def matches_hash_entry(self, other_hash_entry):
        """compare HashEntry objects for matching hash values (and format)"""
        if self.hash_format != other_hash_entry.hash_format:
            return False
        if self.hash_string != other_hash_entry.hash_string:
            return False
        return True
