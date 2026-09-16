import atexit
import json
import os

from lib.tracelib.trace_client import REASON_ENVIRONMENT, TraceClient


# @author Daniel McCoy Stephenson
# @since September 11th, 2026
class UsageReportingService:
    """Reports that Apex was used to the trace service, and nothing else.

    What is sent: a ``startup`` event when the game starts (program name and
    version only) and a ``simulation-started`` event when a simulation begins.
    Nothing about the machine, the user, or the simulation's contents.

    Reporting is on by default and switched off by setting
    ``usage_reporting.enabled`` to ``false`` in ``settings.json`` next to
    ``version.txt``, or for every trace-reporting program at once with the
    ``TRACE_USAGE_REPORTING=off`` or ``DO_NOT_TRACK=1`` environment
    variables (the vendored client checks those first, so they win over the
    settings file). The file is created on the first run after this feature
    was added, and a one-line notice is printed exactly that once. Details:
    https://github.com/Stephenson-Software/trace#usage-reporting

    Every call returns immediately and never raises: the network happens on
    a daemon thread owned by the vendored trace client.
    """

    APPLICATION = "apex"
    SETTINGS_FILE = "settings.json"
    VERSION_FILE = "version.txt"
    SETTINGS_KEY = "usage_reporting"
    DEFAULT_ENDPOINT = "https://trace.danielstephenson.dev"
    DEFAULT_KEY = "McIMZNatgE3SlbwlW_pd629oWKQ2F3zwUeOCHO4BLA0"
    DETAILS_URL = "https://github.com/Stephenson-Software/trace#usage-reporting"
    NOTICE = (
        "Usage reporting is on: apex sends its name and version at startup and a "
        "simulation-started event to https://trace.danielstephenson.dev - nothing about you, "
        "your machine or the simulation. Turn it off with \"usage_reporting\": {\"enabled\": false} "
        "in settings.json, or for every trace-reporting program with the environment variable "
        "TRACE_USAGE_REPORTING=off. Details: " + DETAILS_URL
    )
    NOTICE_OFF_BY_ENVIRONMENT = "Usage reporting is off (environment). Details: " + DETAILS_URL

    def __init__(self, settingsFile=SETTINGS_FILE, versionFile=VERSION_FILE):
        self.settingsFile = settingsFile
        self.versionFile = versionFile
        # Nothing below can raise past this point: a broken settings file or
        # a bad endpoint leaves the client disabled instead of stopping the game.
        self.client = TraceClient.disabled()
        try:
            settings = self.__loadSettings()
            firstRun = self.SETTINGS_KEY not in settings
            if firstRun:
                settings[self.SETTINGS_KEY] = self.__defaultBlock()
                self.__saveSettings(settings)
            block = settings.get(self.SETTINGS_KEY) or {}
            # Always built through the client, even when settings say off:
            # the client checks TRACE_USAGE_REPORTING / DO_NOT_TRACK first and
            # records why it is off in disabled_reason.
            self.client = TraceClient(
                str(block.get("endpoint") or self.DEFAULT_ENDPOINT),
                self.APPLICATION,
                key=str(block.get("key") or ""),
                enabled=bool(block.get("enabled", True)),
            )
            if firstRun:
                if self.client.disabled_reason == REASON_ENVIRONMENT:
                    print(self.NOTICE_OFF_BY_ENVIRONMENT)
                else:
                    print(self.NOTICE)
        except Exception:
            self.client = TraceClient.disabled()
        atexit.register(self.close)

    # public methods ---------------------------------------------------------
    def reportStartup(self):
        version = self.__readVersion()
        tags = {"version": version} if version else None
        self.client.report("startup", tags=tags)

    def reportSimulationStarted(self):
        self.client.report("simulation-started")

    def close(self):
        self.client.close()

    # private methods --------------------------------------------------------
    def __defaultBlock(self):
        return {
            "enabled": True,
            "endpoint": self.DEFAULT_ENDPOINT,
            "key": self.DEFAULT_KEY,
        }

    def __loadSettings(self):
        if not os.path.isfile(self.settingsFile):
            return {}
        with open(self.settingsFile, "r") as file:
            settings = json.load(file)
        return settings if isinstance(settings, dict) else {}

    def __saveSettings(self, settings):
        with open(self.settingsFile, "w") as file:
            json.dump(settings, file, indent=4)
            file.write("\n")

    def __readVersion(self):
        if not os.path.isfile(self.versionFile):
            return None
        with open(self.versionFile, "r") as file:
            return file.read().strip() or None
