import atexit
import json
import os
import re
import sys

from lib.tracelib.trace_client import REASON_ENVIRONMENT, TraceClient, allows_reporting, environment_opts_out


def installIdFile(application):
    """Where this installation's random trace ID is kept:
    ``<user data dir>/<application>/trace-install-id``, the user data dir being
    ``%APPDATA%`` on Windows, ``~/Library/Application Support`` on macOS and
    ``$XDG_DATA_HOME`` (or ``~/.local/share``) elsewhere. The client only reads
    or writes it when reporting is on."""
    home = os.path.expanduser("~")
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", "").strip() or os.path.join(home, "AppData", "Roaming")
    elif sys.platform == "darwin":
        base = os.path.join(home, "Library", "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME", "").strip() or os.path.join(home, ".local", "share")
    return os.path.join(base, application.lower(), "trace-install-id")


def _normaliseKey(key):
    return re.sub(r"[^a-z0-9]", "", str(key).lower())


def hasNearMissOptOut(settings, settingsKey="usage_reporting", switchKey="enabled"):
    """Whether ``settings`` holds an attempt to turn usage reporting off that
    is not written exactly as ``settingsKey`` -> ``switchKey``. Such a setting
    would not be recognised, the first-run block (``enabled: true``) would be
    written next to it, and reporting would stay on. An operator who wrote
    any of these did not ask for reporting, so each counts as off:

    - a top-level key that spells "usage reporting" another way
      (``usage-reporting``, ``usageReporting``, ``UsageReporting``, ...)
      holding a value, or an ``enabled``-like key, that is not clearly on;
    - ``"usage_reporting": "off"`` -- a value instead of a block;
    - inside any such block, a key that spells "enabled" another way
      (``enable``, ``Enabled``, ...) that is not clearly on, or one that
      spells "disabled" whose value is on.
    """
    for key, value in settings.items():
        if "usagereport" not in _normaliseKey(key):
            continue
        if not isinstance(value, dict):
            if not allows_reporting(value):
                return True
            continue
        for child, childValue in value.items():
            if key == settingsKey and child == switchKey:
                continue  # the switch itself, read by the caller
            name = _normaliseKey(child)
            if "disabl" in name and allows_reporting(childValue):
                return True
            if "enabl" in name and not allows_reporting(childValue):
                return True
    return False


# @author Daniel McCoy Stephenson
# @since September 11th, 2026
class UsageReportingService:
    """Reports that Apex was used to the trace service, and nothing else.

    What is sent: a ``startup`` event when the game starts and a
    ``simulation-started`` event when a simulation begins, each carrying the
    program name and version, plus a random installation ID (the tag
    ``install``, kept in :func:`installIdFile` or taken from the
    ``TRACE_INSTALL_ID`` environment variable) so installations can be
    counted. Nothing about the user or the simulation's contents.

    Reporting is on by default and switched off by setting
    ``usage_reporting.enabled`` to ``false`` in ``settings.json`` next to
    ``version.txt``, or for every trace-reporting program at once with the
    ``TRACE_USAGE_REPORTING=off`` or ``DO_NOT_TRACK=1`` environment
    variables (the vendored client checks those first, so they win over the
    settings file). The file is created on the first run after this feature
    was added, and a one-line notice is printed exactly that once. Details:
    https://danielstephenson.dev/usage-reporting

    Every switch fails closed: only ``true`` (or the strings ``"true"``,
    ``"on"``, ``"yes"``, ``"1"``) turns reporting on; ``"false"``, ``"off"``,
    ``0``, a typo, or a ``usage_reporting`` that is not a block at all leave
    it off. A settings file that cannot be read, or is not a JSON object, is
    never rewritten and leaves reporting off. A first run under an
    environment opt-out records ``"enabled": false``, so the opt-out
    survives a later run without the variable. An opt-out written under
    another spelling (``usage-reporting``, ``usageReporting``, an
    ``enable``/``Enabled`` switch, ``disabled: true``) also counts as off,
    and the first run then records ``"enabled": false`` (see
    :func:`hasNearMissOptOut`).

    Every call returns immediately and never raises: the network happens on
    a daemon thread owned by the vendored trace client.
    """

    APPLICATION = "apex"
    SETTINGS_FILE = "settings.json"
    VERSION_FILE = "version.txt"
    #: Sent as the version when ``version.txt`` is missing or empty, so a
    #: source checkout without one still starts (the client requires a version).
    UNKNOWN_VERSION = "unknown"
    SETTINGS_KEY = "usage_reporting"
    DEFAULT_ENDPOINT = "https://trace.danielstephenson.dev"
    DEFAULT_KEY = "McIMZNatgE3SlbwlW_pd629oWKQ2F3zwUeOCHO4BLA0"
    DETAILS_URL = "https://danielstephenson.dev/usage-reporting"
    NOTICE = (
        "Usage reporting is on: apex sends its name, its version and a random installation ID "
        "at startup and a simulation-started event to https://trace.danielstephenson.dev - "
        "nothing about you or the simulation. Turn it off with \"usage_reporting\": {\"enabled\": false} "
        "in settings.json, or for every trace-reporting program with the environment variable "
        "TRACE_USAGE_REPORTING=off. Details: " + DETAILS_URL
    )
    NOTICE_OFF_BY_ENVIRONMENT = (
        "Usage reporting is off (environment), and \"usage_reporting\": {\"enabled\": false} "
        "was written to settings.json so it stays off. Details: " + DETAILS_URL
    )
    NOTICE_OFF_BY_SETTINGS = (
        "Usage reporting is off (settings.json), and \"usage_reporting\": {\"enabled\": false} "
        "was written to settings.json so it stays off. Details: " + DETAILS_URL
    )

    def __init__(self, settingsFile=SETTINGS_FILE, versionFile=VERSION_FILE):
        self.settingsFile = settingsFile
        self.versionFile = versionFile
        # Nothing below can raise past this point: a broken settings file or
        # a bad endpoint leaves the client disabled instead of stopping the game.
        self.client = TraceClient.disabled()
        atexit.register(self.close)
        if sys.platform == "emscripten":
            # The browser (pygbag) build never reports: the client sends from a thread of
            # its own and a pygbag build has no threads, and there is no settings.json there
            # for a player to turn it off with, so nothing is written or printed either.
            return
        try:
            settings = self.__loadSettings()
            firstRun = self.SETTINGS_KEY not in settings
            # An opt-out written under another spelling counts as off.
            nearMissOptOut = hasNearMissOptOut(settings, self.SETTINGS_KEY)
            if firstRun:
                # Under an environment or near-miss opt-out the first run
                # records "off", so a later run does not report.
                settings[self.SETTINGS_KEY] = self.__defaultBlock(
                    enabled=not (environment_opts_out() or nearMissOptOut))
                self.__saveSettings(settings)
            block = settings.get(self.SETTINGS_KEY)
            if not isinstance(block, dict):
                # "usage_reporting": false (or "off", or anything else that is
                # not a block) is read as the switch itself, never as "no
                # block, use the defaults".
                block = {"enabled": block}
            # Always built through the client, even when settings say off:
            # the client checks TRACE_USAGE_REPORTING / DO_NOT_TRACK first and
            # records why it is off in disabled_reason.
            self.client = TraceClient(
                str(block.get("endpoint") or self.DEFAULT_ENDPOINT),
                self.APPLICATION,
                self.__readVersion() or self.UNKNOWN_VERSION,
                key=str(block.get("key") or ""),
                # Not bool(): bool("false") is True. Only true or an "on"
                # string reports; "false", "off", 0, null or a typo do not.
                enabled=allows_reporting(block.get("enabled", True)) and not nearMissOptOut,
                # The client resolves these only after its own opt-out checks,
                # so a disabled client never creates the file.
                install_id=os.environ.get("TRACE_INSTALL_ID"),
                install_id_file=installIdFile(self.APPLICATION),
            )
            if firstRun:
                if self.client.disabled_reason == REASON_ENVIRONMENT:
                    print(self.NOTICE_OFF_BY_ENVIRONMENT)
                elif nearMissOptOut:
                    print(self.NOTICE_OFF_BY_SETTINGS)
                else:
                    print(self.NOTICE)
        except Exception:
            self.client = TraceClient.disabled()

    # public methods ---------------------------------------------------------
    def reportStartup(self):
        self.client.report("startup")

    def reportSimulationStarted(self):
        self.client.report("simulation-started")

    def close(self):
        self.client.close()

    # private methods --------------------------------------------------------
    def __defaultBlock(self, enabled=True):
        return {
            "enabled": enabled,
            "endpoint": self.DEFAULT_ENDPOINT,
            "key": self.DEFAULT_KEY,
        }

    def __loadSettings(self):
        if not os.path.isfile(self.settingsFile):
            return {}
        with open(self.settingsFile, "r") as file:
            settings = json.load(file)
        if not isinstance(settings, dict):
            # Treating it as empty would rewrite the file with reporting on.
            raise ValueError("settings.json is not a JSON object")
        return settings

    def __saveSettings(self, settings):
        with open(self.settingsFile, "w") as file:
            json.dump(settings, file, indent=4)
            file.write("\n")

    def __readVersion(self):
        if not os.path.isfile(self.versionFile):
            return None
        with open(self.versionFile, "r") as file:
            return file.read().strip() or None
