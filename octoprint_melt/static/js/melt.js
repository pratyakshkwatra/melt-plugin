$(function() {
    function MeltViewModel(parameters) {
        var self = this;
        self.settings = parameters[1];
        
        // Settings are automatically loaded and saved by OctoPrint's SettingsViewModel
    }
    
    OCTOPRINT_VIEWMODELS.push({
        construct: MeltViewModel,
        dependencies: ["loginStateViewModel", "settingsViewModel"],
        elements: ["#settings_plugin_melt"]
    });
});
