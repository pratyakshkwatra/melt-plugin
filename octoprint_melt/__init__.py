# flake8: noqa: E501, W293, E302, E303, E261, W291
import octoprint.plugin
from flask import jsonify
import os
import json
import sqlite3
import msgpack
import time
import base64

class MeltPlugin(octoprint.plugin.BlueprintPlugin,
                 octoprint.plugin.StartupPlugin,
                 octoprint.plugin.EventHandlerPlugin,
                 octoprint.plugin.TemplatePlugin,
                 octoprint.plugin.SettingsPlugin,
                 octoprint.plugin.AssetPlugin):

    def on_after_startup(self):
        self._logger.info("Melt plugin started!")
        # Setup local data persistence using SQLite
        self._data_folder = self.get_plugin_data_folder()
        self._db_path = os.path.join(self._data_folder, "metrics.db")
        
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                key TEXT PRIMARY KEY,
                value INTEGER
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS print_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                start_time REAL,
                end_time REAL,
                status TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS telemetry_timeseries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                hotend_temp REAL,
                bed_temp REAL,
                progress REAL
            )
        ''')
        cursor.execute("INSERT OR IGNORE INTO metrics (key, value) VALUES ('total_prints', 0)")
        cursor.execute("INSERT OR IGNORE INTO metrics (key, value) VALUES ('failed_prints', 0)")
        cursor.execute("INSERT OR IGNORE INTO metrics (key, value) VALUES ('total_print_time_seconds', 0)")
        conn.commit()
        conn.close()
        
    def _gather_plugin_telemetry(self):
        """Aggregate data from PrintTimeGenius, SpoolManager, etc."""
        data = {}
        if "PrintTimeGenius" in self._plugin_manager.plugins:
            data["print_time_genius"] = "available"
        if "SpoolManager" in self._plugin_manager.plugins:
            data["spool_manager"] = "available"
        return data

    def _update_metric(self, key, increment):
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE metrics SET value = value + ? WHERE key = ?", (increment, key))
            conn.commit()
            conn.close()
        except Exception as e:
            self._logger.error(f"Failed to update metric: {e}")

    def _log_telemetry(self, temps, progress):
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            ht = temps.get('tool0', {}).get('actual', 0.0) if temps else 0.0
            bt = temps.get('bed', {}).get('actual', 0.0) if temps else 0.0
            cursor.execute("INSERT INTO telemetry_timeseries (timestamp, hotend_temp, bed_temp, progress) VALUES (?, ?, ?, ?)",
                           (time.time(), ht, bt, progress))
            conn.commit()
            conn.close()
        except Exception:
            pass

    def _check_spool_runout(self, filename):
        try:
            metadata = self._file_manager.get_metadata("local", filename)
            filament_length = metadata.get("analysis", {}).get("filament", {}).get("tool0", {}).get("length", 0)
            
            # Query SpoolManager for selected spool remaining length
            spool_manager = self._plugin_manager.get_plugin("SpoolManager")
            if spool_manager:
                # Retrieve the currently selected spool data
                selected_spool = spool_manager.get_selected_spool()
                if selected_spool and 'remainingLength' in selected_spool:
                    remaining_length = selected_spool['remainingLength']
                    if filament_length > remaining_length:
                        self._logger.warning(f"Not enough filament! Required: {filament_length}, Remaining: {remaining_length}")
                        return True
        except Exception as e:
            self._logger.error(f"Error checking SpoolManager: {e}")
        return False



    def on_event(self, event, payload):
        # Cancel Object Safety Intercept
        if event == "plugin_cancelobject_cancel":
            self._logger.info("CancelObject event detected. Ensuring safety protocols.")
            if payload.get("is_last_object", False):
                self._printer.commands(["M104 S0", "M140 S0", "G28 X Y"])
                
        if event == "PrintStarted":
            self._update_metric("total_prints", 1)
            # Log print job
            try:
                conn = sqlite3.connect(self._db_path)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO print_jobs (filename, start_time, status) VALUES (?, ?, ?)",
                               (payload.get("name"), time.time(), "printing"))
                conn.commit()
                conn.close()
            except Exception:
                pass
            
            if self._check_spool_runout(payload.get("name")):
                self._logger.error("Spool validation failed! Aborting print.")
                if self._printer:
                    self._printer.cancel_print()
                    
        if event == "PrintFailed":
            self._update_metric("failed_prints", 1)
            try:
                conn = sqlite3.connect(self._db_path)
                cursor = conn.cursor()
                cursor.execute("UPDATE print_jobs SET end_time = ?, status = 'failed' WHERE id = (SELECT MAX(id) FROM print_jobs)", (time.time(),))
                conn.commit()
                conn.close()
            except Exception:
                pass
            
        if event == "PrintDone":
            try:
                conn = sqlite3.connect(self._db_path)
                cursor = conn.cursor()
                cursor.execute("UPDATE print_jobs SET end_time = ?, status = 'success' WHERE id = (SELECT MAX(id) FROM print_jobs)", (time.time(),))
                # Add print time to total metric
                cursor.execute("SELECT start_time, end_time FROM print_jobs WHERE id = (SELECT MAX(id) FROM print_jobs)")
                row = cursor.fetchone()
                if row and row[0] and row[1]:
                    duration = row[1] - row[0]
                    cursor.execute("UPDATE metrics SET value = value + ? WHERE key = 'total_print_time_seconds'", (int(duration),))
                conn.commit()
                conn.close()
            except Exception:
                pass

        # Hook into internal event bus for core state
        target_events = ["PrintStarted", "PrintProgress", "PrintDone", "PrintFailed", "PrintPaused", "PrintResumed", "ZChange"]
        if event in target_events:
            if event == "PrintProgress":
                cdata = self._printer.get_current_data() if self._printer else {}
                temps = self._printer.get_current_temperatures() if self._printer else {}
                self._log_telemetry(temps, cdata.get('progress', {}).get('completion', 0.0))
                
            self._logger.info(f"Melt emitting telemetry for event: {event}")
            
            # Maintenance check
            maintenance_warning = False
            try:
                conn = sqlite3.connect(self._db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM metrics WHERE key = 'total_print_time_seconds'")
                total_time = cursor.fetchone()[0]
                conn.close()
                if total_time > (500 * 3600): # 500 hours
                    maintenance_warning = True
            except Exception:
                pass

            # Broadcast to any connected websocket clients using msgpack
            payload_dict = {
                "type": "telemetry_update",
                "event": event,
                "payload": payload,
                "current_data": self._printer.get_current_data() if self._printer else {},
                "plugin_data": self._gather_plugin_telemetry(),
                "maintenance_required": maintenance_warning
            }
            # MessagePack serialization
            try:
                packed = msgpack.packb(payload_dict, use_bin_type=True)
                encoded = base64.b64encode(packed).decode('ascii')
                self._plugin_manager.send_plugin_message(self._identifier, {"msgpack_payload": encoded})
            except Exception as e:
                self._logger.error(f"MsgPack serialization failed: {e}")

    # BlueprintPlugin mixin - Single GET request for all state data <50ms
    @octoprint.plugin.BlueprintPlugin.route("/telemetry", methods=["GET"])
    def get_telemetry(self):
        if not self._printer:
            return jsonify({"status": "error", "message": "Printer not initialized"}), 503
            
        data = {
            "status": "ok",
            "state": self._printer.get_state_id(),
            "temperatures": self._printer.get_current_temperatures(),
            "current_data": self._printer.get_current_data(),
            "plugin_data": self._gather_plugin_telemetry()
        }
        return jsonify(data)
        
    def get_bed_mesh_data(self):
        import requests
        # Primary: API Query
        try:
            response = requests.get("http://localhost:5000/api/plugin/bedlevelvisualizer", 
                                    headers={"X-Api-Key": self._settings.global_get(["api", "key"])},
                                    timeout=2.0)
            if response.status_code == 200:
                return response.json().get("mesh", [])
        except Exception as e:
            self._logger.warning(f"BedLevelVisualizer API failed: {e}. Attempting fallback.")

        # Fallback: Direct File Read
        try:
            data_path = os.path.expanduser("~/.octoprint/data/bedlevelvisualizer/data.json")
            if os.path.exists(data_path):
                with open(data_path, "r") as f:
                    data = json.load(f)
                    return data.get("mesh", [])
        except Exception as e:
            self._logger.error(f"Fallback mesh read failed: {e}")
        
        return []

    def get_cancel_objects(self):
        import requests
        try:
            response = requests.get("http://localhost:5000/api/plugin/cancelobject", 
                                    headers={"X-Api-Key": self._settings.global_get(["api", "key"])},
                                    timeout=2.0)
            if response.status_code == 200:
                return response.json().get("objects", [])
        except Exception as e:
            self._logger.error(f"Failed to fetch CancelObject data: {e}")
        return []

    @octoprint.plugin.BlueprintPlugin.route("/ping", methods=["GET"])
    def ping(self):
        return jsonify({"status": "ok", "plugin": "melt"})

    @octoprint.plugin.BlueprintPlugin.route("/mesh", methods=["GET"])
    def get_bed_mesh(self):
        mesh_data = self.get_bed_mesh_data()
        if mesh_data:
            return jsonify({"status": "ok", "mesh": mesh_data})
        return jsonify({"status": "error", "message": "BedLevelVisualizer data unavailable"}), 404

    @octoprint.plugin.BlueprintPlugin.route("/obico/alert", methods=["POST"])
    def obico_alert(self):
        import flask
        data = flask.request.json or {}
        self._logger.warning(f"Obico AI Alert received: {data}")
        self._plugin_manager.send_plugin_message(self._identifier, {
            "type": "obico_alert",
            "payload": data
        })
        return jsonify({"status": "ok"})

    def _generate_svg_thumbnail(self, file_path):
        # Lightweight fallback: Generate an SVG of the first layer
        lines = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for _ in range(25000): # Only read first 25k lines to save CPU
                    line = f.readline()
                    if not line:
                        break
                    lines.append(line)
        except Exception:
            return None

        current_x = 0.0
        current_y = 0.0
        min_x, max_x = 1000.0, -1000.0
        min_y, max_y = 1000.0, -1000.0
        
        path_str = ""
        is_extruding = False
        
        for line in lines:
            if line.startswith("G1 ") or line.startswith("G0 "):
                parts = line.split()
                x, y, e = None, None, None
                for p in parts:
                    if p.startswith('X'):
                        x = float(p[1:])
                    elif p.startswith('Y'):
                        y = float(p[1:])
                    elif p.startswith('E'):
                        e = float(p[1:])
                
                if x is not None:
                    current_x = x
                if y is not None:
                    current_y = y
                
                # Only draw if we are actually moving on XY
                if x is not None or y is not None:
                    min_x = min(min_x, current_x)
                    max_x = max(max_x, current_x)
                    min_y = min(min_y, current_y)
                    max_y = max(max_y, current_y)
                    
                    if e is not None and e > 0:
                        if not is_extruding:
                            path_str += f"M {current_x} {current_y} "
                            is_extruding = True
                        path_str += f"L {current_x} {current_y} "
                    else:
                        is_extruding = False
            
            # Stop if we reach a substantial Z height (layer 2+) to keep it 2D
            if line.startswith("G1 Z") or line.startswith("G0 Z"):
                parts = line.split()
                for p in parts:
                    if p.startswith('Z'):
                        z = float(p[1:])
                        if z > 1.0: # Stop parsing after 1mm height
                            break

        if min_x > max_x:
            return None # No valid moves found
        
        width = max_x - min_x + 10
        height = max_y - min_y + 10
        
        svg = f'''<svg viewBox="{min_x - 5} {min_y - 5} {width} {height}" xmlns="http://www.w3.org/2000/svg">
            <rect x="{min_x - 5}" y="{min_y - 5}" width="{width}" height="{height}" fill="#1a1a1a" />
            <path d="{path_str}" fill="none" stroke="#00FFCC" stroke-width="0.8" stroke-linejoin="round" />
        </svg>'''
        return svg

    @octoprint.plugin.BlueprintPlugin.route("/thumbnail/<path:filename>", methods=["GET"])
    def get_thumbnail(self, filename):
        import re
        from flask import make_response
        file_path = self._file_manager.path_on_disk("local", filename)
        if not os.path.exists(file_path):
            return jsonify({"status": "error", "message": "File not found"}), 404
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = []
                for _ in range(1000): # Check first 1000 lines
                    line = f.readline()
                    if not line:
                        break
                    content.append(line)
            
            gcode_str = "".join(content)
            # PrusaSlicer/Cura thumbnail extraction regex
            match = re.search(r'; thumbnail begin [0-9x]+ [0-9]+\n((?:; .+\n)+); thumbnail end', gcode_str)
            if match:
                b64_str = "".join([line_str.replace("; ", "").strip() for line_str in match.group(1).split("\n")])
                img_data = base64.b64decode(b64_str)
                response = make_response(img_data)
                response.headers.set('Content-Type', 'image/png')
                return response
                
            # Fallback: Generate SVG from G-Code movements
            svg_data = self._generate_svg_thumbnail(file_path)
            if svg_data:
                response = make_response(svg_data)
                response.headers.set('Content-Type', 'image/svg+xml')
                return response
                
            return jsonify({"status": "error", "message": "No thumbnail found and SVG generation failed"}), 404
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    @octoprint.plugin.BlueprintPlugin.route("/exclude", methods=["POST"])
    def exclude_region(self):
        import flask
        data = flask.request.json or {}
        self._logger.info(f"Excluding region: {data}")
        
        # Route the exclusion coordinates to the ExcludeRegion plugin natively
        exclude_plugin = self._plugin_manager.get_plugin("excluderegion")
        if exclude_plugin:
            try:
                # Add the region directly to ExcludeRegion's active exclusion list
                exclude_plugin.add_region([
                    [data.get("min_x", 0), data.get("min_y", 0)],
                    [data.get("max_x", 0), data.get("max_y", 0)]
                ])
                return jsonify({"status": "ok", "message": "Region excluded"})
            except Exception as e:
                self._logger.error(f"Failed to pass region to ExcludeRegion plugin: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        else:
            return jsonify({"status": "error", "message": "ExcludeRegion plugin not installed"}), 404

    @octoprint.plugin.BlueprintPlugin.route("/toggle/<plugin_name>", methods=["POST"])
    def toggle_plugin(self, plugin_name):
        if plugin_name not in ["arc_welder", "port_retry"]:
            return jsonify({"status": "error", "message": "Unsupported plugin toggle"}), 400
        import flask
        data = flask.request.json or {}
        enabled = data.get("enabled", True)
        self._logger.info(f"Toggling {plugin_name} to {enabled}")
        if enabled:
            self._plugin_manager.enable_plugin(plugin_name)
        else:
            self._plugin_manager.disable_plugin(plugin_name)
        return jsonify({"status": "ok", "enabled": enabled})

    def is_blueprint_protected(self):
        return True

    def is_api_protected(self):
        return True

    def get_settings_defaults(self):
        return dict(
            enable_telemetry=True,
            max_db_size_mb=50
        )

    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False)
        ]

    def get_assets(self):
        return dict(
            js=["js/melt.js"],
            css=["css/melt.css"]
        )



__plugin_name__ = "Melt Companion Plugin"
__plugin_pythoncompat__ = ">=3.7,<4"
__plugin_author__ = "Pratyaksh Kwatra"
__plugin_url__ = "https://www.github.com/pratyakshkwatra"
def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = MeltPlugin()
