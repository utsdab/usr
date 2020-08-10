from zoo.preferences import prefinterface
from zoo.libs.tooldata import tooldata


class ArtistPaletteInterface(prefinterface.PreferenceInterface):
    """Class that loads the Zoo Tools menu and main ZooToolsPro shelf at startup
    """

    id = "artistPalette"

    def menuName(self):
        data = self.preference.findSetting("prefs/maya/artistpalette.pref", root=None)
        return data["settings"]

    def loadShelfAtStartup(self):
        return self.preference.findSetting("prefs/maya/artistpalette.pref",
                                           root=None,
                                           name="load_shelf_at_startup")

    def defaultShelf(self):
        try:
            return self.preference.findSetting("prefs/maya/artistpalette.pref",
                                               root=None,
                                               name="default")
        except tooldata.InvalidSettingsPath:
            settings = self.preference.defaultPreferenceSettings("zoo_artist_palette", "prefs/maya/artistPalette")
            return settings.settings["default"]

    def isActiveAtStartup(self):
        try:
            return self.preference.findSetting("prefs/maya/artistpalette.pref",
                                               root=None,
                                               name="isActiveAtStartup")
        except tooldata.InvalidSettingsPath:
            settings = self.preference.defaultPreferenceSettings("zoo_artist_palette", "prefs/maya/artistPalette")
            return settings.settings.get("isActiveAtStartup", False)
