import os

from maya import cmds
import maya.api.OpenMaya as om2

from zoo.libs.maya.cmds.workspace import mayaworkspace


def fileModified():
    """Checks if the current scene has been modified, returns True if it needs saving.

    :return fileModified: True is there have been modifications to the current scene
    :rtype fileModified: bool
    """
    return cmds.file(query=True, modified=True)


def currentSceneFilePath():
    """Returns the current full file path name of the scene, will be "" if not saved

    :return currentSceneFilePath: The full file path of the current scene
    :rtype currentSceneFilePath: str
    """
    return cmds.file(query=True, sceneName=True, shortName=False)  # The current filename of the scene


def saveAsDialogMaMb(windowCaption="Save File", directory="", okCaption="OK"):
    """Pops up a save file dialog but does not save the file, returns the name of the file to save.

    :return filePath: The path of the file saved, if cancelled will be ""
    :rtype filePath: str
    """
    if not directory:
        # get the current file location
        currentFilePath = cmds.file(query=True, sceneName=True, shortName=False)  # the current filename
        if not currentFilePath:  # is an unsaved file
            directory = mayaworkspace.getProjSubDirectory(sudDirectory="scenes")
        else:
            directory = os.path.split(currentFilePath)[0]  # the directory path
    multipleFilters = "Maya Files (*.ma *.mb);;Maya ASCII (*.ma);;Maya Binary (*.mb)"
    filePath = cmds.fileDialog2(fileFilter=multipleFilters,
                                dialogStyle=2,
                                caption=windowCaption,
                                startingDirectory=directory,
                                okCaption=okCaption)
    if not filePath:
        return filePath
    if filePath:  # Is a list so make a string path
        filePath = filePath[0]
    # Save file
    if filePath.split(".")[-1] == "ma":  # Need to force lower
        cmds.file(rename=filePath)
        cmds.file(force=True, type='mayaAscii', save=True)
    if filePath.split(".")[-1] == "mb":  # Need to force lower
        cmds.file(rename=filePath)
        cmds.file(force=True, type='mayaBinary', save=True)
    om2.MGlobal.displayInfo("Success: File saved `{}`".format(filePath))
    return filePath


def createNewScene(force=True):
    """Creates a new maya scene

    :param force: Will force a new scene even if the current scene has not been saved, False will error if not saved
    :type force: bool
    """
    cmds.file(newFile=True, force=force)

