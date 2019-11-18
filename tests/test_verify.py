import pytest
import click
from click.testing import CliRunner
from src import mhl_cli
import os
from contextlib import contextmanager

# TODO: make the cli output testable without regex(i.e. don't include dynamic data such as dates in output like filenames)
# TODO: consider a table-test driven style


@contextmanager
def A002R2EC():
    """
    function used to recreate the A002R2EC template structure from scratch in a new temp dir each test invocation
    :return:
    """
    root = 'A002R2EC'
    runner = CliRunner()
    try:
        with runner.isolated_filesystem():
            os.mkdir(root)
            os.mkdir(f'{root}/Clips')
            with open(f'{root}/Sidecar.txt', 'w') as f:
                f.write('BLOREM ipsum dolor sit amet, consetetur sadipscing elitr.\n')
            with open(f'{root}/Clips/A002C006_141024_R2EC.mov', 'w') as f:
                f.write('abcd\n')
            with open(f'{root}/Clips/A002C007_141024_R2EC.mov', 'w') as f:
                f.write('def\n')
            yield runner
    finally:
        print('exiting context manager')


def test_verify_succeeds_on_no_change():
    """
    tests that verification succeeds if we verify against an unchanged structure.
    :return:
    """
    with A002R2EC() as runner:
        result = runner.invoke(mhl_cli, ['verify', 'A002R2EC'])
        assert result.exit_code == 0
        result = runner.invoke(mhl_cli, ['verify', 'A002R2EC'])
        assert result.exit_code == 0


def test_verify_fails_on_modify_file():
    """
    tests that verification fails if we verify against a modified structure.
    :return:
    """
    with A002R2EC() as runner:
        result = runner.invoke(mhl_cli, ['verify', 'A002R2EC'])
        assert result.exit_code == 0
        # now modify the sidecar file and ensure our verify function exits with code 1
        with open('A002R2EC/Sidecar.txt', 'w') as f:
            f.write('NOT THE ORIGINAL CONTENTS!!!\n')
        result = runner.invoke(mhl_cli, ['verify', 'A002R2EC'])
        print(result.output)
        assert result.exit_code == 1
