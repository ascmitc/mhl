from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    author="Patrick Renner, Alexander Sahm",
    author_email="opensource@pomfort.com",
    description="ASC Media Hash List (ASC MHL)",
    entry_points={"console_scripts": ["ascmhl = mhl.cli.ascmhl:mhltool_cli"]},
    include_package_data=True,
    install_requires=[
        "Click>=7.0",
        "lxml>=4.6.2",
        "pathspec>=0.8.0",
        "xattr>=0.9.6",
        "xxhash>=2.0.0",
    ],
    dependency_links=[],
    long_description=long_description,
    long_description_content_type="text/markdown",
    name="ascmhl",
    packages=find_packages(),
    setup_requires=["pytest-runner", "setuptools_scm"],
    tests_require=["pytest", "pyfakefs", "freezegun", "testfixtures"],
    url="https://github.com/ascmitc/mhl",
    use_scm_version=True,
    python_requires="~=3.7",
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
