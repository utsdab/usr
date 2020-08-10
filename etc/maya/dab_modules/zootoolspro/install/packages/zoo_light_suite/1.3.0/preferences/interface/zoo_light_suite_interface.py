from zoo.preferences.core import prefinterface


class ToolsetPreference(prefinterface.PreferenceInterface):
    id = "zoo.light.suite.interface"
    _relativePath = "prefs/maya/zoo_light_suite.pref"

    def settings(self):
        """Returns the data of the user preferences JSON for the zoo_light_suite"""
        data = self.preference.findSetting(self._relativePath, root=None)
        if not data:
            data = self.preference.defaultPreferenceSettings(self._packageName, self._relativePath)
        return data["settings"]
