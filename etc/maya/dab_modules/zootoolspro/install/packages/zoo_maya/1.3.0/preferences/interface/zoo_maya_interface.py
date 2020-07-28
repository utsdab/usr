from zoo.preferences.core import prefinterface


class ToolsetPreference(prefinterface.PreferenceInterface):
    id = "zoo.maya.interface"
    _relativePath = "prefs/maya/zoo_maya.pref"

    def settings(self):
        """Returns the data of the user preferences JSON for the zoo_light_suite"""
        data = self.preference.findSetting(self._relativePath, root=None)
        if not data:
            data = self.preference.defaultPreferenceSettings(self._packageName, self._relativePath)
        return dict()  # TODO return an empty dict until being used
