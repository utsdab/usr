import contextlib

from maya import cmds
from maya.api import OpenMaya as om2
from maya.api import OpenMayaUI as om2ui
from zoo.libs.maya.api import nodes


@contextlib.contextmanager
def maintainCamera(panel, camera):
    """Context Manager to allow the client to set the current modelpanel to a 
    different camera temporary before setting back to the original camera.

    :param panel: the maya model panel
    :type panel: str
    :param camera: the fullpathName of the camera.
    :type camera: str
    """
    view = om2ui.M3dView()
    currentCamera = view.getM3dViewFromModelPanel(panel)
    cmds.lookThru(panel, camera)
    yield
    cmds.lookThru(panel, currentCamera.fullPathName())
