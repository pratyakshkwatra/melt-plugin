$(function() {
    function MeltViewModel(parameters) {
        var self = this;
        // Logic for Melt Dashboard
    }
    
    OCTOPRINT_VIEWMODELS.push({
        construct: MeltViewModel,
        dependencies: ["loginStateViewModel", "settingsViewModel"],
        elements: ["#tab_plugin_melt"]
    });
});
