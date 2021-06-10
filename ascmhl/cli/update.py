from packaging import version
from threading import Thread

import requests

from ascmhl.__version__ import ascmhl_tool_version


class Updater(Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.latest_version = None
        self.finished = False
        self.start()

    def run(self):
        self._get_latest_version()
        self.finished = True

    @property
    def needs_update(self) -> bool:
        if not self.latest_version:
            return False

        return (
            self.latest_version > version.parse(ascmhl_tool_version)
            and not self.latest_version.is_devrelease
            and not self.latest_version.is_prerelease
        )

    def _get_latest_version(self):
        try:
            r = requests.get("https://api.github.com/repos/ascmitc/mhl/releases/latest")
            r.raise_for_status()
            self.latest_version = version.parse(r.json().get("tag_name"))
        except requests.exceptions.RequestException:
            self.finished = True
