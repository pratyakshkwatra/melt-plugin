import pytest
from unittest.mock import MagicMock, patch
import os
import sqlite3
import msgpack
import base64

from octoprint_melt import MeltPlugin

@pytest.fixture
def plugin():
    # Setup
    p = MeltPlugin()
    p._logger = MagicMock()
    p._printer = MagicMock()
    p._plugin_manager = MagicMock()
    p._file_manager = MagicMock()
    
    # Mock data folder
    p.get_plugin_data_folder = MagicMock(return_value="/tmp/melt_test_data")
    if not os.path.exists("/tmp/melt_test_data"):
        os.makedirs("/tmp/melt_test_data")
        
    yield p
    
    # Teardown
    db_path = "/tmp/melt_test_data/metrics.db"
    if os.path.exists(db_path):
        os.remove(db_path)


def test_on_after_startup(plugin):
    """Test SQLite initialization on startup."""
    plugin.on_after_startup()
    plugin._logger.info.assert_called_with("Melt plugin started!")
    
    assert os.path.exists("/tmp/melt_test_data/metrics.db")
    conn = sqlite3.connect("/tmp/melt_test_data/metrics.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    assert "metrics" in tables
    assert "print_jobs" in tables


@patch('octoprint_melt.jsonify')
def test_get_telemetry(mock_jsonify, plugin):
    """Test telemetry REST API returns correct JSON state."""
    plugin._printer.get_state_id.return_value = "PRINTING"
    plugin._printer.get_current_data.return_value = {"progress": {"completion": 50}}
    plugin._printer.get_current_temperatures.return_value = {"tool0": {"actual": 200, "target": 205}}
    
    mock_jsonify.side_effect = lambda x: x
    
    resp = plugin.get_telemetry()
    assert resp["status"] == "ok"
    assert resp["state"] == "PRINTING"


def test_on_event_broadcasts_msgpack(plugin):
    """Test WebSocket broadcasting packs to msgpack and base64 encodes."""
    plugin._identifier = "melt"
    plugin._printer.get_current_data.return_value = {"foo": "bar"}
    
    plugin.on_event("PrintProgress", {"progress": 10})
    
    plugin._plugin_manager.send_plugin_message.assert_called_once()
    args, _ = plugin._plugin_manager.send_plugin_message.call_args
    assert args[0] == "melt"
    
    payload = args[1]["msgpack_payload"]
    decoded = base64.b64decode(payload)
    unpacked = msgpack.unpackb(decoded, raw=False)
    
    assert unpacked["type"] == "telemetry_update"
    assert unpacked["event"] == "PrintProgress"
    assert unpacked["payload"]["progress"] == 10
    assert unpacked["current_data"]["foo"] == "bar"


@patch('octoprint_melt.jsonify')
def test_get_thumbnail_not_found(mock_jsonify, plugin):
    """Test thumbnail endpoint when file is missing."""
    plugin._file_manager.path_on_disk.return_value = "/tmp/fake/does_not_exist.gcode"
    
    mock_jsonify.side_effect = lambda x: x
    resp, code = plugin.get_thumbnail("test.gcode")
    
    assert code == 404
    assert resp["status"] == "error"


@patch('requests.get')
def test_inject_cancel_object(mock_get, plugin):
    """Test safety GCode is injected when the last object is cancelled."""
    plugin.on_event("plugin_cancelobject_cancel", {"is_last_object": True})
    plugin._printer.commands.assert_called_with(["M104 S0", "M140 S0", "G28 X Y"])


from flask import Flask  # noqa: E402
app = Flask(__name__)


@patch('octoprint_melt.jsonify')
def test_toggle_plugin(mock_jsonify, plugin):
    """Test toggle REST API endpoint."""
    mock_jsonify.side_effect = lambda x: x
    
    with app.test_request_context(json={"enabled": False}):
        # Disable
        plugin._plugin_manager.get_plugin_info.return_value.enabled = True
        resp = plugin.toggle_plugin("arc_welder")
        plugin._plugin_manager.disable_plugin.assert_called_with("arc_welder")
        assert resp["status"] == "ok"


def test_db_persistence(plugin):
    """Test metrics are saved to SQLite correctly."""
    plugin.on_after_startup()
    conn = sqlite3.connect("/tmp/melt_test_data/metrics.db")
    cursor = conn.cursor()
    
    # Trigger PrintStarted to create record
    plugin.on_event("PrintStarted", {"name": "test.gcode"})
    
    # Trigger PrintDone to update record
    plugin.on_event("PrintDone", {"name": "test.gcode"})
    
    cursor.execute("SELECT * FROM print_jobs WHERE filename='test.gcode'")
    job = cursor.fetchone()
    assert job is not None
    assert job[1] == "test.gcode"
    assert job[4] == "success"
