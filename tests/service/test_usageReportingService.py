import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from service.usageReportingService import UsageReportingService


# helper methods -------------------------------------------------------------
class Capture:
    def __init__(self):
        self.requests = []
        self.arrived = threading.Event()


def startStubServer(capture):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0"))
            capture.requests.append({
                "path": self.path,
                "authorization": self.headers.get("Authorization"),
                "body": json.loads(self.rfile.read(length).decode("utf-8")),
            })
            self.send_response(201)
            self.send_header("Content-Length", "0")
            self.end_headers()
            capture.arrived.set()

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


@pytest.fixture
def stub():
    capture = Capture()
    server = startStubServer(capture)
    capture.endpoint = "http://127.0.0.1:%d" % server.server_address[1]
    yield capture
    server.shutdown()
    server.server_close()


@pytest.fixture
def workdir(tmp_path, monkeypatch):
    # The machine running the tests may itself have opted out of usage
    # reporting; every test starts from a clean environment.
    monkeypatch.delenv("TRACE_USAGE_REPORTING", raising=False)
    monkeypatch.delenv("DO_NOT_TRACK", raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "version.txt").write_text("9.9.9-TEST")
    return tmp_path


def writeSettings(workdir, block, extra=None):
    settings = dict(extra or {})
    settings["usage_reporting"] = block
    (workdir / "settings.json").write_text(json.dumps(settings))


# first-run tests ------------------------------------------------------------
def test_firstRunPrintsNoticeAndWritesSettingsBlock(workdir, capsys):
    # execute
    service = UsageReportingService()
    service.close()

    # assert
    out = capsys.readouterr().out
    assert out.count(UsageReportingService.NOTICE) == 1
    assert "https://github.com/Stephenson-Software/trace#usage-reporting" in out
    assert "TRACE_USAGE_REPORTING=off" in out
    settings = json.loads((workdir / "settings.json").read_text())
    assert settings["usage_reporting"]["enabled"] is True
    assert settings["usage_reporting"]["endpoint"] == UsageReportingService.DEFAULT_ENDPOINT
    assert settings["usage_reporting"]["key"] == UsageReportingService.DEFAULT_KEY


def test_secondRunDoesNotPrintNoticeAgain(workdir, capsys):
    # prepare
    UsageReportingService().close()
    capsys.readouterr()

    # execute
    UsageReportingService().close()

    # assert
    assert UsageReportingService.NOTICE not in capsys.readouterr().out


def test_firstRunKeepsOtherSettings(workdir, capsys):
    # prepare
    (workdir / "settings.json").write_text(json.dumps({"other": 1}))

    # execute
    UsageReportingService().close()

    # assert
    settings = json.loads((workdir / "settings.json").read_text())
    assert settings["other"] == 1
    assert "usage_reporting" in settings


# reporting tests ------------------------------------------------------------
def test_startupEventCarriesApplicationAndVersion(workdir, stub):
    # prepare
    writeSettings(workdir, {"enabled": True, "endpoint": stub.endpoint, "key": "test-key"})
    service = UsageReportingService()

    # execute
    service.reportStartup()
    assert stub.arrived.wait(5)
    service.close()

    # assert
    request = stub.requests[0]
    assert request["path"] == "/api/metrics"
    assert request["authorization"] == "Bearer test-key"
    assert request["body"] == {"application": "apex", "name": "startup", "tags": {"version": "9.9.9-TEST"}}


def test_startupEventOmitsVersionWhenVersionFileIsMissing(workdir, stub):
    # prepare
    (workdir / "version.txt").unlink()
    writeSettings(workdir, {"enabled": True, "endpoint": stub.endpoint, "key": "test-key"})
    service = UsageReportingService()

    # execute
    service.reportStartup()
    assert stub.arrived.wait(5)
    service.close()

    # assert
    assert stub.requests[0]["body"] == {"application": "apex", "name": "startup"}


def test_simulationStartedEventIsSent(workdir, stub):
    # prepare
    writeSettings(workdir, {"enabled": True, "endpoint": stub.endpoint, "key": "test-key"})
    service = UsageReportingService()

    # execute
    service.reportSimulationStarted()
    assert stub.arrived.wait(5)
    service.close()

    # assert
    assert stub.requests[0]["body"] == {"application": "apex", "name": "simulation-started"}


# opt-out tests --------------------------------------------------------------
def test_disabledSettingSendsNothing(workdir, stub):
    # prepare
    writeSettings(workdir, {"enabled": False, "endpoint": stub.endpoint, "key": "test-key"})
    service = UsageReportingService()

    # execute
    service.reportStartup()
    service.reportSimulationStarted()
    service.close()

    # assert
    assert service.client.enabled is False
    assert stub.requests == []


def test_emptyKeySendsNothing(workdir, stub):
    # prepare
    writeSettings(workdir, {"enabled": True, "endpoint": stub.endpoint, "key": ""})

    # execute
    service = UsageReportingService()
    service.close()

    # assert
    assert service.client.enabled is False


def test_brokenSettingsFileLeavesReportingDisabled(workdir, capsys):
    # prepare
    (workdir / "settings.json").write_text("{not json")

    # execute
    service = UsageReportingService()
    service.close()

    # assert
    assert service.client.enabled is False
    assert UsageReportingService.NOTICE not in capsys.readouterr().out


def test_doNotTrackEnvironmentVariableWinsOverEnabledSettings(workdir, stub, monkeypatch):
    # prepare
    writeSettings(workdir, {"enabled": True, "endpoint": stub.endpoint, "key": "test-key"})
    monkeypatch.setenv("DO_NOT_TRACK", "1")
    service = UsageReportingService()

    # execute
    service.reportStartup()
    service.reportSimulationStarted()
    service.close()

    # assert
    assert service.client.enabled is False
    assert service.client.disabled_reason == "environment"
    assert stub.requests == []


def test_traceUsageReportingOffEnvironmentVariableWinsOverEnabledSettings(workdir, stub, monkeypatch):
    # prepare
    writeSettings(workdir, {"enabled": True, "endpoint": stub.endpoint, "key": "test-key"})
    monkeypatch.setenv("TRACE_USAGE_REPORTING", "off")
    service = UsageReportingService()

    # execute
    service.reportStartup()
    service.close()

    # assert
    assert service.client.enabled is False
    assert service.client.disabled_reason == "environment"
    assert stub.requests == []


def test_firstRunUnderEnvironmentOptOutSaysReportingIsOff(workdir, capsys, monkeypatch):
    # prepare
    monkeypatch.setenv("TRACE_USAGE_REPORTING", "off")

    # execute
    service = UsageReportingService()
    service.close()

    # assert
    out = capsys.readouterr().out
    assert UsageReportingService.NOTICE not in out
    assert out.count(UsageReportingService.NOTICE_OFF_BY_ENVIRONMENT) == 1
    settings = json.loads((workdir / "settings.json").read_text())
    assert settings["usage_reporting"]["enabled"] is True, "the environment never rewrites the settings file"
