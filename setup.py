from setuptools import setup

setup(
    name='mhl',
    version='0.1',
    py_modules=['cli'],
    # TODO: update install_requires... might be missing some
    install_requires=[
        'Click',
        'xattr'
        'xxhash',
        'lxml',
    ],
    entry_points='''
        [console_scripts]
        mhl=main:mhl_cli
    ''',
)
