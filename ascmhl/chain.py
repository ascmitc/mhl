"""
__author__ = "Patrick Renner, Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""
from typing import List

from . import logger


class MHLChain:
    """
    class for representing a chain file with its list of generations (one for each ascmhl file)
    managed by the MHLHistory class
    uses MHLChainGeneration for storing information

    model member variables:
    mhl_history -- MHLHistory object for context
    generations -- list of MHLChainGeneration objects

    attribute member variables:
    file path -- absolute path to chain file
    """

    # init

    file_path: str
    generations: List["MHLChainGeneration"]

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.generations = []

    # build

    def append_generation(self, generation):
        self.generations.append(generation)

    # log

    def log(self):
        logger.info("     file path: {0}".format(self.file_path))
        for generation in self.generations:
            generation.log()


class MHLChainGeneration:
    """
    class for representing one generation
    managed by a MHLChain object

    model member variables:
    mhl_chain -- MHLChain object for context

    attribute member variables:
    generation_number -- integer, -1 means invalid
    ascmhl_filename --
    hashformat --
    hash_string --

    other member variables:
    """

    generation_number: int  # -1 means invalid
    ascmhl_filename: str
    hash_format: str
    hash_string: str

    def __init__(self, generation_number=-1, ascmhl_filename=None, hash_format=None, hash_string=None):
        # line string examples:
        # 0001 A002R2EC_2019-10-08_100916_0001.ascmhl SHA1: 9e9302b3d7572868859376f0e5802b87bab3199e

        self.generation_number = generation_number
        self.ascmhl_filename = ascmhl_filename
        self.hash_format = hash_format
        self.hash_string = hash_string

    def log(self):
        action = "*"  # FIXME
        indicator = " "

        logger.info(
            "{0} {1}: {2} {3}: {4}".format(
                indicator,
                self.hash_format.rjust(6),
                self.hash_string.ljust(32),
                action.ljust(10),
                self.ascmhl_filename,
            )
        )
