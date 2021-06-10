import time
from packaging import version

import requests


def test_updater(requests_mock, mocker):
    mocker.patch("ascmhl.__version__.ascmhl_tool_version", "0.0.1")
    requests_mock.get(
        "https://api.github.com/repos/ascmitc/mhl/releases/latest",
        json={"tag_name": "v0.6.5"},
    )

    from importlib import reload
    import ascmhl.cli.update

    reload(ascmhl.cli.update)

    updater = ascmhl.cli.update.Updater()
    while not updater.finished:
        time.sleep(0.1)

    assert updater.latest_version == version.parse("0.6.5")
    assert updater.needs_update is True
    updater.join(timeout=1)


def test_updater_prerelease(requests_mock, mocker):
    mocker.patch("ascmhl.__version__.ascmhl_tool_version", "0.0.1")
    requests_mock.get(
        "https://api.github.com/repos/ascmitc/mhl/releases/latest",
        json={"tag_name": "v0.6.5-alpha.2"},
    )

    from importlib import reload
    import ascmhl.cli.update

    reload(ascmhl.cli.update)

    updater = ascmhl.cli.update.Updater()
    while not updater.finished:
        time.sleep(0.1)

    assert updater.latest_version == version.parse("0.6.5a2")
    assert updater.needs_update is False
    updater.join(timeout=1)


def test_updater_timeout(requests_mock, mocker):
    mocker.patch("ascmhl.__version__.ascmhl_tool_version", "0.0.1")

    requests_mock.get(
        "https://api.github.com/repos/ascmitc/mhl/releases/latest",
        exc=requests.exceptions.ConnectTimeout,
    )

    from importlib import reload
    import ascmhl.cli.update

    reload(ascmhl.cli.update)

    updater = ascmhl.cli.update.Updater()
    while not updater.finished:
        time.sleep(0.1)

    assert updater.latest_version is None
    assert updater.needs_update is False
    updater.join(timeout=1)
