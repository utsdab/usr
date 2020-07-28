import os

import maya.cmds as cmds
import maya.api.OpenMaya as om2


def getCurrentMayaWorkspace():
    """Returns the current project directory

    :return projectDirectoryPath: the path of the current Maya project directory
    :rtype projectDirectoryPath: str
    """
    return cmds.workspace(q=True, rootDirectory=True)


def getProjSubDirectory(sudDirectory="scenes", message=True):
    """Returns the path of the current Maya project sub directory Eg:

        /scenes/
        or
        /sourceImages/
        etc

    Note: If not found will default to the home directory of your OS.

    :param sudDirectory: The subDirectory of the project directory, can be multiple directories deep
    :type sudDirectory: str
    :param message: Warn the user if the path wasn't found?
    :type message: bool
    :return directoryPath: The path of the directory
    :rtype directoryPath: str
    """
    projectDir = getCurrentMayaWorkspace()
    directory = os.path.join(projectDir, sudDirectory)
    if not os.path.isdir(directory):  # Doesn't exist so set to Home directory
        homeDirectory = os.path.expanduser("~")  # home directory
        om2.MGlobal.displayWarning("Directory `{}` doesn't exist, setting to `{}`".format(directory, homeDirectory))
        directory = homeDirectory
    return directory

