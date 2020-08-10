"""
Startup function
    copies the default preferences from each package to the user_preferences
Shutdown function
    bakes currently installed preference roots to main zootools config path.
"""
import logging

from zoo.libs.utils.general import compareDictionaries

from zoo.preferences.core import preference
logger = logging.getLogger("Stylesheets")


def startup(package):
    """ Run commands on zoo_preferences start up

    :param package:
    :type package:
    :return:
    :rtype:
    """
    # ok now copy across the missing default preferences over to the user directory
    preference.copyOriginalToRoot("user_preferences", force=False)

    # Copy over any stylesheet prefs keys by comparing JSON dictionaries
    interface = preference.interface("core_interface")
    userPreferences = interface.settings()
    userStyles = userPreferences["settings"]
    # Maybe should be for all prefs not just stylesheet
    default = preference.defaultPreferenceSettings("zoo_preferences", "global/stylesheet")
    defaultStyles = default["settings"]

    target, messageLog = compareDictionaries(defaultStyles, userStyles)  # do the compare
    if messageLog:  # if keys have been updated
        userPreferences.save(indent=True, sort=True)
        logger.info(messageLog)


def shutdown(package):
    prefInterface = preference.interface("core_interface")
    prefInterface.bakePreferenceRoots()
