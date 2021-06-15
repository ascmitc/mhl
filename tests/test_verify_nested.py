"""
__author__ = "Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

import os
from freezegun import freeze_time
from click.testing import CliRunner

from ascmhl.history import MHLHistory
import ascmhl.commands

scenario_output_path = "examples/scenarios/Output"
fake_ref_path = "/ref"

# def test_create_simple(fs, simple_mhl_history):
#    """
#    test that ensures that hasehs in a new format are also verified in child histories
#    used to verify fix of bug: https://github.com/ascmitc/mhl/issues/48
#    """
#
#    runner = CliRunner()
#    result = runner.invoke(ascmhl.commands.create, ['/root', '-h', 'md5'])
#    assert result.exit_code == 0


def test_create_nested(fs, nested_mhl_histories):
    """
    test that ensures that hasehs in a new format are also verified in child histories
    used to verify fix of bug: https://github.com/ascmitc/mhl/issues/48
    """

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root", "-h", "md5"])
    assert result.exit_code == 0
