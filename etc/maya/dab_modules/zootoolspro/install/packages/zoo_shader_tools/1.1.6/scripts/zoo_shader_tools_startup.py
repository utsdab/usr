"""
Startup function:

    builds the default asset directories if they don't exist

"""
import logging

from zoo.apps.shader_tools import shaderdirectories

logger = logging.getLogger("Zoo Shader Tools Startup")


def startup(package):
    """Creates the assets folders if they don't exist
    1. Creates folder if it doesn't exist:
        userPath/zoo_preferences/assets/shaders

    2. Upgrades .pref to "settings" if upgrading from 2.2.3 or lower

    3. Updates .pref dictionary keys if any are missing
    """
    shaderdirectories.buildShaderAssetDirectories()

