import pytest
import click
from click.testing import CliRunner
from src import mhl_cli
import os
from contextlib import contextmanager

# TODO: make the cli output testable without regex(i.e. don't include dynamic data such as dates in output like filenames)


class IsolatedInvoker(object):
    def __init__(self):
        self.runner = CliRunner()
        self.root = None
        self.result = None

    def verify(self):
        self.result = self.runner.invoke(mhl_cli, ['verify', self.root])
        return self.result


class A002R2EC(IsolatedInvoker):
    """
    A002R2EC creates a bit equivalent match to the Scenarios/Output/A002R2EC Template structure inside of a temporary isolated fs directory.
    """
    def __init__(self):
        super().__init__()
        self.root = "A002R2EC"

    @contextmanager
    def __enter__(self):
        with self.runner.isolated_filesystem() as iso_fs:
            os.mkdir(self.root)
            os.mkdir(f'{self.root}/Clips')
            with open('Sidecar.txt', 'w') as f:
                f.write('BLOREM ipsum dolor sit amet, consetetur sadipscing elitr.\n')
            with open('A002R2EC/Clips/A002C006_141024_R2EC.mov', 'w') as f:
                f.write('abcd\n')
            with open('A002R2EC/Clips/A002C007_141024_R2EC.mov', 'w') as f:
                f.write('def\n')
            print('yielding')
            yield iso_fs
            print('exiting yield')

    def __exit__(self):
        pass


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


# def test_verification_fails_on_file_changed():
#     """
#     tests that verification fails if we verify against a modified structure.
#     :return:
#     """
#     runner = CliRunner()
#     with runner.isolated_filesystem():
#         os.mkdir('A002R2EC')
#         os.mkdir('A002R2EC/Clips')
#         with open('Sidecar.txt', 'w') as f:
#             f.write('BLOREM ipsum dolor sit amet, consetetur sadipscing elitr.\n')
#         with open('A002R2EC/Clips/A002C006_141024_R2EC.mov', 'w') as f:
#             f.write('abcd\n')
#         with open('A002R2EC/Clips/A002C007_141024_R2EC', 'w') as f:
#             f.write('def\n')
#
#         result = runner.invoke(mhl_cli, ['verify', 'A002R2EC/Clips'])
#         print(result.output)
#         assert result.exit_code == 0
#
#         # now change a file and ensure verification fails
#         with open('A002R2EC/Clips/A002C007_141024_R2EC', 'w') as f:
#             f.write('ghi\n')
#
#         result = runner.invoke(mhl_cli, ['verify', 'A002R2EC/Clips'])
#         print(result.output)
#         # assert that our program failed by exiting with an exit code of 1
#         assert result.exit_code == 1
#
#
# def test_verification_fails_on_file_added():
#     """
#     tests that verification fails if we verify against a structure that has an added file.
#     :return:
#     """
#     runner = CliRunner()
#     with runner.isolated_filesystem():
#         os.mkdir('A002R2EC')
#         os.mkdir('A002R2EC/Clips')
#         with open('Sidecar.txt', 'w') as f:
#             f.write('BLOREM ipsum dolor sit amet, consetetur sadipscing elitr.\n')
#         with open('A002R2EC/Clips/A002C006_141024_R2EC.mov', 'w') as f:
#             f.write('abcd\n')
#         with open('A002R2EC/Clips/A002C007_141024_R2EC', 'w') as f:
#             f.write('def\n')
#
#         result = runner.invoke(mhl_cli, ['verify', 'A002R2EC/Clips'])
#         print(result.output)
#         assert result.exit_code == 0
#
#         # now change a file and ensure verification fails
#         with open('A002R2EC/Clips/A002C008_141024_R2EC', 'w') as f:
#             f.write('xyz\n')
#
#         result = runner.invoke(mhl_cli, ['verify', 'A002R2EC/Clips'])
#         print(result.output)
#         # assert that our program exiting with an exit code of 1
#         assert result.exit_code == 1
