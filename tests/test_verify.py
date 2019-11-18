import pytest
import click
from click.testing import CliRunner
from src import mhl_cli
import os

# TODO: make the cli output testable (i.e. don't include dynamic data such as dates in output like filenames)
# TODO: use a common test setup/fixture


def test_verification_succeeds():
    """
    tests that verification succeeds if we verify against an unchanged structure.
    :return:
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir('A002R2EC')
        os.mkdir('A002R2EC/Clips')
        with open('Sidecar.txt', 'w') as f:
            f.write('BLOREM ipsum dolor sit amet, consetetur sadipscing elitr.\n')
        with open('A002R2EC/Clips/A002C006_141024_R2EC.mov', 'w') as f:
            f.write('abcd\n')
        with open('A002R2EC/Clips/A002C007_141024_R2EC.mov', 'w') as f:
            f.write('def\n')

        first_result = runner.invoke(mhl_cli, ['verify', 'A002R2EC/Clips'])
        print(first_result.output)
        assert first_result.exit_code == 0

        second_result = runner.invoke(mhl_cli, ['verify', 'A002R2EC/Clips'])
        print(second_result.output)
        assert second_result.exit_code == 0
        assert first_result.output == second_result.output


def test_verification_fails():
    """
    tests that verification fails if we verify against an unchanged structure.
    :return:
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir('A002R2EC')
        os.mkdir('A002R2EC/Clips')
        with open('Sidecar.txt', 'w') as f:
            f.write('BLOREM ipsum dolor sit amet, consetetur sadipscing elitr.\n')
        with open('A002R2EC/Clips/A002C006_141024_R2EC.mov', 'w') as f:
            f.write('abcd\n')
        with open('A002R2EC/Clips/A002C007_141024_R2EC', 'w') as f:
            f.write('def\n')

        result = runner.invoke(mhl_cli, ['verify', 'A002R2EC/Clips'])
        print(result.output)
        assert result.exit_code == 0

        # now change a file and ensure verification fails
        with open('A002R2EC/Clips/A002C007_141024_R2EC', 'w') as f:
            f.write('ghi\n')

        result = runner.invoke(mhl_cli, ['verify', 'A002R2EC/Clips'])
        print(result.output)
        # assert that our program exiting with an exit code of 1
        assert result.exit_code == 1
