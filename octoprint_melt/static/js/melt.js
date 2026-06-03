$(function () {
  function MeltViewModel(parameters) {
    var self = this;
    self.settings = parameters[0];

    self.statusText = ko.observable("Waiting for telemetry...");
    self.totalPrints = ko.observable(0);
    self.failedPrints = ko.observable(0);
    self.printHours = ko.observable(0);
    self.activeClients = ko.observable(0);
    self.bytesSent = ko.observable(0);
    self.recentJobs = ko.observableArray([]);
    self.telemetryChart = null;

    self.onDataUpdaterPluginMessage = function (plugin, data) {
      if (plugin !== "octoprint_melt") {
        return;
      }
      if (data.msgpack_payload) {
        self.statusText("Receiving high-throughput telemetry...");
        // Re-fetch analytics to update graph when print is active
        self.fetchAnalytics();
      }
    };

    self.fetchAnalytics = function() {
        OctoPrint.get(OctoPrint.getBlueprintUrl("octoprint_melt") + "analytics/metrics").done(function (r) {
            self.totalPrints(r.total_prints || 0);
            self.failedPrints(r.failed_prints || 0);
            self.printHours(((r.total_print_time_seconds || 0) / 3600).toFixed(1));
            self.activeClients(r.active_clients || 0);
            self.bytesSent(((r.bytes_sent || 0) / 1048576).toFixed(2));
        });

        OctoPrint.get(OctoPrint.getBlueprintUrl("octoprint_melt") + "analytics/jobs").done(function (r) {
            self.recentJobs(r.jobs || []);
        });

        OctoPrint.get(OctoPrint.getBlueprintUrl("octoprint_melt") + "analytics/timeseries").done(function (r) {
            if (self.telemetryChart && r.timeseries) {
                var labels = [];
                var hotend = [];
                var bed = [];
                r.timeseries.forEach(function(pt) {
                    var d = new Date(pt.timestamp * 1000);
                    labels.push(d.getHours() + ":" + (d.getMinutes()<10?'0':'') + d.getMinutes());
                    hotend.push(pt.hotend_temp);
                    bed.push(pt.bed_temp);
                });
                self.telemetryChart.data.labels = labels;
                self.telemetryChart.data.datasets[0].data = hotend;
                self.telemetryChart.data.datasets[1].data = bed;
                self.telemetryChart.update();
            }
        });
    };

    self.onStartupComplete = function () {
      OctoPrint.get(OctoPrint.getBlueprintUrl("octoprint_melt") + "telemetry")
        .done(function (response) {
          if (response.status === "ok") {
            self.statusText("Connected & Idle. Ready for high-throughput telemetry.");
          }
        })
        .fail(function () {
          self.statusText("Error: Cannot reach Melt backend API.");
        });

      // Initialize Chart.js
      var ctx = document.getElementById('meltTelemetryChart');
      if (ctx) {
          self.telemetryChart = new Chart(ctx, {
              type: 'line',
              data: {
                  labels: [],
                  datasets: [{
                      label: 'Hotend Temp (°C)',
                      borderColor: '#06B6D4',
                      data: [],
                      fill: false,
                      tension: 0.1
                  }, {
                      label: 'Bed Temp (°C)',
                      borderColor: '#F97316',
                      data: [],
                      fill: false,
                      tension: 0.1
                  }]
              },
              options: {
                  responsive: true,
                  maintainAspectRatio: false
              }
          });
      }
      
      self.fetchAnalytics();
      // Poll every 30 seconds
      setInterval(self.fetchAnalytics, 30000);
    };
  }

  OCTOPRINT_VIEWMODELS.push({
    construct: MeltViewModel,
    dependencies: ["settingsViewModel"],
    elements: ["#tab_plugin_melt", "#settings_plugin_melt"],
  });
});
