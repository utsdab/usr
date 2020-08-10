import inspect
import os

from zoo.libs.pyqt import stylesheet, utils
from zoo.libs.utils import colour, zlogging, filesystem
from zoo.preferences import prefinterface
from zoo.core import api
from zoovendor.six import string_types

logger = zlogging.getLogger(__name__)


class ZooToolsPreference(prefinterface.PreferenceInterface):
    """Main interface for zoo preferences. This class shouldn't be 
    instanced directly but through the PreferenceManager instance.

    """
    # the unique identifier on which to be referred to in the registry
    id = "core_interface"
    # internal use only,  relative path from the root directories
    # for the stylesheet.pref file
    _relativePath = "prefs/global/stylesheet.pref"
    _preference_roots_path = "env/preference_roots.config"
    # internal use only, zoo preference package name
    _packageName = "zoo_preferences"
    _settings = None

    def currentTheme(self):
        """Returns the current theme name for zootools.

        :return: The style sheet theme name
        :rtype: str
        """
        return self.preference.findSetting(self._relativePath, root=None, name="current_theme")

    def defaultPreferencesPath(self):
        return "~/zoo_preferences"

    def themes(self):
        """Returns the themes as a list

        :return: The style sheet theme name
        :rtype: str
        """
        return self.preference.findSetting(self._relativePath, root=None, name="themes").keys()

    def settings(self):
        """Returns the :class:`SettingsObject` instance corresponding to the relativepath
        
        :return: The .pref file loaded into a SettingsObject, use Object.save() to save any changes.
        :rtype: :class:`zoo.libs.tooldata.tooldata.SettingsObject`
        """
        if self._settings is None:
            self._settings = self.preference.findSetting(self._relativePath, root=None)
        return self._settings

    def forceRefresh(self):
        """ Force a refresh

        :return:
        :rtype:
        """
        self._settings = None
        self.settings()

    def stylesheet(self, theme=None):
        """Loads and returns the stylesheet string

        :param theme: Themes name
        :type theme: basestring
        :return: The final composed stylesheet
        :rtype: :class:`zoo.libs.pyqt.styleSheet.StyleSheet`
        """
        if theme is None:
            theme = self.currentTheme()
        return self.stylesheetForTheme(theme)

    def stylesheetSetting(self, key, theme=None):
        """ Get one specific setting from a theme in the stylesheet.

        :param key: A key from the theme eg "$BTN_BACKGROUND_COLOR"
        :param theme: Leave none to use default
        :return: The key value
        """
        try:
            settings = self.settings()['settings']
            theme = theme or settings['current_theme']
            ret = settings['themes'][theme].get(key)
        except KeyError:
            logger.error("Incorrectly format stylesheet: {}".format(self._relativePath))
            raise

        if ret is None:
            self.preference.defaultPreferenceSettings(self._packageName, self._relativePath)

        return ret

    def stylesheetSettingColour(self, key, theme=None):
        """ Return colour setting from current theme

        :param key:
        :param theme:
        :return: Tu(r,g,b)
        :rtype: tuple(float,float,float)
        """
        return colour.hexToRGB(self.stylesheetSetting(key, theme))

    def revertThemeToDefault(self, theme=None, save=True):
        """ Reverts current theme to default

        :return:
        :rtype:
        """
        default = self.preference.defaultPreferenceSettings("zoo_preferences", "global/stylesheet")
        defaultTheme = default["settings"]["themes"][self.currentTheme()]
        userTheme = self.settings()["settings"]["themes"][self.currentTheme()]
        userTheme.update(defaultTheme)
        if save:
            self.settings().save(indent=True, sort=True)

    def __getattr__(self, item):
        """ Retrieve the current theme's key value

        :param item:
        :return:
        """

        setting = self.stylesheetSetting("$" + item)

        if setting is None:
            return super(ZooToolsPreference, self).__getattribute__(item)
        # Return the int value by itself
        elif isinstance(setting, int):
            return setting
        # May cause problems if stylesheet.pref has strings that arent colours
        elif isinstance(setting, string_types):
            if setting.startswith('^'):  # apply dpiScaling for '^' prefixed strings
                return utils.dpiScale(int(setting[1:]))

            if len(setting) in (3, 6, 8):  # Hex number
                return colour.hexToRGBA(setting)

        return super(ZooToolsPreference, self).__getattribute__(item)

    def stylesheetForTheme(self, theme):
        """ Return stylesheet from theme

        :param theme: theme eg "dark" or "maya-toolkit"
        :return:
        """

        stylePrefs = self.preference.findSetting(self._relativePath, root=None)
        if not stylePrefs:
            stylePrefs = self.preference.defaultPreferenceSettings(self._packageName, self._relativePath)

        # a sleight of hand to grab the stylesheet.qss file by grabbing the preferences object path
        setts = stylePrefs["settings"]

        # Get current theme if theme is none
        theme = theme or setts["current_theme"]

        themes = setts["themes"]
        data = themes.get(theme)

        if data is None:
            raise ValueError("Current styleSheet theme doesn't exist, Theme:{}".format(theme))

        return self.stylesheetFromData(data)

    def stylesheetFromData(self, data):
        """ Generate stylesheet from data.

        Data is the dict usually from stylesheet.pref under one of the themes
        {
            "$EMBED_WINDOW_BG": "2a2a2a",
            "$EMBED_WINDOW_BORDER_COL": "3c3c3c",
            "$DEBUG_1": "ff0000",
            "$DEBUG_2": "0012ff",
            "$TEAROFF_LINES": "AAAAAA"
        }

        :param data: Data is the dict usually from stylesheet.pref under one of the themes
        :type data: dict
        :return:
        """
        preferenceLocation = inspect.getmodule(self.preference.__class__).__file__
        stylePath = os.path.join(os.path.dirname(preferenceLocation), "zootools_style.qss")
        return stylesheet.StyleSheet.fromPath(stylePath, **data)

    def bakePreferenceRoots(self):
        """Bakes the Preferences root paths and names to zootoolsInstall/config/preferences_root.config

        """
        rootConfig = self.rootConfigPath()
        rootPaths = {rootName: str(rootObject) for rootName, rootObject in self.preference.roots.items()}
        filesystem.saveJson(rootPaths, rootConfig)

    def rootConfigPath(self):
        currentZoo = api.currentConfig()
        return os.path.abspath(os.path.join(currentZoo.configPath, self._preference_roots_path))


