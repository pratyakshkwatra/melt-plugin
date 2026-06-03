$(function () {
  function MeltViewModel(parameters) {
    var self = this;
    self.settings = parameters[0];

    self.statusText = ko.observable("Waiting for telemetry...");
    self.totalPrints = ko.observable(0);
    self.failedPrints = ko.observable(0);

    self.onDataUpdaterPluginMessage = function (plugin, data) {
      if (plugin !== "melt") {
        return;
      }
      if (data.msgpack_payload) {
        self.statusText("Receiving high-throughput telemetry...");
      }
    };

    // Fetch initial state so it doesn't stay stuck when printer is idle
    self.onStartupComplete = function () {
      OctoPrint.get(OctoPrint.getBlueprintUrl("melt") + "telemetry")
        .done(function (response) {
          if (response.status === "ok") {
            self.statusText(
              "Connected & Idle. Ready for high-throughput telemetry.",
            );
          }
        })
        .fail(function () {
          self.statusText("Error: Cannot reach Melt backend API.");
        });
    };
  }

  OCTOPRINT_VIEWMODELS.push({
    construct: MeltViewModel,
    dependencies: ["settingsViewModel"],
    elements: ["#tab_plugin_melt", "#settings_plugin_melt"],
  });
});
