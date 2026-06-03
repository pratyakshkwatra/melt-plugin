import sys
from unittest.mock import MagicMock

# Create a full mock of the octoprint package
mock_octo = MagicMock()
mock_octo.plugin.BlueprintPlugin = type('BlueprintPlugin', (object,), {'route': lambda *a, **k: lambda f: f})
mock_octo.plugin.StartupPlugin = type('StartupPlugin', (object,), {})
mock_octo.plugin.EventHandlerPlugin = type('EventHandlerPlugin', (object,), {})
mock_octo.plugin.TemplatePlugin = type('TemplatePlugin', (object,), {})
mock_octo.plugin.SettingsPlugin = type('SettingsPlugin', (object,), {})
mock_octo.plugin.AssetPlugin = type('AssetPlugin', (object,), {})

sys.modules['octoprint'] = mock_octo
sys.modules['octoprint.plugin'] = mock_octo.plugin
