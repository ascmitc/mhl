"""
__author__ = "Patrick Renner"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

from click.testing import CliRunner

from ascmhl.__version__ import ascmhl_tool_version
from ascmhl.cli.ascmhl import mhltool_cli


def test_version():
    runner = CliRunner()
    result = runner.invoke(mhltool_cli, "--version")
    assert result.exit_code == 0
    assert ascmhl_tool_version in result.output
