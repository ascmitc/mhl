"""
__author__ = "Patrick Renner"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

from . import logger
from .__version__ import ascmhl_reference_hash_format
from .chain import MHLChain, MHLChainGeneration
from .hashlist import MHLHashList
from .hasher import create_filehash
import os


def parse(file_path):
    """parsing the chain.txt file and building the MHLChain for the chain member variable"""
    logger.debug(f'parsing "{os.path.basename(file_path)}"...')

    chain = MHLChain(file_path)

    if not os.path.exists(file_path):
        return chain

    lines = [line.rstrip("\n") for line in open(file_path)]

    for line in lines:
        line = line.rstrip().lstrip()
        if line != "" and not line.startswith("#"):
            generation = _generation_from_line_in_chainfile(line)
            if generation is None:
                logger.error("cannot read line")
                continue
            chain.append_generation(generation)

    return chain


def _generation_from_line_in_chainfile(line):
    """creates a Generation object from a line int the chain file"""

    # TODO split by whitespace
    parts = line.split(None)

    if parts is not None and parts.__len__() < 4:
        logger.error('cannot read line "{line}"')
        return None

    generation = MHLChainGeneration(
        int(parts[0]),
        parts[1],
        (parts[2])[:-1],
        parts[3],
    )

    if parts.__len__() == 6:
        generation.signature_identifier = parts[4]
        generation.signature = parts[5]

    # TODO sanity checks
    return generation


def write_chain(chain: MHLChain, new_hash_list: MHLHashList):
    logger.debug(f'writing "{os.path.basename(chain.file_path)}"...')
    _append_new_generation_to_file(chain, new_hash_list)


def _line_for_chainfile(chain_generation: MHLChainGeneration):
    """creates a text line for appending a generation to a chain file"""
    result_string = (
        str(chain_generation.generation_number).zfill(4)
        + " "
        + chain_generation.ascmhl_filename
        + " "
        + chain_generation.hash_format
        + ": "
        + chain_generation.hash_string
    )

    return result_string


def _append_new_generation_to_file(chain: MHLChain, hash_list: MHLHashList):
    """appends an externally created Generation object to the chain file"""

    # get a new generation for a hashlist
    generation = MHLChainGeneration(
        hash_list.generation_number,
        hash_list.get_file_name(),
        ascmhl_reference_hash_format,
        create_filehash(ascmhl_reference_hash_format, hash_list.file_path),
    )

    # TODO sanity checks
    # - if generation is already part of self.generations
    # - if generation number is sequential

    # immediately write to file
    logger.debug(f'   appending chain generation for "{generation.ascmhl_filename}" to chain file')

    with open(chain.file_path, "a") as file:
        file.write(_line_for_chainfile(generation) + "\n")

    # FIXME: check if file could be created

    # …and store here
    # FIXME: only if successfully written to file
    chain.generations.append(generation)
