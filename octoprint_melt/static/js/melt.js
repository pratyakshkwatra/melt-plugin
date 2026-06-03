$(function() {
    function MeltViewModel(parameters) {
        var self = this;
        self.settings = parameters[0];
        
        // Observables for the Dashboard Tab
        self.statusText = ko.observable("Waiting for telemetry...");
        self.totalPrints = ko.observable(0);
        self.failedPrints = ko.observable(0);
        
        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin !== "melt") {
                return;
            }
            if (data.msgpack_payload) {
                self.statusText("Receiving high-throughput telemetry...");
            }
        };
    }
    
    OCTOPRINT_VIEWMODELS.push({
        construct: MeltViewModel,
        dependencies: ["settingsViewModel"],
        elements: ["#tab_plugin_melt", "#settings_plugin_melt"]
    });
});
